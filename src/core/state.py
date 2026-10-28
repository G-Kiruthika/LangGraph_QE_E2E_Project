from src.models.schemas import ScenarioResponse
from typing import TypedDict, List, Dict, Any


class GraphState(TypedDict, total=False):
    issue_key: str
    jira_story: str
    test_scenarios: ScenarioResponse
    testcases: dict
    playwright_code: str
    generated_test_scripts: List[Dict[str, Any]]
    error: str
