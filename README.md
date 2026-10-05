# AI-Powered Quality Engineering (QE) Framework

This project is an advanced, AI-driven Quality Engineering (QE) automation framework built using **LangGraph** and **LangChain**. It reads Jira user stories, queries local knowledge bases (RAG), automatically generates test scenarios, refines them using a self-healing reviewer agent, and automatically posts them back to Jira as a subtask.

## Core Features & Architecture

*   **LangGraph Orchestration**: Uses a `StateGraph` to manage memory (`GraphState`) and move data seamlessly through multiple execution nodes.
*   **Jira API Integration**: Programmatically fetches real-time Jira story details and creates subtasks directly within the Jira workspace without requiring manual data entry.
*   **RAG (Retrieval-Augmented Generation)**: Uses a local **ChromaDB** vector store embedded with `all-MiniLM-L6-v2`. The system searches domain-specific knowledge bases (e.g., OrangeHRM documentation) and injects the context directly into the agent's prompt to ensure highly accurate, domain-aware scenarios.
*   **Self-Healing AI Loop**: Uses a dual-agent ReAct system.
    *   **Generator Agent**: Writes the initial test scenarios based on the Jira story and RAG context.
    *   **Reviewer Agent**: Evaluates the scenarios against Acceptance Criteria. If the confidence score is `< 85%`, it sends feedback back to the Generator to fix its mistakes. The loop runs iteratively until the quality threshold is met.
*   **Structured Output Parsing**: Leverages Pydantic schemas and robust markdown-fence stripping to ensure the LLM strictly outputs parsable JSON arrays.

## Project Structure
- `src/core/`: Contains the foundational LangGraph state definitions, KB ingestion scripts, and LLM configuration (powered by Google Gemini).
- `src/models/`: Contains Pydantic schemas enforcing strict JSON outputs from the LLMs.
- `src/nodes/`: Contains the individual LangGraph nodes (`jira_node.py`, `scenario_node.py`).
- `src/agents/`: Contains the specialized ReAct agents (Fetcher, Orchestrator, Generator, Reviewer).
- `src/tools/`: Contains custom Python tools for Jira REST requests, RAG retrieval (`rag_tools.py`), and the Self-Healing Orchestrator (`scenario_self_healing_tool.py`).
- `src/knowledge_base/`: Stores the raw text files used for RAG embeddings.
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
3. Configure environment variables in `.env` (or copy from `.env.example`):
   ```bash
   # Google Gemini LLM API Key
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.1-flash-lite # or gemini-1.5-flash

   # Jira API Configuration
   JIRA_DOMAIN=https://your-domain.atlassian.net
   JIRA_USERNAME=your_email@example.com
   JIRA_API_KEY=your_jira_api_token_here
   ```
4. **Build the Vector Database**: Before running the graph for the first time, ingest your knowledge base text files into ChromaDB:
   ```bash
   python -m src.core.ingest_kb
   ```

## Execution
To run the graph and automatically generate scenarios for your Jira ticket:
```bash
python main.py
```
The output will be saved locally to `outputs/final_scenarios.json` and a subtask will automatically be created in Jira.
