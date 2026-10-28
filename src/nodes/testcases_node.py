import json
import os
from dotenv import load_dotenv
from src.core.state import GraphState
from src.agents.testcases_orchestrator_agent import testcases_orchestrator_agent
from src.agents.upload_testcases_xray_agent import upload_testcases_xray_agent

load_dotenv()


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, dict):
                parts.append(json.dumps(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, dict):
        return json.dumps(content)
    return str(content) if content is not None else ""


def generate_test_cases(state: GraphState):
    print("--- Generating Test Cases with Self-Healing ---")

    # If previous step had an error, stop immediately
    if state.get("error"):
        return {"error": state["error"]}

    # 1. Extract data from GraphState
    story_details = state.get("story_details", {})
    if isinstance(story_details, dict):
        summary = story_details.get("summary", "")
        description = story_details.get("description", "")
        story_key = story_details.get("issue_key", "")
    else:
        summary = ""
        description = str(story_details)
        story_key = ""

    jira_story = extract_text(state.get("jira_story", ""))
    if not description and jira_story:
        description = jira_story
    if not summary and jira_story:
        summary = jira_story[:100]

    # Use issue_key from state if not found in story_details
    if not story_key:
        story_key = state.get("issue_key", "")

    scenarios = state.get("test_scenarios", {})
    scenarios_json = json.dumps(scenarios) if isinstance(scenarios, dict) else str(scenarios)

    # If story_key wasn't parsed properly, attempt to extract it from description
    if not story_key and "**issue_key:**" in description:
        for line in description.splitlines():
            if "**issue_key:**" in line:
                story_key = line.split("**issue_key:**")[1].strip()
                break

    project_key = story_key.split("-")[0] if "-" in story_key else ""

    # 2. Invoke Orchestrator
    user_message = (
        f"Summary: {summary}\n"
        f"Description: {description}\n"
        f"Epic Context: {state.get('epic_context', '')}\n"
        f"Preconditions: {state.get('preconditions', '')}\n"
        f"Scenarios: {scenarios_json}\n"
    )

    try:
        result = testcases_orchestrator_agent.invoke({
            "messages": [("user", user_message)]
        })
    except Exception as e:
        error_msg = f"Failed to generate test cases: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print("Stopping execution immediately.")
        return {"error": error_msg}

    messages = result.get("messages", [])
    tool_messages = [m for m in messages if getattr(m, 'type', '') == 'tool']
    if tool_messages:
        raw_content = tool_messages[-1].content
    else:
        raw_content = messages[-1].content if messages else ""

    output_str = extract_text(raw_content)

    # 3. Parse output
    try:
        clean_str = output_str.strip()
        if "```json" in clean_str:
            clean_str = clean_str.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_str:
            clean_str = clean_str.split("```")[1].split("```")[0].strip()
        parsed_testcases = json.loads(clean_str)
    except Exception:
        parsed_testcases = {"raw_output": output_str}

    # Verify testcases were generated
    if isinstance(parsed_testcases, dict) and "error" in parsed_testcases:
        error_msg = f"Test cases generation failed: {parsed_testcases['error']}"
        print(f"\n[ERROR] {error_msg}")
        print("Stopping execution immediately.")
        return {"error": error_msg, "testcases": parsed_testcases}

    # 4. Integrate with Xray Jira via the upload_testcases_xray_agent
    xray_client_id = os.getenv("XRAY_CLIENT_ID", "")
    xray_client_secret = os.getenv("XRAY_CLIENT_SECRET", "")
    jira_base_url = os.getenv("JIRA_DOMAIN", "")
    jira_user = os.getenv("JIRA_USERNAME", "")
    jira_api_token = os.getenv("JIRA_API_KEY", "")

    has_xray_credentials = all([jira_base_url, jira_user, jira_api_token, xray_client_id, xray_client_secret])

    if has_xray_credentials and story_key and project_key:
        print(f"--- Pushing Test Cases to Xray Jira ({story_key}) via Agent ---")

        tests_data = parsed_testcases.get("testcases", []) if isinstance(parsed_testcases, dict) else parsed_testcases

        if tests_data and isinstance(tests_data, list):
            tests_json_str = json.dumps(tests_data)

            try:
                xray_response = upload_testcases_xray_agent.invoke({
                    "messages": [(
                        "user",
                        f"Upload the following test cases to Xray Jira for project '{project_key}' "
                        f"and story '{story_key}':\n{tests_json_str}"
                    )]
                })

                xray_messages = xray_response.get("messages", [])
                if xray_messages:
                    last_xray_msg = xray_messages[-1]
                    raw_val = (
                        last_xray_msg.content
                        if hasattr(last_xray_msg, "content")
                        else str(last_xray_msg)
                    )
                    xray_result = extract_text(raw_val)
                else:
                    xray_result = "ERROR: Xray agent returned no messages."
            except Exception as e:
                xray_result = f"ERROR: Exception invoking Xray agent: {str(e)}"

            print("Xray Integration Result:\n", xray_result)

            # STOP IF THERE IS AN ERROR UPLOADING TO XRAY
            if "ERROR:" in xray_result or "failed" in xray_result.lower():
                fail_reason = f"Xray testcase upload failed for '{story_key}': {xray_result}"
                print(f"\n[ERROR] {fail_reason}")
                print("Stopping execution immediately.")
                return {"error": fail_reason, "testcases": parsed_testcases}

            if isinstance(parsed_testcases, dict):
                parsed_testcases["xray_sync_result"] = xray_result
        else:
            fail_reason = "No valid test cases list found to upload to Xray"
            print(f"\n[ERROR] {fail_reason}")
            print("Stopping execution immediately.")
            return {"error": fail_reason, "testcases": parsed_testcases}

    elif has_xray_credentials and not (story_key and project_key):
        fail_reason = f"Cannot upload to Xray: missing valid story_key ('{story_key}') or project_key ('{project_key}')"
        print(f"\n[ERROR] {fail_reason}")
        print("Stopping execution immediately.")
        return {"error": fail_reason, "testcases": parsed_testcases}
    else:
        print("--- Skipping Xray Integration (Missing env vars) ---")

    return {"testcases": parsed_testcases}
