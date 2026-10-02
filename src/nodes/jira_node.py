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
