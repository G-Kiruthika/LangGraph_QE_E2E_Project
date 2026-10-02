import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from langchain_core.tools import tool

# Load environment variables from .env
load_dotenv()

@tool
def get_issue_details(issue_key: str) -> dict:
    """Retrieves key details for a specific issue key (e.g., 'PROJ-123').

    Args:
        issue_key (str): The unique issue identifier, such as 'KAN-1' or 'PROJ-42'.

    Returns:
        dict: Issue details including summary, status, assignee, and issue key.
    """
    domain = os.getenv("JIRA_DOMAIN")
    username = os.getenv("JIRA_USERNAME")
    api_key = os.getenv("JIRA_API_KEY")

    if not domain or not username or not api_key:
        return {"error": "Missing API credentials in environment variables."}

    url = f"{domain}/rest/api/3/issue/{issue_key}"
    auth = HTTPBasicAuth(username, api_key)
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, auth=auth, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract relevant fields to keep response clean for the LLM
        fields = data.get("fields", {})
        return {
            "key": data.get("key"),
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            "created": fields.get("created"),
        }

    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except Exception as err:
        return {"error": f"An unexpected error occurred: {str(err)}"}