import os
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()


def create_jira_subtask(parent_key: str, scenarios: dict) -> dict:
    """Creates a Jira subtask under the given parent issue with the generated test scenarios as the description.

    Args:
        parent_key (str): The Jira parent issue key (e.g., 'AUT-1').
        scenarios (dict): The generated test scenarios to embed in the subtask description.

    Returns:
        dict: Result containing the created subtask key or an error message.
    """
    project_key = parent_key.split("-")[0]

    if isinstance(scenarios, dict):
        description_text = json.dumps(scenarios.get("scenarios", scenarios), indent=2)
    else:
        description_text = str(scenarios)

    domain = os.getenv("JIRA_DOMAIN")
    username = os.getenv("JIRA_USERNAME")
    api_key = os.getenv("JIRA_API_KEY")

    if not domain or not username or not api_key:
        print("Missing Jira credentials")
        return {"error": "Missing Jira credentials"}

    url = f"{domain}/rest/api/2/issue"
    auth = HTTPBasicAuth(username, api_key)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": "Generated Test Scenarios for " + parent_key,
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
        return {"subtask_key": subtask_key}
    except Exception as e:
        print(f"Failed to create subtask: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(e.response.text)
        return {"error": str(e)}

