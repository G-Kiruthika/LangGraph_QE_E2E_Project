import json
import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# Import our local agents
from src.agents.testcases_generator_agent import testcases_generator_agent
from src.agents.testcase_reviewer_agent import testcase_reviewer_agent
from src.tools.rag_tools import orangehrmDomain_kb_tool

logger = logging.getLogger(__name__)

def _strip_fences(text):
    if not text:
        return text
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

class TestCasesSelfHealingGeneratorSchema(BaseModel):
    storysummary: str = Field(..., description="Jira story summary")
    storydescription: str = Field("", description="Jira story description")
    scenarios: str = Field("", description="JSON string of generated test scenarios")
    epiccontext: str = Field("", description="Epic summary + description")
    preconditions: str = Field("", description="Extracted preconditions")
    threshold: int = Field(85, description="Minimum reviewer confidence (0-100) required to stop the loop")
    max_regen: int = Field(3, description="Circuit-breaker: maximum generate-review rounds")

class TestCasesSelfHealingGeneratorToolV1(BaseTool):
    name: str = "TestCasesSelfHealingGeneratorToolV1"
    description: str = (
        "Self-healing test cases generation for a Jira story and its scenarios. Runs a Generator and an "
        "independent Reviewer agent in a loop until confidence score is >= threshold."
    )
    args_schema: Type[BaseModel] = TestCasesSelfHealingGeneratorSchema

    def _run(self, **kwargs) -> str:
        a = kwargs.get("kwargs", kwargs) or kwargs
        story_summary = (a.get("storysummary") or "").strip()
        if not story_summary:
            return json.dumps({"status": "error", "error": "storysummary is required"})

        story_description = a.get("storydescription") or ""
        scenarios = a.get("scenarios") or ""
        epic_context = a.get("epiccontext") or ""
        preconditions = a.get("preconditions") or ""
        threshold = int(a.get("threshold", 85))
        max_regen = max(1, int(a.get("max_regen", 3)))
        
        # 0. Fetch KB context
        try:
            kb_context = orangehrmDomain_kb_tool.invoke({"query": story_summary})
        except Exception as e:
            logger.warning(f"Failed to fetch KB context: {e}")
            kb_context = "No KB context available."

        feedback = ""
        best = None
        trajectory = []

        for round_num in range(1, max_regen + 1):
            # 1. GENERATE TESTCASES
            gen_payload_str = (
                f"Summary: {story_summary}\n"
                f"Description: {story_description}\n"
                f"Scenarios:\n{scenarios}\n"
                f"Epic: {epic_context}\n"
                f"Preconditions: {preconditions}\n"
                f"Knowledge Base Context:\n{kb_context}\n"
            )
            if feedback:
                gen_payload_str += f"\nReviewer Feedback from last round: {feedback}. Please fix these issues exactly."

            try:
                gen_result = testcases_generator_agent.invoke({"messages": [("user", gen_payload_str)]})
                
                messages = gen_result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        testcases_json = json.dumps(last_msg.tool_calls[0].get("args", {}))
                    else:
                        raw_testcases = last_msg.content
                        if isinstance(raw_testcases, str):
                            testcases_json = raw_testcases
                        elif isinstance(raw_testcases, list):
                            parts = []
                            for item in raw_testcases:
                                if isinstance(item, str):
                                    parts.append(item)
                                elif isinstance(item, dict) and "text" in item:
                                    parts.append(item["text"])
                                elif isinstance(item, dict):
                                    parts.append(json.dumps(item))
                                else:
                                    parts.append(str(item))
                            testcases_json = "\n".join(parts)
                        elif isinstance(raw_testcases, dict):
                            testcases_json = json.dumps(raw_testcases)
                        else:
                            testcases_json = str(raw_testcases)
                else:
                    testcases_json = ""
            except Exception as e:
                trajectory.append({"round": round_num, "error": f"generator failed: {str(e)}"})
                break

            # 2. REVIEW TESTCASES
            try:
                review_result = testcase_reviewer_agent.invoke({
                    "story_details": gen_payload_str,
                    "testcases": testcases_json
                })
                
                confidence = review_result.confidence
                curr_feedback = review_result.feedback
                
                review_dict = {
                    "confidence": confidence,
                    "feedback": curr_feedback,
                    "approved": review_result.approved
                }
            except Exception as e:
                trajectory.append({"round": round_num, "error": f"reviewer failed: {str(e)}"})
                break

            if best is None or confidence > best["confidence"]:
                best = {"confidence": confidence, "testcases": testcases_json, "review": review_dict, "round": round_num}

            if confidence >= threshold:
                decision = "STOP threshold-met"
            elif round_num == max_regen:
                decision = "STOP regen-cap"
            else:
                decision = "REGENERATE"

            trajectory.append({"round": round_num, "confidence": confidence, "decision": decision})

            if decision.startswith("STOP"):
                break
            
            feedback = curr_feedback

        if best is None:
            return json.dumps({"status": "error", "error": "no successful round", "trajectory": trajectory})

        try:
            parsed_testcases = json.loads(_strip_fences(best["testcases"]))
            if isinstance(parsed_testcases, dict) and "testcases" in parsed_testcases:
                parsed_testcases = parsed_testcases["testcases"]
        except Exception:
            parsed_testcases = best["testcases"]

        return json.dumps({
            "status": "ok",
            "confidencescore": best["confidence"],
            "threshold": threshold,
            "rounds": best["round"],
            "healingtriggered": best["round"] > 1,
            "testcases": parsed_testcases,
            "reviewerfeedback": best["review"]["feedback"],
            "trajectory": trajectory
        })
