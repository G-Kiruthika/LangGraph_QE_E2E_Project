from src.core.llm import llm
from src.models.schemas import TestCaseResponse
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

system_prompt = """You are an expert QA Engineer. Generate a list of detailed test cases based on the provided Jira story and generated test scenarios.

Instructions:
1. Analyze all provided inputs carefully, especially the story description, the generated scenarios, and the Knowledge Base Context. 
2. For each provided test scenario, generate a detailed testcase including the exact steps, test data, and expected results.
3. Your output must strictly follow the required JSON array format below. 
4. Ensure all fields are present, including traceability to the original 'scenario_id'.
5. Include both "**Preconditions:**" and "**Postconditions:**" directly inside the `description` string itself.
6. The `test_type` must be one of: "Functional", "Non-functional", "Negative", "Integration".
7. Self-Healing Loop: If reviewer feedback is provided, you MUST address the feedback and adjust your generated testcases accordingly.

Expected JSON Array format for testcases:
[
  {
    "summary": "[QE-378] Verify successful login",
    "description": "**Objective:** Ensure user can login.\\n\\n**Preconditions:**\\nUser is registered.\\n\\n**Postconditions:**\\nUser session is created.",
    "test_type": "Functional",
    "scenario_id": "TS-01",
    "steps": [
      {
        "action": "Navigate to login page",
        "data": "URL",
        "expected_result": "Login page appears"
      }
    ]
  }
]
"""

testcases_generator_agent = create_react_agent(
    model=llm,
    tools=[],
    prompt=system_prompt,
    response_format=TestCaseResponse
)
