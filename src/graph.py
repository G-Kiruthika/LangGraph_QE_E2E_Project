from src.nodes.scenario_node import generate_test_scenarios
from src.nodes.jira_node import fetch_jira_story, create_subtask
from src.nodes.testcases_node import generate_test_cases
from src.nodes.testScriptGen_node import generate_and_heal_test_scripts
from langgraph.graph import StateGraph, START, END
from src.core.state import GraphState

workflow = StateGraph(GraphState)
    
# Add nodes
workflow.add_node("fetch_jira_story", fetch_jira_story)
workflow.add_node("generate_test_scenarios", generate_test_scenarios)
workflow.add_node("create_subtask", create_subtask)
workflow.add_node("generate_test_cases", generate_test_cases)
workflow.add_node("generate_and_heal_test_scripts", generate_and_heal_test_scripts)

# Add edges
workflow.add_edge(START, "fetch_jira_story")
workflow.add_edge("fetch_jira_story", "generate_test_scenarios")
workflow.add_edge("generate_test_scenarios", "create_subtask")
workflow.add_edge("create_subtask", "generate_test_cases")
workflow.add_edge("generate_test_cases", "generate_and_heal_test_scripts")
workflow.add_edge("generate_and_heal_test_scripts", END)
    
result = workflow.compile()
