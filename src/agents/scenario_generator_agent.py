# src/agents/scenario_generator_agent.py
from src.core.llm import llm
from src.models.schemas import ScenarioResponse # The Pydantic model for a list of scenarios
from langchain_core.prompts import ChatPromptTemplate
from src.tools.rag_tools import orangehrmDomain_kb_tool

system_prompt = """You are an expert QA Engineer. Generate a list of test scenarios for the given Jira story.
Instructions:
1. Analyze all provided inputs carefully, especially the storydescription, preconditions, acbullets, and the provided Knowledge Base Context. 
2. Generate a comprehensive but minimal list of test scenarios covering positive, negative, edge, and boundary cases.   
3. Ensure no two scenarios are nearly identical (e.g., parameterize scenarios if necessary).   
4. Self-Healing Loop: If reviewerfeedback is provided, you MUST address the feedback and adjust your generated scenarios accordingly.  
5. Your output must strictly follow the required JSON array format below. 
6. Ensure all fields are present.  
7. Limit the number of scenarios generated to a maximum of 10 only.   
"""

from langgraph.prebuilt import create_react_agent

scenario_generator_agent = create_react_agent(
    model=llm,
    tools=[],
    prompt=system_prompt,
    response_format=ScenarioResponse
)
