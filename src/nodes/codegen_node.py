import os
import json
from src.core.state import GraphState
from src.tools.script_self_healing_tool import ScriptSelfHealingTool

script_healing_tool = ScriptSelfHealingTool()

def generate_and_heal_test_scripts(state: GraphState):
    print("\n--- Generating & Self-Healing Playwright Test Scripts ---")
    
    # 1. Extract testcases from state
    testcases_data = state.get("testcases", {})
    if isinstance(testcases_data, dict):
        # Could be wrapped in {"testcases": [...]} or raw dict
        testcases_list = testcases_data.get("testcases", testcases_data)
        testcases_json = json.dumps(testcases_list, indent=2)
    else:
        testcases_json = str(testcases_data)

    # 2. Extract story summary or title
    story_content = state.get("jira_story", "")
    if isinstance(story_content, list):
        story_summary = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in story_content])
    elif isinstance(story_content, dict):
        story_summary = story_content.get("summary", json.dumps(story_content))
    else:
        story_summary = str(story_content)

    if not story_summary or len(story_summary.strip()) == 0:
        story_summary = "OrangeHRM Login and Dashboard Test Suite"
    else:
        story_summary = story_summary[:200]

    # Target URL can be inferred or default to OrangeHRM demo
    target_url = "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login"

    # 3. Run Self-Healing Test Script Tool
    max_retries = int(os.getenv("SCRIPT_MAX_RETRIES", "5"))
    tool_output_str = script_healing_tool._run(
        story_summary=story_summary,
        testcases_json=testcases_json,
        target_url=target_url,
        max_retries=max_retries
    )

    try:
        tool_output = json.loads(tool_output_str)
        playwright_code = tool_output.get("code", "")
        status = tool_output.get("status", "UNKNOWN")
        rounds = tool_output.get("rounds", 1)
        healed = tool_output.get("self_healed", False)
        report_file = tool_output.get("report_file", "")
        if report_file:
            print(f"--- Playwright HTML Report: {report_file} ---")
        print(f"--- Test Script Generation Finished: Status={status}, Rounds={rounds}, Healed={healed} ---")
    except Exception as e:
        print(f"Warning parsing tool output: {e}")
        try:
            parsed = json.loads(tool_output_str)
            playwright_code = parsed.get("code", tool_output_str)
        except Exception:
            playwright_code = tool_output_str
        print("--- Test Script Generation Finished ---")

    return {"playwright_code": playwright_code}
