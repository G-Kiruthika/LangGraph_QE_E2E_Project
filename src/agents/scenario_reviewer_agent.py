# src/agents/scenario_reviewer_agent.py
from src.core.llm import llm
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# Define what the reviewer should return
class ReviewResponse(BaseModel):
    confidence: int = Field(description="Score from 0 to 100")
    feedback: str = Field(description="Detailed feedback on what is missing or duplicated")
    approved: bool = Field(description="True if confidence is >= 85")

system_prompt = """
You are a strict QA Reviewer. Review the provided test scenarios against the Jira story.
Instructions:
1.Review the generated scenarios against the story details (storydescription, acbullets, preconditions). 
2.Evaluate them based on two main criteria:
a. Coverage: Are all acceptance criteria and requirements covered? Are negative, edge, and boundary cases considered?
b. Redundancy: Are there near-identical scenarios that should be collapsed into one parameterized scenario?   
3.Calculate a confidence score from 0 to 100 representing how good the scenarios are. 
4.Provide detailed feedback explaining what needs to be improved, and list the strengths and gaps. 
5.Return ONLY a valid JSON object matching the required structure. 
 """

scenario_reviewer_agent = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "Story: {story_details}\n\nScenarios: {scenarios}")
]) | llm.with_structured_output(ReviewResponse)
