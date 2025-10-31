import os
import sys
import json
from groq import Groq
from prompts import system_prompt, OUTPUT_SCHEMA
import argparse
import logging
from typing import List, Dict, Any
from pydantic import BaseModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.FileHandler("agent.log")],
)

# Suppress verbose HTTP logs
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class AIAgent:

    MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.messages: List[Dict[str, Any]] = []
        self.tools: List[Tool] = []
        self._setup_tools()

    def _setup_tools(self):
        self.tools = [
            Tool(
                name="read_file",
                description="Read the contents of a file at the specified path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="list_files",
                description="List all files and directories in the specified path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to list (defaults to current directory)",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name="edit_file",
                description="Edits a file by replacing old_text with new_text. Creates the file if it doesn't exist.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to search for and replace (leave empty to create new file)",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The text to replace old_text with",
                        },
                    },
                    "required": ["path", "new_text"],
                },
            ),
        ]
    def _execute_tools(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input.get("old_text", ""),
                    tool_input["new_text"],
                )
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _read_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                return f"File contents of {path}:\n{content}"
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _list_files(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Path not found: {path}"
            
            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}/")
                else:
                    items.append(f"[FILE] {item}")
            if not items:
                return f"Empty directory: {path}"

            return f"Contents of {path}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing files: {str(e)}"
 
    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        try:
            if os.path.exists(path) and old_text:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                if old_text not in content:
                    return f"Text not found in file: {old_text}"

                content = content.replace(old_text, new_text)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                return f"Successfully edited {path}"
            else:
                # Only create directory if path contains subdirectories
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

                return f"Successfully created {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def chat(self, user_query: str) -> str:
        self.messages.append({"role": "user", "content": user_query})

        tool_schemas_description = "\n".join(
                            [f"- {tool.name}: {tool.description}\n  Input Schema: {tool.input_schema}" for tool in self.tools]
                        )
        
        try:
            while True:
                response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct", 
                messages=[
                    {"role": "system", "content": f"{system_prompt.format(tool_schemas=tool_schemas_description)}"},
                    {"role": "user", "content": f"{self.messages}"}
                         ],
                    response_format={"type": "json_schema", 
                                "json_schema": {
                                                "name": "orchestrator_schema",
                                                "schema": OUTPUT_SCHEMA
                                                }
                                }
                )

                response = json.loads(response.choices[0].message.content)

                assistant_message = {"role": "assistant", "content": []}
                
                for content in response["content"]:
                    if content["action_type"] == "text":
                        assistant_message["content"].append({
                        "type": "text",
                        "text": content["response_text"]
                        })
                    elif content["action_type"] == "tool_use":             
                        assistant_message["content"].append({
                            "type": "tool_use",
                            "tool_name": content["tool_name"],
                            "tool_input": content["tool_input"]
                        })
                    
                self.messages.append(assistant_message)
                
                tool_results = []
                for content in response["content"]:
                    if content["action_type"] == "tool_use":
                        result = self._execute_tools(content["tool_name"], content["tool_input"])
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "content": result,
                            }
                        )

                if tool_results:
                    self.messages.append({"role": "user", "content": tool_results})
                else:
                    return response["content"][0]["response_text"]
        except Exception as e:
            return e

def main():
    parser = argparse.ArgumentParser(
        description="AI Code Assistant - A conversational AI agent with file editing capabilities"
    )
    parser.add_argument(
        "--api-key", help="Groq API key (or set GROQ_API_KEY env var)"
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(
            "Error: Please provide an API key via --api-key or GROQ_API_KEY environment variable"
        )
        sys.exit(1)

    agent = AIAgent(api_key)

    print("AI Code Assistant")
    print("================")
    print("A conversational AI agent that can read, list, and edit files.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("\nAssistant: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print()


if __name__ == "__main__":
    main()  

