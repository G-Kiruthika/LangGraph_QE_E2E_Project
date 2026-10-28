import os
import json
from src.core.state import GraphState
from integrations.orchestration_tools.script_self_healing import ScriptSelfHealingTool

script_healing_tool = ScriptSelfHealingTool()


def generate_and_heal_test_scripts(state: GraphState):
    print("\n--- Generating & Self-Healing Individual Playwright Test Scripts in outputs/final_testscripts/ ---")

    # 1. Extract testcases from state
    testcases_data = state.get("testcases", {})
    if isinstance(testcases_data, dict):
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

    target_url = "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login"

    # 3. Run Self-Healing Test Script Tool (outputs to outputs/final_testscripts/)
    max_retries = int(os.getenv("SCRIPT_MAX_RETRIES", "5"))
    tool_output_str = script_healing_tool._run(
        story_summary=story_summary,
        testcases_json=testcases_json,
        target_url=target_url,
        max_retries=max_retries
    )

    generated_scripts = []
    try:
        tool_output = json.loads(tool_output_str)
        status = tool_output.get("status", "UNKNOWN")
        total_tests = tool_output.get("total_tests", 0)
        passed_count = tool_output.get("passed_count", 0)
        healed_count = tool_output.get("healed_count", 0)
        report_file = tool_output.get("report_file", "")
        generated_scripts = tool_output.get("generated_scripts", [])

        print(f"\n--- Test Scripts Generation Completed ---")
        print(f"Overall Status: {status} ({passed_count}/{total_tests} Passed, {healed_count} Healed)")
        print(f"Playwright HTML Report: {report_file}")
        print("Generated Test Scripts in outputs/final_testscripts/:")
        for s in generated_scripts:
            print(f"  - [{s.get('status')}] {s.get('scenario_id')}: outputs/final_testscripts/{os.path.basename(s.get('file', ''))} (Rounds: {s.get('rounds')})")
    except Exception as e:
        print(f"Warning parsing tool output: {e}")

    return {
        "playwright_code": tool_output_str,
        "generated_test_scripts": generated_scripts
    }
