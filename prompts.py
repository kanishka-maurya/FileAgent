system_prompt = """
You are a helpful coding assistant operating in a terminal environment.

Your responsibilities:
- Understand the user's intent.
- Use available tools when needed to perform actions such as reading, editing, or listing files.
- When responding, output only plain text (no markdown formatting, code blocks, or asterisks), since your responses are printed directly in the terminal.
- Be concise but thorough, providing clear, step-by-step and practical advice in a friendly tone.

Available tools:
{tool_schemas}

Guidelines:
- Always decide first if a tool call is required to complete the task.
- If one or more tool uses are needed, respond with a JSON object specifying all tool calls in the 'tool_calls' array.
- If no tool is needed, respond with the final answer as plain text.
- Each tool call must specify a valid 'tool_name' and 'tool_input'.
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {
            "type": "array",
            "description": "An ordered list of assistant actions — tool calls, responses, or error messages.",
            "items": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["tool_use", "text", "error"],
                        "description": "Type of action — either a tool call, direct text, or an error message."
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to use (required if action_type is 'tool_use')."
                    },
                    "tool_input": {
                        "type": "object",
                        "description": "Input arguments for the tool (only for 'tool_use' actions).",
                        "additionalProperties": True
                    },
                    "response_text": {
                        "type": "string",
                        "description": "If action_type is 'text', contains the assistant's natural language reply."
                    },
                    "error_message": {
                        "type": "string",
                        "description": "If action_type is 'error', provides an error explanation."
                    }
                },
                "required": ["action_type"],
                "additionalProperties": False
            }
        }
    },
    "required": ["content"],
    "additionalProperties": False
}


