# AI-Powered End-to-End Testing Pipeline

This project is an AI-driven automated testing framework built using **LangGraph** and **LangChain**. It reads Jira user stories, automatically generates test scenarios and test cases, and outputs Playwright automation scripts.

## Project Structure
- `src/core/`: Contains the foundational LangGraph state definitions and prompt templates.
- `src/models/`: Contains Pydantic schemas enforcing strict JSON outputs from the LLM.
- `src/nodes/`: Contains the individual LangGraph nodes (the agents doing the work).
- `src/integrations/`: Handles external API connections (Jira, TestRail).
- `src/rag/`: Handles context retrieval for advanced code generation.
- `src/graph.py`: The LangGraph orchestrator linking all nodes together.
- `main.py`: The entry point for executing the graph.

## Setup Instructions
1. Ensure you have Python 3.12+ installed.
2. We recommend using `uv` for fast dependency management.
   ```bash
   uv venv
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

## Execution
To run the graph:
```bash
python main.py
```
