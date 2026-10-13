import os
import sys
import json
import logging
import subprocess
from typing import Type, Dict, Any
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

def _generate_playwright_html_report(report_path: str, story_summary: str, status: str, rounds: int, self_healed: bool, stdout: str, stderr: str, script_code: str, videos_dir: str):
    """Generates a comprehensive Playwright HTML execution report with embedded video recordings."""
    video_files = []
    if os.path.exists(videos_dir):
        for f in os.listdir(videos_dir):
            if f.endswith(".webm") or f.endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(videos_dir, f), os.path.dirname(report_path))
                video_files.append(rel_path.replace("\\", "/"))

    status_color = "#10b981" if status == "PASSED" else "#ef4444"
    if self_healed:
        status_color = "#8b5cf6"

    video_html_blocks = ""
    if video_files:
        for idx, vf in enumerate(video_files):
            video_html_blocks += f"""
            <div class="video-card">
                <h4>Recording #{idx+1}: {os.path.basename(vf)}</h4>
                <video controls width="100%" style="border-radius: 8px; border: 1px solid #334155; margin-top: 8px;">
                    <source src="{vf}" type="video/webm">
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
    <title>Playwright Test Execution Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1100px;
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
            background-color: {status_color};
            color: #ffffff;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
            font-size: 20px;
            font-weight: 600;
        }}
        .section {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        pre {{
            background: #090d16;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            color: #38bdf8;
            font-size: 13px;
        }}
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
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
                <h1 style="margin: 0 0 8px 0;">Playwright Test Execution Report</h1>
                <p style="margin: 0; color: #94a3b8;">Jira Story: <strong>{story_summary}</strong></p>
            </div>
            <div class="badge">{status}</div>
        </div>

        <div class="grid">
            <div class="card">
                <h4>Status</h4>
                <p style="color: {status_color};">{status}</p>
            </div>
            <div class="card">
                <h4>Execution Rounds</h4>
                <p>{rounds}</p>
            </div>
            <div class="card">
                <h4>Self-Healed</h4>
                <p>{'Yes' if self_healed else 'No'}</p>
            </div>
            <div class="card">
                <h4>Recorded Videos</h4>
                <p>{len(video_files)} file(s)</p>
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0;">Execution Videos</h2>
            <div class="video-grid">
                {video_html_blocks}
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0;">Console Output</h2>
            <h4>Standard Output:</h4>
            <pre>{stdout or 'No stdout recorded'}</pre>
            {f'<h4>Standard Error:</h4><pre style="color: #f87171;">{stderr}</pre>' if stderr else ''}
        </div>

        <div class="section">
            <h2 style="margin-top: 0;">Generated Playwright Script</h2>
            <pre style="color: #a7f3d0;">{script_code}</pre>
        </div>
    </div>
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[REPORT] Playwright HTML report generated at: {report_path}")


class ScriptSelfHealingSchema(BaseModel):
    story_summary: str = Field(..., description="Summary of the Jira story")
    testcases_json: str = Field(..., description="JSON string of the generated test cases")
    target_url: str = Field("https://opensource-demo.orangehrmlive.com/web/index.php/auth/login", description="Target application URL")
    max_retries: int = Field(5, description="Maximum self-healing rounds on execution failure")

class ScriptSelfHealingTool(BaseTool):
    name: str = "ScriptSelfHealingTool"
    description: str = (
        "Generates Playwright Python test scripts for test cases, executes them against the application, "
        "and automatically self-heals the script if execution errors or locator failures occur."
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
        scripts_dir = os.path.join(base_dir, "outputs", "test_scripts")
        reports_dir = os.path.join(base_dir, "outputs", "reports")
        videos_dir = os.path.join(reports_dir, "videos")
        
        os.makedirs(scripts_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)

        script_file_path = os.path.join(scripts_dir, "test_generated_suite.py")
        report_file_path = os.path.join(reports_dir, "playwright_report.html")

        # 1. Retrieve Locators Context (Verified KB + Live DOM)
        print("\n--- [Self-Healing Script Tool] Fetching latest application locators ---")
        try:
            locators_context = get_application_locators_tool.invoke({"query_or_url": target_url})
        except Exception as e:
            locators_context = f"Locator extraction fallback ({e})"

        # 2. Initial Test Script Generation
        print("--- [Self-Healing Script Tool] Generating initial Playwright Python test script ---")
        prompt = (
            f"Jira Story: {story_summary}\n"
            f"Target URL: {target_url}\n"
            f"Test Cases:\n{testcases_json}\n\n"
            f"Latest Locators Context:\n{locators_context}\n\n"
            "Generate the complete, robust Playwright Python test script."
        )

        agent_res = testscript_generator_agent.invoke({"messages": [("user", prompt)]})
        last_msg = agent_res.get("messages", [])[-1]
        raw_code = getattr(last_msg, "content", "") if hasattr(last_msg, "content") else str(last_msg)
        current_script = _extract_python_code(raw_code)

        # 3. Execution and Self-Healing Loop
        rounds = 0
        healing_history = []
        is_passed = False
        last_exec_result = {}

        while rounds < max_retries:
            rounds += 1
            print(f"--- [Self-Healing Script Tool] Executing test script (Round {rounds}/{max_retries}) ---")

            with open(script_file_path, "w", encoding="utf-8") as f:
                f.write(current_script)

            exec_result = self._execute_script(script_file_path)
            last_exec_result = exec_result

            if exec_result["passed"]:
                print(f"[PASSED] Test script executed successfully in Round {rounds}!")
                is_passed = True
                healing_history.append({"round": rounds, "status": "PASSED", "error": None})
                break
            else:
                err_snippet = (exec_result["stderr"] or exec_result["stdout"] or "Unknown error").strip()
                print(f"[FAILED] Test script execution failed in Round {rounds}:")
                safe_snippet = err_snippet[:300].encode("ascii", errors="replace").decode("ascii")
                print(f"{safe_snippet}...")
                healing_history.append({"round": rounds, "status": "FAILED", "error": err_snippet})

                if rounds >= max_retries:
                    print("Reached maximum self-healing retry limit.")
                    break

                # Self-healing request to agent
                print(f"[HEALING] Triggering Self-Healing for Round {rounds + 1}...")
                heal_prompt = (
                    f"The previously generated Playwright script failed execution with the following error:\n\n"
                    f"=== SCRIPT ===\n{current_script}\n\n"
                    f"=== EXECUTION ERROR ===\n{err_snippet}\n\n"
                    f"=== LOCATORS CONTEXT ===\n{locators_context}\n\n"
                    "Analyze the error traceback (e.g. timeout, missing selector, assertion error). "
                    "Self-heal the script by updating the selectors, wait strategies, or assertions so it passes. "
                    "Return ONLY the updated executable Python script inside ```python ```."
                )

                heal_res = testscript_generator_agent.invoke({"messages": [("user", heal_prompt)]})
                h_msg = heal_res.get("messages", [])[-1]
                h_code = getattr(h_msg, "content", "") if hasattr(h_msg, "content") else str(h_msg)
                current_script = _extract_python_code(h_code)

        # Final write of script
        with open(script_file_path, "w", encoding="utf-8") as f:
            f.write(current_script)

        # 4. Generate HTML Report with Videos
        final_status = "PASSED" if is_passed else "FAILED_AFTER_RETRIES"
        try:
            _generate_playwright_html_report(
                report_path=report_file_path,
                story_summary=story_summary,
                status=final_status,
                rounds=rounds,
                self_healed=is_passed and rounds > 1,
                stdout=last_exec_result.get("stdout", ""),
                stderr=last_exec_result.get("stderr", ""),
                script_code=current_script,
                videos_dir=videos_dir
            )
        except Exception as e:
            print(f"Warning: Failed to generate HTML report: {e}")

        # 5. Optional Pytest HTML Report run
        try:
            pytest_report_path = os.path.join(reports_dir, "pytest_report.html")
            subprocess.run(
                [sys.executable, "-m", "pytest", script_file_path, f"--html={pytest_report_path}", "--self-contained-html"],
                capture_output=True,
                text=True,
                timeout=45
            )
            print(f"[REPORT] Pytest HTML report generated at: {pytest_report_path}")
        except Exception:
            pass

        output_payload = {
            "status": final_status,
            "rounds": rounds,
            "self_healed": is_passed and rounds > 1,
            "script_file": script_file_path,
            "report_file": report_file_path,
            "videos_dir": videos_dir,
            "healing_history": healing_history,
            "last_stdout": last_exec_result.get("stdout", ""),
            "last_stderr": last_exec_result.get("stderr", ""),
            "code": current_script
        }

        return json.dumps(output_payload, indent=2)
