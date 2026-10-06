import requests
import urllib3
import json
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# Suppress SSL warnings for local execution
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. PYDANTIC BASE MODEL (INPUT SCHEMA)
# ==========================================
class XrayJiraCompleteTraceabilitySchema(BaseModel):
    """Schema defining the required inputs for the Xray Jira Traceability Tool."""
    jira_base_url: str = Field(default="", description="Base URL for Jira instance")
    jira_user: str = Field(default="", description="Jira user email")
    jira_api_token: str = Field(default="", description="Jira API token")
    xray_client_id: str = Field(default="", description="Xray Client ID")
    xray_client_secret: str = Field(default="", description="Xray Client Secret")
    project_key: str = Field(default="", description="Target Jira Project Key")
    story_key: str = Field(default="", description="Target Jira Story Key to link tests to")
    tests_json: str = Field(default="[]", description="JSON string containing multiple test cases")

# ==========================================
# 2. LANGCHAIN BASE TOOL
# ==========================================
class XrayJiraCompleteTraceabilityTool(BaseTool):
    name: str = "XrayJiraCompleteTraceabilityTool"
    description: str = "Creates Cucumber Preconditions, Tests, links them natively, and links to a Jira Story."
    args_schema: Type[BaseModel] = XrayJiraCompleteTraceabilitySchema

    def get_xray_token(self, client_id: str, client_secret: str) -> str:
        """Authenticates with Xray API using provided client credentials."""
        url = "https://eu.xray.cloud.getxray.app/api/v2/authenticate"
        resp = requests.post(
            url,
            json={"client_id": client_id, "client_secret": client_secret},
            verify=False
        )
        return resp.text.strip('"')

    def link_work_item(self, jira_base_url: str, source_key: str, target_key: str, jira_auth: tuple, link_type: str = "Relates") -> str:
        """Natively links two Jira issues together so they appear in the 'Linked work items' UI."""
        link_url = f"{jira_base_url}/rest/api/2/issueLink"
        link_payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": source_key},
            "outwardIssue": {"key": target_key}
        }
        res = requests.post(link_url, json=link_payload, auth=jira_auth, verify=False)
        if res.status_code == 201:
            return f"SUCCESS: Linked work item: {source_key} -> {target_key}"
        else:
            return f"WARNING: Work item link failed: {res.text}"

    def _run(self, jira_base_url: str, jira_user: str, jira_api_token: str,
             xray_client_id: str, xray_client_secret: str,
             project_key: str, story_key: str, tests_json: str, **kwargs) -> str:
        try:
            xray_token = self.get_xray_token(xray_client_id, xray_client_secret)
            gql_url = "https://eu.xray.cloud.getxray.app/api/v2/graphql"
            headers = {"Authorization": f"Bearer {xray_token}", "Content-Type": "application/json"}
            jira_auth = (jira_user, jira_api_token)
            tests = json.loads(tests_json)
            results = []
            
            for test in tests:
                # ---------------------------------------------------------
                # DATA PRESERVATION AND PARSING
                # ---------------------------------------------------------
                raw_summary = test.get("summary", "Untitled Test")
                raw_desc = test.get("description", "")
                
                # Format the steps into a markdown string to append to description
                steps = test.get("steps", [])
                steps_md = "\n\n**Test Steps:**\n"
                if steps:
                    steps_md += "| Step | Action | Data | Expected Result |\n|---|---|---|---|\n"
                    for idx, step in enumerate(steps):
                        action = step.get("action", "").replace("\n", " ")
                        data = step.get("data", "").replace("\n", " ")
                        expected_result = step.get("expected_result", "").replace("\n", " ")
                        steps_md += f"| {idx+1} | {action} | {data} | {expected_result} |\n"
                
                test_desc = raw_desc + steps_md
                
                # ==========================================
                # 1. CREATE TEST ISSUE (GraphQL)
                # ==========================================
                test_mutation = """
                mutation CreateTestIssue($projectKey: String!, $summary: String!, $desc: String!) {
                    createTest(
                        testType: { name: "Manual" },
                        jira: { fields: { project: { key: $projectKey }, summary: $summary, description: $desc } }
                    ) {
                        test { jira(fields: ["key", "id"]) }
                    }
                }
                """
                t_vars = {
                    "projectKey": project_key,
                    "summary": raw_summary,
                    "desc": test_desc
                }
                t_resp = requests.post(gql_url, json={"query": test_mutation, "variables": t_vars}, headers=headers, verify=False)
                if t_resp.status_code != 200:
                    results.append(f"ERROR: HTTP {t_resp.status_code} creating Test: {t_resp.text}")
                    continue
                try:
                    t_json = t_resp.json()
                except Exception:
                    results.append(f"ERROR: Failed to parse JSON from Xray. Response: {t_resp.text}")
                    continue
                
                if "errors" in t_json:
                    results.append(f"ERROR: Error creating Test: {json.dumps(t_json['errors'])}")
                    continue
                    
                t_data = t_json["data"]["createTest"]["test"]["jira"]
                test_key = t_data["key"]
                test_id = t_data["id"]
                
                # ==========================================
                # 2. LINK USER STORY TO TESTS (Jira Native REST)
                # ==========================================
                link_url = f"{jira_base_url}/rest/api/2/issueLink"
                link_payload = {
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": test_key},
                    "outwardIssue": {"key": story_key}
                }
                link_res = requests.post(link_url, json=link_payload, auth=jira_auth, verify=False)
                if link_res.status_code == 201:
                    results.append(f"SUCCESS: Created Test {test_key}. Linked successfully to Story {story_key}.")
                else:
                    results.append(f"SUCCESS: Created Test {test_key}, but Story Link failed: {link_res.text}")
                    
            return "\n".join(results)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"ERROR: System Error: {str(e)}"
