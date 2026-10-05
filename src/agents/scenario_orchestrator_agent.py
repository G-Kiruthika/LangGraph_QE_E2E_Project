from src.core.llm import llm
from src.tools.scenario_self_healing_tool import ScenarioSelfHealingGeneratorToolV1
from langgraph.prebuilt import create_react_agent

# 1. Initialize the self-healing tool
scenario_self_healing_tool = ScenarioSelfHealingGeneratorToolV1()

# 2. Define the Orchestrator's prompt
system_prompt = "You are the Scenario Orchestrator Agent. Your sole responsibility is to execute the ScenarioSelfHealingGeneratorToolV1 to generate and review test scenarios for a given Jira story. Extract the required parameters from the user's input and pass them to the tool. IMPORTANT: You MUST output the exact raw JSON returned by the tool as your final answer. Do NOT summarize it, do NOT create markdown tables, just output the raw JSON."

# 3. Export the final agent executor (as a LangGraph compiled graph)
scenario_orchestrator_agent = create_react_agent(
    model=llm,
    tools=[scenario_self_healing_tool],
    prompt=system_prompt
)
