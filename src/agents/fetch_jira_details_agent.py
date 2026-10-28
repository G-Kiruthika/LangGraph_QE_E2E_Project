from langgraph.prebuilt import create_react_agent
from src.core.llm import llm
from integrations.jira.fetch_jira import get_issue_details

# Tools for this agent
jira_tools = [get_issue_details]

system_message = """You are a Jira expert. Fetch ticket details using your tools and summarize the status.

After fetching the ticket, return the complete Jira issue information.
The final response must contain:
- issue_key
- summary
- description
- status

Do not invent any values. Use the information returned by the Jira tool."""

fetch_jira_details_agent = create_react_agent(
    model=llm,
    tools=jira_tools,
    prompt=system_message
)
