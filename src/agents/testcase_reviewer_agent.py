from src.core.llm import llm
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# Define what the reviewer should return
class ReviewResponse(BaseModel):
    confidence: int = Field(description="Score from 0 to 100")
    feedback: str = Field(description="Detailed feedback on what is missing or duplicated")
    approved: bool = Field(description="True if confidence is >= 85")

system_prompt = """
You are a strict QA Reviewer. Review the provided test cases against the Jira story and the generated scenarios.

Instructions:
1. Review the generated test cases against the story details and the provided scenarios. 
2. Evaluate them based on two main criteria:
   a. Traceability: Are all test cases correctly linked back to a scenario_id?
   b. Quality: Do the test cases have clear action, data, and expected_result steps? Are preconditions and postconditions included in the description? Is the test_type appropriate?
3. Calculate a confidence score from 0 to 100 representing how good the test cases are. 
4. Provide detailed feedback explaining what needs to be improved, and list the strengths and gaps. 
5. Return ONLY a valid JSON object matching the required structure. 
 """

testcase_reviewer_agent = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "Story & Scenarios: {story_details}\n\nTest Cases: {testcases}")
]) | llm.with_structured_output(ReviewResponse)
