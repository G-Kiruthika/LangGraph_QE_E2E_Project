from src.core.state import GraphState
from src.agents.fetch_jira_details_agent import jira_agent

def fetch_jira_story(state: GraphState):
    print("--- Fetching Jira Story via Agent ---")
    
    # Get the issue key from the state (e.g., PROJ-123)
    # We assume the ticket ID is in the 'testcases' key or can be inferred
    issue_key = "QE-378" # Updated to test with QE-378
    
    # Invoke the ReAct agent
    response = jira_agent.invoke({
        "messages": [("user", f"Fetch the Jira ticket {issue_key} and return its story description.")]
    })
    
    # Extract the final response from the agent
    # The response is usually in the 'messages' key as a list
    jira_story_content = ""
    if "messages" in response and response["messages"]:
        last_msg = response["messages"][-1]
        # Handle different possible response formats
        if hasattr(last_msg, 'content'):
            jira_story_content = last_msg.content
        elif isinstance(last_msg, dict):
             jira_story_content = last_msg.get('content', '')
        else:
            jira_story_content = str(last_msg)
    
    return {"jira_story": jira_story_content}

import os
import requests
import json
from requests.auth import HTTPBasicAuth

def create_subtask(state: GraphState):
    print("--- Creating Jira Subtask for Generated Scenarios ---")
    
    parent_key = "QE-378"
    project_key = parent_key.split("-")[0]
    
    scenarios = state.get("test_scenarios", {})
    if isinstance(scenarios, dict):
        description_text = json.dumps(scenarios.get("scenarios", scenarios), indent=2)
    else:
        description_text = str(scenarios)
        
    domain = os.getenv("JIRA_DOMAIN")
    username = os.getenv("JIRA_USERNAME")
    api_key = os.getenv("JIRA_API_KEY")
    
    if not domain or not username or not api_key:
        print("Missing Jira credentials")
        return {"testcases": {"error": "Missing Jira credentials"}}

    url = f"{domain}/rest/api/2/issue"
    auth = HTTPBasicAuth(username, api_key)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": "Generated Test Scenarios for " + parent_key,
            "description": description_text,
            "issuetype": {"name": "Subtask"}
        }
    }
    
    try:
        # verify=False is used in your get_issue_details as well, so keeping consistency
        response = requests.post(url, headers=headers, auth=auth, json=payload, verify=False, timeout=10)
        response.raise_for_status()
        new_issue = response.json()
        print(f"Successfully created subtask: {new_issue.get('key')}")
    except Exception as e:
        print(f"Failed to create subtask: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(e.response.text)
             
    return {"testcases": state.get("testcases", {})}
