import json
import re
from src.core.state import GraphState
from src.agents.fetch_jira_details_agent import fetch_jira_details_agent
from src.agents.create_subtask_jira_agent import create_subtask_jira_agent


def _extract_text(content) -> str:
    """Safely normalizes any content (str, list of dicts/strings, dict) into a single string."""
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


def _check_for_jira_error(content_str: str) -> str:
    """Helper to detect common Jira error messages in text."""
    if not isinstance(content_str, str):
        content_str = _extract_text(content_str)

    error_patterns = [
        r"HTTP error occurred:?\s*(\d{3}[^\n.]*)",
        r"(404\s+(?:Client Error|Not Found))",
        r"(could not be found)",
        r"(issue does not exist)",
        r"(missing api credentials)",
        r"(an unexpected error occurred:?[^\n.]*)",
        r"(unauthorized|forbidden|authentication failed)",
    ]
    for pattern in error_patterns:
        match = re.search(pattern, content_str, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def fetch_jira_story(state: GraphState):
    print("--- Fetching Jira Story via Agent ---")

    # Get the issue key from the state (passed in from main.py user input)
    issue_key = state.get("issue_key", "AUT-1")

    # Invoke the fetch_jira_details ReAct agent
    try:
        response = fetch_jira_details_agent.invoke({
            "messages": [("user", f"Fetch the Jira ticket {issue_key} and return its story description.")]
        })
    except Exception as e:
        error_msg = f"Failed to invoke Jira agent: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print("Stopping execution immediately.")
        return {"error": error_msg, "jira_story": ""}

    # 1. Check ToolMessages directly for structured errors from get_issue_details
    messages = response.get("messages", [])
    tool_error = None
    for msg in messages:
        if getattr(msg, "type", "") == "tool":
            raw_content = getattr(msg, "content", "")
            try:
                data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
                if isinstance(data, dict) and "error" in data:
                    tool_error = data["error"]
                    break
            except Exception:
                pass

    # 2. Extract final message content
    jira_story_content = ""
    if messages:
        last_msg = messages[-1]
        raw_val = getattr(last_msg, "content", "") if hasattr(last_msg, "content") else last_msg
        jira_story_content = _extract_text(raw_val)

    # 3. Detect if retrieval failed
    text_error = _check_for_jira_error(jira_story_content)
    detected_error = tool_error or text_error

    if detected_error or not jira_story_content or not jira_story_content.strip():
        fail_reason = detected_error or "Empty story description returned by Jira"
        full_error = f"Failed to retrieve Jira issue '{issue_key}': {fail_reason}"
        print(f"\n[ERROR] {full_error}")
        print("Stopping execution immediately.")
        return {"error": full_error, "jira_story": ""}

    return {"jira_story": jira_story_content}


def create_subtask(state: GraphState):
    print("--- Creating Jira Subtask for Generated Scenarios via Agent ---")

    # If previous step had an error, stop immediately
    if state.get("error"):
        return {"error": state["error"]}

    # Use issue_key from state
    parent_key = state.get("issue_key", "AUT-1")

    scenarios = state.get("test_scenarios", {})
    scenarios_json = json.dumps(scenarios) if isinstance(scenarios, dict) else str(scenarios)

    # Invoke the create_subtask_jira ReAct agent
    try:
        response = create_subtask_jira_agent.invoke({
            "messages": [(
                "user",
                f"Create a Jira subtask under parent issue {parent_key} with the following test scenarios:\n{scenarios_json}"
            )]
        })
    except Exception as e:
        error_msg = f"Failed to invoke subtask agent: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print("Stopping execution immediately.")
        return {"error": error_msg}

    # Inspect tool output for success / error
    messages = response.get("messages", [])
    subtask_error = None
    subtask_created = False
    subtask_key = None

    for msg in messages:
        if getattr(msg, "type", "") == "tool":
            raw_content = getattr(msg, "content", "")
            try:
                data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
                if isinstance(data, dict):
                    if "error" in data:
                        subtask_error = data["error"]
                    elif "subtask_key" in data and data["subtask_key"]:
                        subtask_created = True
                        subtask_key = data["subtask_key"]
            except Exception:
                pass

    # Extract final text message
    agent_text = ""
    if messages:
        last_msg = messages[-1]
        raw_val = getattr(last_msg, "content", "") if hasattr(last_msg, "content") else last_msg
        agent_text = _extract_text(raw_val)

    # Detect failure
    text_error = _check_for_jira_error(agent_text)
    if subtask_error or text_error or not subtask_created:
        fail_reason = subtask_error or text_error or agent_text or "Subtask creation failed"
        full_error = f"Failed to create Jira subtask under '{parent_key}': {fail_reason}"
        print(f"\n[ERROR] {full_error}")
        print("Stopping execution immediately.")
        return {"error": full_error}

    print(f"[SUCCESS] Subtask verified: {subtask_key}")
    return {"testcases": state.get("testcases", {})}
