# System Architecture

This Quality Engineering (QE) pipeline is built as a stateful multi-agent system using **LangGraph**.

## State Definition (`src/core/state.py`)
The pipeline memory ([`GraphState`](file:///c:/Users/kiruthika.ganesan/Desktop/vs%20code/llm%20learn/Project-1/src/core/state.py)) holds data as it transitions across nodes:
- `jira_story`: Raw user story text, description, and acceptance criteria.
- `test_scenarios`: Structured Pydantic object (`ScenarioResponse`) representing edge cases, negative tests, and happy paths.
- `testcases`: Granular step-by-step test cases ready for Jira & Xray synchronization.
- `playwright_code`: Raw tool outputs and execution summaries.
- `generated_test_scripts`: List of individual generated test scripts metadata (file path, scenario ID, rounds, status).

## Graph Workflow (`src/graph.py`)
The orchestrator executes sequentially through 5 specialized nodes:

1. **Jira Fetch Node** (`fetch_jira_story`): Programmatically fetches story requirements and acceptance criteria from Jira Cloud REST API.
2. **Scenario Generation Node** (`generate_test_scenarios`): Invokes dual-agent ReAct loop (Generator & Reviewer) with RAG context; self-heals until confidence score reaches ≥ 85%.
3. **Subtask Creation Node** (`create_subtask`): Automatically posts verified scenarios as a child subtask in Jira.
4. **Test Cases & Xray Node** (`generate_test_cases`): Formulates structured manual test steps and bulk-synchronizes them into Atlassian Xray Cloud with traceability links.
5. **Playwright Script Gen & Self-Healing Node** (`generate_and_heal_test_scripts`): Extracts locators, generates modular Pytest scripts in `tests/`, executes them, heals code upon failure, records browser video, and builds an HTML execution report.

## Multi-Agent Hierarchy (`src/agents/`)
- **`fetch_jira_details_agent`**: Interacts with Jira Cloud REST endpoints.
- **`scenario_generator_agent` & `scenario_reviewer_agent`**: Self-healing scenario formulation governed by `scenario_orchestrator_agent`.
- **`testcases_generator_agent` & `testcase_reviewer_agent`**: Detailed test case creation governed by `testcases_orchestrator_agent`.
- **`testscript_generator_agent`**: Dynamic Playwright code synthesis and error-traceback correction.
