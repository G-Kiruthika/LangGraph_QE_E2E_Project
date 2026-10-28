import os
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.core.llm import llm

load_dotenv()


@tool
def create_jira_subtask_tool(parent_key: str, scenarios_json: str) -> dict:
    """Creates a Jira subtask under the given parent issue key with the generated test scenarios as the description.

    Args:
        parent_key (str): The Jira parent issue key (e.g., 'AUT-1').
        scenarios_json (str): JSON string of generated test scenarios to embed in the subtask description.

    Returns:
        dict: Result containing the created subtask key or an error message.
    """
    project_key = parent_key.split("-")[0]

    try:
        scenarios = json.loads(scenarios_json)
        description_text = json.dumps(
            scenarios.get("scenarios", scenarios) if isinstance(scenarios, dict) else scenarios,
            indent=2
        )
    except Exception:
        description_text = scenarios_json

    domain = os.getenv("JIRA_DOMAIN")
    username = os.getenv("JIRA_USERNAME")
    api_key = os.getenv("JIRA_API_KEY")

    if not domain or not username or not api_key:
        return {"error": "Missing Jira credentials in environment variables."}

    url = f"{domain}/rest/api/2/issue"
    auth = HTTPBasicAuth(username, api_key)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": f"Generated Test Scenarios for {parent_key}",
            "description": description_text,
            "issuetype": {"name": "Subtask"},
        }
    }

    try:
        response = requests.post(
            url, headers=headers, auth=auth, json=payload, verify=False, timeout=10
        )
        response.raise_for_status()
        new_issue = response.json()
        subtask_key = new_issue.get("key")
        print(f"Successfully created subtask: {subtask_key}")
        return {"subtask_key": subtask_key, "status": "success"}
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "response") and e.response is not None:
            error_msg += f" | Response: {e.response.text}"
        return {"error": error_msg}


system_message = """You are a Jira automation expert. Your job is to create a Jira subtask under a parent story.

Use the create_jira_subtask_tool with:
- parent_key: the Jira issue key provided (e.g., 'AUT-1')
- scenarios_json: the JSON string of generated test scenarios to attach

Always confirm the subtask was created successfully and return the subtask key."""

create_subtask_jira_agent = create_react_agent(
    model=llm,
    tools=[create_jira_subtask_tool],
    prompt=system_message
)

