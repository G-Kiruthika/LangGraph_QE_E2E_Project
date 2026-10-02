# My AI Learning Tracker

This document tracks my progress as I build the AI-Powered Testing Pipeline.

## 🟢 Completed Concepts
- **LangChain Basics**: Understanding prompts, LLM invocations, and basic chains.
- **RAG Basics**: Familiarity with Vectors, Vectorstores, Text-Splitters, Embeddings, and LLMs.
- **LangGraph Fundamentals**:
  - `State` (managing shared memory using `TypedDict`).
  - `Nodes` (Python functions representing agents/steps).
  - `Edges` (routing logic connecting the nodes).
  - `StateGraph` compilation and execution (`invoke`).
- **Python Structuring**: Using `TypedDict`, `Dataclass`, and Pydantic `BaseModel`.
- **Project Engineering**: Creating a clean, modular folder structure and setting up a virtual environment using `uv`.

## 🟡 Currently Learning / In Progress
- **Structured LLM Outputs**: Utilizing LangChain's `with_structured_output()` to force LLMs to return perfectly formatted JSON corresponding to Pydantic schemas.
- **Connecting Real LLMs**: Hooking up OpenAI/Gemini to LangGraph nodes instead of using dummy data.

## 🔴 Pending / Future Concepts
- **Human-in-the-Loop (LangGraph)**: Pausing execution for human approval (e.g., approving test scenarios before writing test cases).
- **Orchestrating RAG with LangGraph**: Using nodes to conditionally retrieve and grade documents.
- **Vectorless RAG**: Advanced retrieval without traditional vector databases.
- **Guardrails**: Adding robust safety and formatting checks to LLM outputs.
