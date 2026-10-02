from src.models.schemas import ScenarioResponse
from typing import TypedDict


class GraphState(TypedDict):
    jira_story: str
    test_scenarios: ScenarioResponse
    testcases: dict
    playwright_code: str