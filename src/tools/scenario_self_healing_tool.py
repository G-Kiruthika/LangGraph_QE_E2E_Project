import json
import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# Import our local agents
from src.agents.scenario_generator_agent import scenario_generator_agent
from src.agents.scenario_reviewer_agent import scenario_reviewer_agent
from src.tools.rag_tools import orangehrmDomain_kb_tool

logger = logging.getLogger(__name__)

def _strip_fences(text):
    if not text:
        return text
    # Very basic fence stripper, you can expand if needed
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

_NL_MARKER = "[[NL]]"

def _flatten_multiline(text):
    if not text:
        return text
    return text.replace("\r\n", "\n").replace("\n", _NL_MARKER)

class ScenarioSelfHealingGeneratorSchema(BaseModel):
    storysummary: str = Field(..., description="Jira story summary")
    storydescription: str = Field("", description="Jira story description")
    epiccontext: str = Field("", description="Epic summary + description")
    preconditions: str = Field("", description="Extracted preconditions")
    threshold: int = Field(85, description="Minimum reviewer confidence (0-100) required to stop the loop")
    max_regen: int = Field(3, description="Circuit-breaker: maximum generate-review rounds")

class ScenarioSelfHealingGeneratorToolV1(BaseTool):
    name: str = "ScenarioSelfHealingGeneratorToolV1"
    description: str = (
        "Self-healing scenario-list generation for a Jira story. Runs a Generator and an "
        "independent Reviewer agent in a loop until confidence score is >= threshold."
    )
    args_schema: Type[BaseModel] = ScenarioSelfHealingGeneratorSchema

    def _run(self, **kwargs) -> str:
        a = kwargs.get("kwargs", kwargs) or kwargs
        story_summary = (a.get("storysummary") or "").strip()
        if not story_summary:
            return json.dumps({"status": "error", "error": "storysummary is required"})

        story_description = a.get("storydescription") or ""
        epic_context = a.get("epiccontext") or ""
        preconditions = a.get("preconditions") or ""
        threshold = int(a.get("threshold", 85))
        max_regen = max(1, int(a.get("max_regen", 3)))
        
        # 0. Fetch KB context
        try:
            print("\n[DEBUG] TOOL IS SEARCHING KNOWLEDGE BASE DIRECTLY...")
            kb_context = orangehrmDomain_kb_tool.invoke({"query": story_summary})
            print(f"\n=================== RAG CONTEXT RETRIEVED ===================")
            print(kb_context)
            print(f"=============================================================\n")
        except Exception as e:
            logger.warning(f"Failed to fetch KB context: {e}")
            kb_context = "No KB context available."

        feedback = ""
        best = None
        trajectory = []

        for round_num in range(1, max_regen + 1):
            # 1. GENERATE SCENARIOS (using local agent)
            gen_payload_str = (
                f"Summary: {story_summary}\n"
                f"Description: {story_description}\n"
                f"Epic: {epic_context}\n"
                f"Preconditions: {preconditions}\n"
                f"Knowledge Base Context:\n{kb_context}\n"
            )
            if feedback:
                gen_payload_str += f"\nReviewer Feedback from last round: {feedback}. Please fix these issues exactly."

            try:
                # Invoke generator agent
                # Note: scenario_generator_agent is now a create_react_agent, so it needs messages
                gen_result = scenario_generator_agent.invoke({"messages": [("user", gen_payload_str)]})
                
                # We need it as a JSON string to pass it around
                messages = gen_result.get("messages", [])
                if messages:
                    raw_scenarios = messages[-1].content
                    if isinstance(raw_scenarios, str):
                        scenarios_json = raw_scenarios
                    elif isinstance(raw_scenarios, list):
                        parts = []
                        for item in raw_scenarios:
                            if isinstance(item, str):
                                parts.append(item)
                            elif isinstance(item, dict) and "text" in item:
                                parts.append(item["text"])
                            elif isinstance(item, dict):
                                parts.append(json.dumps(item))
                            else:
                                parts.append(str(item))
                        scenarios_json = "\n".join(parts)
                    elif isinstance(raw_scenarios, dict):
                        scenarios_json = json.dumps(raw_scenarios)
                    else:
                        scenarios_json = str(raw_scenarios)
                else:
                    scenarios_json = ""
            except Exception as e:
                trajectory.append({"round": round_num, "error": f"generator failed: {str(e)}"})
                break

            # 2. REVIEW SCENARIOS (using local agent)
            try:
                # The reviewer agent returns a Pydantic 'ReviewResponse' object
                review_result = scenario_reviewer_agent.invoke({
                    "story_details": gen_payload_str,
                    "scenarios": scenarios_json
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
                best = {"confidence": confidence, "scenarios": scenarios_json, "review": review_dict, "round": round_num}

            if confidence >= threshold:
                decision = "STOP threshold-met"
            elif round_num == max_regen:
                decision = "STOP regen-cap"
            else:
                decision = "REGENERATE"

            trajectory.append({"round": round_num, "confidence": confidence, "decision": decision})

            if decision.startswith("STOP"):
                break
            
            # Feed this back into the next loop
            feedback = curr_feedback

        if best is None:
            return json.dumps({"status": "error", "error": "no successful round", "trajectory": trajectory})

        return json.dumps({
            "status": "ok",
            "confidencescore": best["confidence"],
            "threshold": threshold,
            "rounds": best["round"],
            "healingtriggered": best["round"] > 1,
            "scenarios": _flatten_multiline(best["scenarios"]),
            "reviewerfeedback": best["review"]["feedback"],
            "trajectory": trajectory
        })
