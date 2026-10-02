# System Architecture

This pipeline is built as a **State Graph** using LangGraph.

## State Definition (`src/core/state.py`)
The pipeline memory (`GraphState`) holds the data as it flows through the nodes:
- `jira_story`: The raw user story text.
- `test_scenarios`: A structured Pydantic object (`ScenarioResponse`) representing edge cases and testing paths.
- `testcases`: Structured test cases ready for TestRail.
- `playwright_code`: Executable JavaScript/Playwright automation scripts.

## Graph Workflow (`src/graph.py`)
The orchestrator executes sequentially through the following nodes:

1. **Jira Node** (`fetch_jira_story`): Reads the initial requirements.
2. **Scenario Node** (`generate_test_scenarios`): Uses an LLM with structured output to map out scenarios based on the Jira story.
3. **TestRail Node** (pending): Translates scenarios into structured Test Cases.
4. **Code Gen Node** (pending): Generates the Playwright code using RAG for codebase context.

## Models (`src/models/schemas.py`)
We use Pydantic models (e.g., `Scenario`, `ScenarioResponse`) paired with Langchain's `with_structured_output()` to guarantee the LLM outputs exact JSON formats suitable for API uploads.
