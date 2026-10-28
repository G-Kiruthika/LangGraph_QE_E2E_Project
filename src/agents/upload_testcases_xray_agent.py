import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.core.llm import llm
from integrations.jira.xray_jira_tool import XrayJiraCompleteTraceabilityTool

load_dotenv()

_xray_tool_instance = XrayJiraCompleteTraceabilityTool()


@tool
def upload_testcases_to_xray(
    project_key: str,
    story_key: str,
    tests_json: str,
) -> str:
    """Uploads generated test cases to Xray Jira and links them to the parent story.

    Args:
        project_key (str): The Jira project key (e.g., 'AUT').
        story_key (str): The Jira story key to link tests to (e.g., 'AUT-1').
        tests_json (str): JSON string containing the list of test cases with steps.

    Returns:
        str: A summary of created tests and their link status.
    """
    jira_base_url = os.getenv("JIRA_DOMAIN", "")
    jira_user = os.getenv("JIRA_USERNAME", "")
    jira_api_token = os.getenv("JIRA_API_KEY", "")
    xray_client_id = os.getenv("XRAY_CLIENT_ID", "")
    xray_client_secret = os.getenv("XRAY_CLIENT_SECRET", "")

    if not all([jira_base_url, jira_user, jira_api_token, xray_client_id, xray_client_secret]):
        return "ERROR: Missing Xray/Jira credentials in environment variables."

    return _xray_tool_instance._run(
        jira_base_url=jira_base_url,
        jira_user=jira_user,
        jira_api_token=jira_api_token,
        xray_client_id=xray_client_id,
        xray_client_secret=xray_client_secret,
        project_key=project_key,
        story_key=story_key,
        tests_json=tests_json,
    )


system_message = """You are an Xray Jira integration expert. Your job is to upload test cases to Xray Jira and link them to the parent user story.

Use the upload_testcases_to_xray tool with:
- project_key: the Jira project key extracted from the story key (e.g., 'AUT' from 'AUT-1')
- story_key: the full Jira story key (e.g., 'AUT-1')
- tests_json: a JSON string of the test cases list

Always report the results of each test case upload and linking operation."""

upload_testcases_xray_agent = create_react_agent(
    model=llm,
    tools=[upload_testcases_to_xray],
    prompt=system_message
)

