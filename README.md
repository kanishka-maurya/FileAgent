# FileAgent – AI File Interaction Assistant

FileAgent is a lightweight AI-powered command-line assistant that can **read, list, and edit files** on your local system.  
It uses the **Groq API** (Llama 4 model) to interpret natural language commands and intelligently execute file operations.

---

```bash
Open Powershell
```

## Prerequisites


Before running FileAgent, make sure you have:


- **Python ≥ 3.9** installed  
```bash
  python --version
```

- Install uv package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- Clone the repository:
```bash
  git clone https://github.com/kanishka-maurya/FileAgent.git
  cd FileAgent
```

- This will create a virtual environment and install dependencies defined in pyproject.toml:
```bash
  uv sync
```

- Configure you groq_api_key and run the file:
```bash
uv run FileAgent.py --api-key your_groq_api_key
```

- You'll see:
```bash
AI Code Assistant
================
A conversational AI agent that can read, list, and edit files.
Type 'exit' or 'quit' to end the conversation.
```

- What you can do with this Agent:
```bash
1. List Files in a Directory
You: List all files and folders in path_to_your_folder
```
```bash
2. Read a Specific File
You: Summarise the content of your_filepath  
```
```bash
3. Create a New File
You: Create a new file named notes.txt with the text "This is my first AI-created file." in directory path_to_your_directory
```
```bash
4. Edit an Existing File
You: Replace the word "draft" with "final" in your_file_path
```
```bash
5. Chat Without Tool Usage
You: Who is the current Prime Minister of India?
```


