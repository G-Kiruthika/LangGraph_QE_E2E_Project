
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.core.llm import llm
from src.models.schemas import JiraIssueOutput
from src.tools.tools import get_issue_details

jira_tools = [get_issue_details]

system_message = """You are a Jira expert. Fetch ticket details using your tools and summarize the status.

After fetching the ticket, return the complete Jira issue information.
The final response must contain:
- issue_key
- summary
- description
- status

Do not invent any values. Use the information returned by the Jira tool."""

jira_agent = create_react_agent(
    model=llm,
    tools=jira_tools,
    prompt=system_message
)
