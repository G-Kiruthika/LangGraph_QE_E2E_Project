from pydantic import BaseModel, Field
from typing import List, Optional

class JiraIssueOutput(BaseModel):
    issue_key: str = Field(description="The issue key identifier, e.g., 'KAN-12'")
    summary: str = Field(description="Brief title or summary of the issue")
    description: str = Field(description="The description of the issue")
    status: str = Field(description="Current status of the issue, e.g., 'In Progress'")
    assignee: Optional[str] = Field(default="Unassigned", description="Assigned user's name")
    
class Scenario(BaseModel):
    """Schema for a test scenario"""
    test_scenario_id: str
    test_scenario_description: str
    expected_results: str
    preconditions: str
    test_data: str
    navigable_path: str
    acceptance_criteria_id: str
    IssueId: str

class ScenarioResponse(BaseModel):
    scenarios: List[Scenario]
    
class TestStep(BaseModel):
    action: str
    data: str
    expected_result: str

class TestCase(BaseModel):
    summary: str
    description: str
    test_type: str = Field(default="Functional", description="e.g. Functional, Non-functional, Negative, Integration")
    scenario_id: str
    steps: List[TestStep]

class TestCaseResponse(BaseModel):
    testcases: List[TestCase]