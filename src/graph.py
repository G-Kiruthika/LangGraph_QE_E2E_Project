from src.nodes.scenario_node import generate_test_scenarios
from src.nodes.jira_node import fetch_jira_story, create_subtask
from src.nodes.testcases_node import generate_test_cases
from src.nodes.testScriptGen_node import generate_and_heal_test_scripts
from langgraph.graph import StateGraph, START, END
from src.core.state import GraphState


def should_continue_after_jira(state: GraphState) -> str:
    if state.get("error"):
        return END
    return "generate_test_scenarios"


def should_continue_after_scenarios(state: GraphState) -> str:
    if state.get("error"):
        return END
    return "create_subtask"


def should_continue_after_subtask(state: GraphState) -> str:
    if state.get("error"):
        return END
    return "generate_test_cases"


def should_continue_after_testcases(state: GraphState) -> str:
    if state.get("error"):
        return END
    return "generate_and_heal_test_scripts"


workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("fetch_jira_story", fetch_jira_story)
workflow.add_node("generate_test_scenarios", generate_test_scenarios)
workflow.add_node("create_subtask", create_subtask)
workflow.add_node("generate_test_cases", generate_test_cases)
workflow.add_node("generate_and_heal_test_scripts", generate_and_heal_test_scripts)

# Add conditional edges to immediately stop execution on any error
workflow.add_edge(START, "fetch_jira_story")

workflow.add_conditional_edges(
    "fetch_jira_story",
    should_continue_after_jira,
    {
        "generate_test_scenarios": "generate_test_scenarios",
        END: END,
    }
)

workflow.add_conditional_edges(
    "generate_test_scenarios",
    should_continue_after_scenarios,
    {
        "create_subtask": "create_subtask",
        END: END,
    }
)

workflow.add_conditional_edges(
    "create_subtask",
    should_continue_after_subtask,
    {
        "generate_test_cases": "generate_test_cases",
        END: END,
    }
)

workflow.add_conditional_edges(
    "generate_test_cases",
    should_continue_after_testcases,
    {
        "generate_and_heal_test_scripts": "generate_and_heal_test_scripts",
        END: END,
    }
)

workflow.add_edge("generate_and_heal_test_scripts", END)

result = workflow.compile()
