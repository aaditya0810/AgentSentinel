import os
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from .auditor import evaluate_reasoning_mock

app = FastAPI(
    title="AgentSentinel - Intercept Layer",
    description="Governance and Control Plane for AI Agents",
    version="1.0.0"
)

# Load policies
POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "policies.yaml")
with open(POLICY_PATH, "r") as f:
    POLICIES = yaml.safe_load(f)

# Models for the Intercept Layer
class ToolCallRequest(BaseModel):
    agent_id: str
    role: str
    tool_name: str
    tool_args: Dict[str, Any]
    reasoning: Optional[str] = None
    auditor_model: Optional[str] = "GPT-4o"

class ToolCallResponse(BaseModel):
    status: str
    message: str
    action_allowed: bool
    hallucination_score: Optional[float] = None

def evaluate_policy(request: ToolCallRequest) -> None:
    """
    Enforces hard constraints based on the policies.yaml file.
    """
    role_policies = POLICIES.get("roles", {}).get(request.role)
    
    if not role_policies:
        raise HTTPException(status_code=403, detail=f"Role '{request.role}' not found in policies.")
        
    if request.tool_name in role_policies.get("blocked_actions", []):
         raise HTTPException(status_code=403, detail=f"Action '{request.tool_name}' is expressly blocked by policy for role '{request.role}'.")
         
    if request.tool_name not in role_policies.get("allowed_actions", []):
         raise HTTPException(status_code=403, detail=f"Action '{request.tool_name}' is not permitted. Only explicitly allowed actions are permitted.")

    # Time of day checking (simplified for MVP)
    # Budget tracking could also be integrated here.

@app.post("/api/v1/intercept", response_model=ToolCallResponse)
async def intercept_tool_call(request: ToolCallRequest):
    """
    The Intercept Layer gateway for all Agent Tool Calls.
    """
    # 1. Policy Engine Evaluation (Hard Constraints)
    try:
        evaluate_policy(request)
    except HTTPException as e:
        return ToolCallResponse(
            status="blocked",
            message=e.detail,
            action_allowed=False
        )

    # 2. Sent to Reasoning Auditor (Secondary LLM Mock)
    auditor_threshold = POLICIES.get("auditor_settings", {}).get("hallucination_threshold", 0.8)
    
    auditor_response = evaluate_reasoning_mock(
        role=request.role,
        tool_name=request.tool_name,
        tool_args=request.tool_args,
        reasoning=request.reasoning or "",
        threshold=auditor_threshold,
        auditor_model=request.auditor_model or "GPT-4o"
    )
    
    if not auditor_response["approved"]:
        return ToolCallResponse(
            status="blocked_by_auditor",
            message=f"Reasoning Audit Failed. Reason: {auditor_response['reasoning']}",
            action_allowed=False,
            hallucination_score=auditor_response["hallucination_score"]
        )
    
    return ToolCallResponse(
        status="approved",
        message=f"Tool call passed Policy Engine and Auditor. Auditor note: {auditor_response['reasoning']}",
        action_allowed=True,
        hallucination_score=auditor_response["hallucination_score"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
