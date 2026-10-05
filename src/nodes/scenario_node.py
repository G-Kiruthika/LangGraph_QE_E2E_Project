from src.core.state import GraphState
from src.agents.scenario_orchestrator_agent import scenario_orchestrator_agent
import json

def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, dict):
                parts.append(json.dumps(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, dict):
        return json.dumps(content)
    return str(content) if content is not None else ""

def generate_test_scenarios(state: GraphState):
    print("--- Generating Test Scenarios with Self-Healing ---")
    
    # 1. Extract data from your GraphState
    story_details = state.get("story_details", {})
    if isinstance(story_details, dict):
        summary = story_details.get("summary", "")
        description = story_details.get("description", "")
    else:
        summary = ""
        description = str(story_details)
        
    jira_story = extract_text(state.get("jira_story", ""))
    if not description and jira_story:
        description = jira_story
    if not summary and jira_story:
        summary = jira_story[:100]
    
    # 2. Invoke the fully encapsulated orchestrator agent
    user_message = f"Story Summary: {summary}\nStory Description: {description}\nEpic Context: {state.get('epic_context', '')}\nPreconditions: {state.get('preconditions', '')}"
    
    result = scenario_orchestrator_agent.invoke({
        "messages": [("user", user_message)]
    })
    
    # The result has "messages", we need to extract the final output
    messages = result.get("messages", [])
    
    # Prioritize getting the raw JSON from the tool message directly to bypass LLM summarization
    tool_messages = [m for m in messages if getattr(m, 'type', '') == 'tool']
    if tool_messages:
        raw_content = tool_messages[-1].content
    else:
        raw_content = messages[-1].content if messages else ""
        
    output_str = extract_text(raw_content)
    
    # 4. Parse the returned scenarios if possible, otherwise just return the string
    try:
        # Check if wrapped in markdown code fences
        clean_str = output_str.strip()
        if "```json" in clean_str:
            clean_str = clean_str.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_str:
            clean_str = clean_str.split("```")[1].split("```")[0].strip()
        parsed_scenarios = json.loads(clean_str)
    except Exception:
        parsed_scenarios = {"raw_output": output_str}

    # 5. Return the result back into your GraphState
    return {"test_scenarios": parsed_scenarios}


