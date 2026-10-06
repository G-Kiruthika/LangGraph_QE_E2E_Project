from src.core.llm import llm
from src.tools.testcases_selfHealing_tool import TestCasesSelfHealingGeneratorToolV1
from langgraph.prebuilt import create_react_agent

testcases_self_healing_tool = TestCasesSelfHealingGeneratorToolV1()

system_prompt = "You are the Test Cases Orchestrator Agent. Your sole responsibility is to execute the TestCasesSelfHealingGeneratorToolV1 to generate and review test cases for a given Jira story and generated scenarios. Extract the required parameters from the user's input and pass them to the tool. IMPORTANT: You MUST output the exact raw JSON returned by the tool as your final answer. Do NOT summarize it, do NOT create markdown tables, just output the raw JSON."

testcases_orchestrator_agent = create_react_agent(
    model=llm,
    tools=[testcases_self_healing_tool],
    prompt=system_prompt
)
