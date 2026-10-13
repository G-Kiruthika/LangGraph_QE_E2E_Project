import os
import sys
import re
import json
import logging
import subprocess
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from src.agents.testscript_generator_agent import testscript_generator_agent
from src.tools.locator_extractor_tool import get_application_locators_tool

logger = logging.getLogger(__name__)

def _extract_text(content) -> str:
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

def _extract_python_code(content: Any) -> str:
    """Extracts raw python code from a markdown code block."""
    text = _extract_text(content).strip()
    if not text:
        return ""
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text

def _slugify(text: str, max_length: int = 40) -> str:
    """Generates a safe filename slug."""
    # Remove Jira tags like [QE-378]
    cleaned = re.sub(r"\[.*?\]", "", text).strip()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned).strip().lower()
    cleaned = re.sub(r"[-\s]+", "_", cleaned)
    return cleaned[:max_length].strip("_")

def _generate_playwright_html_report(report_path: str, story_summary: str, suite_results: List[Dict[str, Any]], videos_dir: str):
    """Generates a comprehensive Playwright HTML execution report for all generated test scripts."""
    video_files = []
    if os.path.exists(videos_dir):
        for f in os.listdir(videos_dir):
            if f.endswith(".webm") or f.endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(videos_dir, f), os.path.dirname(report_path))
                video_files.append((f, rel_path.replace("\\", "/")))

    total_tests = len(suite_results)
    passed_tests = sum(1 for r in suite_results if r.get("status") == "PASSED")
    failed_tests = sum(1 for r in suite_results if r.get("status") != "PASSED")
    healed_tests = sum(1 for r in suite_results if r.get("healed", False))

    overall_status = "ALL PASSED" if (failed_tests == 0 and total_tests > 0) else f"{passed_tests}/{total_tests} PASSED"
    overall_color = "#10b981" if failed_tests == 0 else ("#f59e0b" if passed_tests > 0 else "#ef4444")

    # Generate Test Case Rows
    testcase_rows_html = ""
    for r in suite_results:
        st = r.get("status", "UNKNOWN")
        st_color = "#10b981" if st == "PASSED" else "#ef4444"
        badge = f"<span style='color: {st_color}; font-weight: bold;'>{st}</span>"
        if r.get("healed"):
            badge += " <span style='background: #8b5cf6; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>HEALED</span>"

        tc_id = r.get("scenario_id", "TC")
        tc_summary = r.get("summary", "")
        file_name = os.path.basename(r.get("file", ""))
        rounds = r.get("rounds", 1)
        err = r.get("stderr", "") or ""

        testcase_rows_html += f"""
        <tr style="border-bottom: 1px solid #334155;">
            <td style="padding: 12px; font-weight: bold; color: #38bdf8;">{tc_id}</td>
            <td style="padding: 12px;">{tc_summary}</td>
            <td style="padding: 12px; font-family: monospace; font-size: 13px; color: #cbd5e1;">tests/{file_name}</td>
            <td style="padding: 12px;">{rounds}</td>
            <td style="padding: 12px;">{badge}</td>
        </tr>
        """

    # Video Blocks
    video_html_blocks = ""
    if video_files:
        for fname, vrel in video_files:
            video_html_blocks += f"""
            <div class="video-card">
                <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #94a3b8;">{fname}</h4>
                <video controls width="100%" style="border-radius: 8px; border: 1px solid #334155;">
                    <source src="{vrel}" type="video/webm">
                    Your browser does not support the video tag.
                </video>
            </div>
            """
    else:
        video_html_blocks = "<p style='color: #94a3b8;'>No video recordings found in directory.</p>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playwright Test Suite Execution Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .badge {{
            padding: 8px 16px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            background-color: {overall_color};
            color: #ffffff;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
        }}
        .card h4 {{
            margin: 0 0 8px 0;
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
        }}
        .card p {{
            margin: 0;
            font-size: 22px;
            font-weight: 700;
        }}
        .section {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            padding: 12px;
            background: #0f172a;
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
            border-bottom: 2px solid #334155;
        }}
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
        }}
        .video-card {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin: 0 0 8px 0;">Playwright Test Suite Execution Report</h1>
                <p style="margin: 0; color: #94a3b8;">Jira Story: <strong>{story_summary}</strong></p>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Test Scripts Folder: <code>tests/</code></p>
            </div>
            <div class="badge">{overall_status}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h4>Total Test Scripts</h4>
                <p>{total_tests}</p>
            </div>
            <div class="card">
                <h4>Passed</h4>
                <p style="color: #10b981;">{passed_tests}</p>
            </div>
            <div class="card">
                <h4>Failed</h4>
                <p style="color: {'#ef4444' if failed_tests > 0 else '#94a3b8'};">{failed_tests}</p>
            </div>
            <div class="card">
                <h4>Self-Healed</h4>
                <p style="color: #8b5cf6;">{healed_tests}</p>
            </div>
            <div class="card">
                <h4>Execution Videos</h4>
                <p>{len(video_files)}</p>
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Test Cases & Individual Test Scripts (in tests/)</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Summary</th>
                        <th>Script File</th>
                        <th>Rounds</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {testcase_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Execution Video Recordings</h2>
            <div class="video-grid">
                {video_html_blocks}
            </div>
        </div>
    </div>
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[REPORT] Consolidated Playwright HTML report generated at: {report_path}")


class ScriptSelfHealingSchema(BaseModel):
    story_summary: str = Field(..., description="Summary of the Jira story")
    testcases_json: str = Field(..., description="JSON string of the generated test cases")
    target_url: str = Field("https://opensource-demo.orangehrmlive.com/web/index.php/auth/login", description="Target application URL")
    max_retries: int = Field(5, description="Maximum self-healing rounds per test script on failure")

class ScriptSelfHealingTool(BaseTool):
    name: str = "ScriptSelfHealingTool"
    description: str = (
        "Generates individual Playwright Python test scripts for each test case in the tests/ folder, "
        "executes them against the application, and automatically self-heals scripts if failures occur."
    )
    args_schema: Type[BaseModel] = ScriptSelfHealingSchema

    def _execute_script(self, script_path: str, timeout_seconds: int = 90) -> Dict[str, Any]:
        """Executes a test script using the current Python environment and captures output."""
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0
            }
        except subprocess.TimeoutExpired as e:
            return {
                "exit_code": -1,
                "stdout": e.stdout or "",
                "stderr": f"Execution timed out after {timeout_seconds}s",
                "passed": False
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "passed": False
            }

    def _run(self, story_summary: str, testcases_json: str, target_url: str = "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login", max_retries: int = 5, **kwargs) -> str:
        max_retries = int(kwargs.get("max_retries") or max_retries or os.getenv("SCRIPT_MAX_RETRIES", 5))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Test scripts destination folder is tests/
        tests_dir = os.path.join(base_dir, "tests")
        reports_dir = os.path.join(base_dir, "outputs", "reports")
        videos_dir = os.path.join(reports_dir, "videos")
        
        os.makedirs(tests_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)

        report_file_path = os.path.join(reports_dir, "playwright_report.html")

        # 1. Parse test cases into a list
        parsed_cases = []
        try:
            data = json.loads(testcases_json)
            if isinstance(data, list):
                parsed_cases = data
            elif isinstance(data, dict):
                if "testcases" in data and isinstance(data["testcases"], list):
                    parsed_cases = data["testcases"]
                else:
                    parsed_cases = [data]
        except Exception:
            # Fallback if raw text
            parsed_cases = [{"scenario_id": "TS-01", "summary": story_summary, "description": testcases_json, "steps": []}]

        print(f"\n--- [Self-Healing Script Tool] Loaded {len(parsed_cases)} test case(s) for script generation in tests/ ---")

        # 2. Retrieve Locators Context once for efficiency
        print("--- [Self-Healing Script Tool] Fetching latest application locators ---")
        try:
            locators_context = get_application_locators_tool.invoke({"query_or_url": target_url})
        except Exception as e:
            locators_context = f"Locator extraction fallback ({e})"

        # 3. Process each testcase into a separate test script in tests/
        suite_results = []
        all_scripts_code = {}

        for idx, tc in enumerate(parsed_cases):
            tc_id = tc.get("scenario_id") or f"TS-{idx+1:02d}"
            tc_summary = tc.get("summary") or f"Test Case {tc_id}"
            clean_id = tc_id.lower().replace("-", "_")
            slug = _slugify(tc_summary)
            if not slug:
                slug = f"scenario_{idx+1}"
            
            script_filename = f"test_{clean_id}_{slug}.py"
            script_file_path = os.path.join(tests_dir, script_filename)

            print(f"\n=======================================================")
            print(f"[{idx+1}/{len(parsed_cases)}] Generating & Healing Script: tests/{script_filename}")
            print(f"Test Case: {tc_id} - {tc_summary}")
            print(f"=======================================================")

            # Prompt agent for this specific test case
            prompt = (
                f"Jira Story: {story_summary}\n"
                f"Target URL: {target_url}\n"
                f"Generate a single standalone Playwright Python test script for the following test case:\n"
                f"Scenario ID: {tc_id}\n"
                f"Summary: {tc_summary}\n"
                f"Details: {json.dumps(tc, indent=2)}\n\n"
                f"Application Locators Context:\n{locators_context}\n\n"
                f"Requirements:\n"
                f"- Name the test function `def test_{clean_id}_{slug}(page):`\n"
                f"- Include necessary imports and helper functions (`navigate_to`, `login_to_orangehrm` if dashboard auth is required)\n"
                f"- If testing login page, ensure `page.context.clear_cookies()` is called before navigation\n"
                f"- Include the `if __name__ == '__main__':` runner block with video recording to `outputs/reports/videos`\n"
                f"- Return ONLY the Python code inside ```python ```"
            )

            agent_res = testscript_generator_agent.invoke({"messages": [("user", prompt)]})
            last_msg = agent_res.get("messages", [])[-1]
            raw_code = getattr(last_msg, "content", "") if hasattr(last_msg, "content") else str(last_msg)
            current_script = _extract_python_code(raw_code)

            # Self-healing loop for this testcase
            rounds = 0
            is_passed = False
            last_exec = {}

            while rounds < max_retries:
                rounds += 1
                print(f"[RUN] Executing tests/{script_filename} (Round {rounds}/{max_retries})...")

                with open(script_file_path, "w", encoding="utf-8") as f:
                    f.write(current_script)

                exec_result = self._execute_script(script_file_path)
                last_exec = exec_result

                if exec_result["passed"]:
                    print(f"[PASSED] tests/{script_filename} executed successfully in Round {rounds}!")
                    is_passed = True
                    break
                else:
                    err_snippet = (exec_result["stderr"] or exec_result["stdout"] or "Execution failed").strip()
                    safe_snip = err_snippet[:250].encode("ascii", errors="replace").decode("ascii")
                    print(f"[FAILED] Round {rounds} failed: {safe_snip}...")

                    if rounds >= max_retries:
                        print(f"Reached max retries ({max_retries}) for tests/{script_filename}.")
                        break

                    print(f"[HEALING] Self-healing tests/{script_filename} for Round {rounds + 1}...")
                    heal_prompt = (
                        f"The test script tests/{script_filename} for {tc_id} failed with the following error:\n\n"
                        f"=== SCRIPT ===\n{current_script}\n\n"
                        f"=== ERROR TRACEBACK ===\n{err_snippet}\n\n"
                        f"=== LOCATORS CONTEXT ===\n{locators_context}\n\n"
                        "Inspect the error and update the selectors, waits, or assertions so it passes. "
                        "Return ONLY the updated Python script inside ```python ```."
                    )
                    heal_res = testscript_generator_agent.invoke({"messages": [("user", heal_prompt)]})
                    h_msg = heal_res.get("messages", [])[-1]
                    h_code = getattr(h_msg, "content", "") if hasattr(h_msg, "content") else str(h_msg)
                    current_script = _extract_python_code(h_code)

            # Save final version to tests/
            with open(script_file_path, "w", encoding="utf-8") as f:
                f.write(current_script)

            status_str = "PASSED" if is_passed else "FAILED"
            suite_results.append({
                "scenario_id": tc_id,
                "summary": tc_summary,
                "file": script_file_path,
                "status": status_str,
                "rounds": rounds,
                "healed": is_passed and rounds > 1,
                "stdout": last_exec.get("stdout", ""),
                "stderr": last_exec.get("stderr", "")
            })
            all_scripts_code[script_filename] = current_script

        # 4. Generate Consolidated Playwright HTML Report
        try:
            _generate_playwright_html_report(
                report_path=report_file_path,
                story_summary=story_summary,
                suite_results=suite_results,
                videos_dir=videos_dir
            )
        except Exception as e:
            print(f"Warning: Failed to generate HTML report: {e}")

        # 5. Run Pytest across the entire tests/ folder
        pytest_report_path = os.path.join(reports_dir, "pytest_report.html")
        try:
            print(f"\n--- [Self-Healing Script Tool] Executing Pytest suite across tests/ ---")
            subprocess.run(
                [sys.executable, "-m", "pytest", tests_dir, f"--html={pytest_report_path}", "--self-contained-html"],
                capture_output=True,
                text=True,
                timeout=120
            )
            print(f"[REPORT] Pytest HTML report generated at: {pytest_report_path}")
        except Exception as e:
            print(f"Notice: Pytest run encountered: {e}")

        overall_passed = all(r.get("status") == "PASSED" for r in suite_results)
        final_summary = {
            "status": "ALL_PASSED" if overall_passed else "PARTIAL_PASSED",
            "total_tests": len(suite_results),
            "passed_count": sum(1 for r in suite_results if r.get("status") == "PASSED"),
            "failed_count": sum(1 for r in suite_results if r.get("status") != "PASSED"),
            "healed_count": sum(1 for r in suite_results if r.get("healed")),
            "tests_dir": tests_dir,
            "generated_scripts": suite_results,
            "report_file": report_file_path,
            "pytest_report_file": pytest_report_path,
            "videos_dir": videos_dir
        }

        return json.dumps(final_summary, indent=2)
