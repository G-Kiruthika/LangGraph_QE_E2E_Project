import json
import os
from dotenv import load_dotenv
from src.core.state import GraphState
from src.agents.testcases_orchestrator_agent import testcases_orchestrator_agent
from src.tools.xray_jira_tool import XrayJiraCompleteTraceabilityTool

load_dotenv()

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

def generate_test_cases(state: GraphState):
    print("--- Generating Test Cases with Self-Healing ---")
    
    # 1. Extract data from GraphState
    story_details = state.get("story_details", {})
    if isinstance(story_details, dict):
        summary = story_details.get("summary", "")
        description = story_details.get("description", "")
        story_key = story_details.get("issue_key", "")
    else:
        summary = ""
        description = str(story_details)
        story_key = ""
        
    jira_story = extract_text(state.get("jira_story", ""))
    if not description and jira_story:
        description = jira_story
    if not summary and jira_story:
        summary = jira_story[:100]
        
    scenarios = state.get("test_scenarios", {})
    scenarios_json = json.dumps(scenarios) if isinstance(scenarios, dict) else str(scenarios)

    # If story_key wasn't parsed properly, attempt to extract it from description
    if not story_key and "**issue_key:**" in description:
        for line in description.splitlines():
            if "**issue_key:**" in line:
                story_key = line.split("**issue_key:**")[1].strip()
                break

    project_key = story_key.split("-")[0] if "-" in story_key else ""
    
    # 2. Invoke Orchestrator
    user_message = (
        f"Summary: {summary}\n"
        f"Description: {description}\n"
        f"Epic Context: {state.get('epic_context', '')}\n"
        f"Preconditions: {state.get('preconditions', '')}\n"
        f"Scenarios: {scenarios_json}\n"
    )
    
    result = testcases_orchestrator_agent.invoke({
        "messages": [("user", user_message)]
    })
    
    messages = result.get("messages", [])
    tool_messages = [m for m in messages if getattr(m, 'type', '') == 'tool']
    if tool_messages:
        raw_content = tool_messages[-1].content
    else:
        raw_content = messages[-1].content if messages else ""
        
    output_str = extract_text(raw_content)
    
    # 3. Parse output
    try:
        clean_str = output_str.strip()
        if "```json" in clean_str:
            clean_str = clean_str.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_str:
            clean_str = clean_str.split("```")[1].split("```")[0].strip()
        parsed_testcases = json.loads(clean_str)
    except Exception:
        parsed_testcases = {"raw_output": output_str}

    # 4. Integrate with Xray Jira
    # Check if we should push to Xray based on environment configuration
    jira_base_url = os.getenv("JIRA_DOMAIN", "")
    jira_user = os.getenv("JIRA_USERNAME", "")
    jira_api_token = os.getenv("JIRA_API_KEY", "")
    xray_client_id = os.getenv("XRAY_CLIENT_ID", "")
    xray_client_secret = os.getenv("XRAY_CLIENT_SECRET", "")
    
    if all([jira_base_url, jira_user, jira_api_token, xray_client_id, xray_client_secret, story_key, project_key]):
        print(f"--- Pushing Test Cases to Xray Jira ({story_key}) ---")
        xray_tool = XrayJiraCompleteTraceabilityTool()
        
        # Prepare the tests JSON for XrayTool
        tests_data = parsed_testcases.get("testcases", []) if isinstance(parsed_testcases, dict) else parsed_testcases
        
        if tests_data and isinstance(tests_data, list):
            tests_json_str = json.dumps(tests_data)
            
            xray_result = xray_tool._run(
                jira_base_url=jira_base_url,
                jira_user=jira_user,
                jira_api_token=jira_api_token,
                xray_client_id=xray_client_id,
                xray_client_secret=xray_client_secret,
                project_key=project_key,
                story_key=story_key,
                tests_json=tests_json_str
            )
            print("Xray Integration Result:\n", xray_result)
            # You can inject the result into parsed_testcases if you want it logged
            if isinstance(parsed_testcases, dict):
                parsed_testcases["xray_sync_result"] = xray_result
    else:
        print("--- Skipping Xray Integration (Missing env vars or story key) ---")

    return {"testcases": parsed_testcases}
