from src.core.state import GraphState
from src.agents.scenario_orchestrator_agent import scenario_orchestrator_agent
import json

def generate_test_scenarios(state: GraphState):
    print("--- Generating Test Scenarios with Self-Healing ---")
    
    # 1. Extract data from your GraphState
    story_details = state.get("story_details", {})
    summary = story_details.get("summary", "No Summary Provided")
    description = story_details.get("description", "No Description Provided")
    
    # 2. Invoke the fully encapsulated orchestrator agent
    user_message = f"Story Summary: {summary}\nStory Description: {description}\nEpic Context: {state.get('epic_context', '')}\nPreconditions: {state.get('preconditions', '')}"
    
    result = scenario_orchestrator_agent.invoke({
        "messages": [("user", user_message)]
    })
    
    # The result has "messages", we need to extract the final output
    messages = result.get("messages", [])
    output_str = messages[-1].content if messages else ""
    
    # 4. Parse the returned scenarios if possible, otherwise just return the string
    try:
        # Assuming the LLM output the JSON string exactly as returned by the tool
        parsed_scenarios = json.loads(output_str)
    except json.JSONDecodeError:
        parsed_scenarios = {"raw_output": output_str}

    # 5. Return the result back into your GraphState
    return {"test_scenarios": parsed_scenarios}
