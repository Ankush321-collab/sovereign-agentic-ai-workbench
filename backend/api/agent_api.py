from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from backend.agent.graph import run_agent

router = APIRouter(tags=["Agent"])

class AgentRunRequest(BaseModel):
    """Unified request that accepts both old ChatRequest format and new workflow format."""
    # Old format (from Chat.jsx)
    message: Optional[str] = None
    file_id: Optional[str] = None
    # New format (from api.js runAgentWorkflow)
    query: Optional[str] = None
    ocr_readings: Optional[List[Any]] = None

# Global audit trace store for status inspection
LATEST_AGENT_STATE = {}

@router.post("/agent/run")
async def run_agent_endpoint(request: AgentRunRequest):
    """
    Direct Agent Run Endpoint.
    Runs the full PLAN -> POLICY GATE -> TOOLS -> CRITIQUE -> FINALIZER pipeline.
    Accepts both {message, file_id} and {query, ocr_readings} formats.
    """
    global LATEST_AGENT_STATE
    # Normalize: prefer 'query' field, fallback to 'message'
    user_query = request.query or request.message or ""
    uploaded_file = request.file_id or None

    if not user_query:
        raise HTTPException(status_code=400, detail="Either 'query' or 'message' field required")

    try:
        final_state = await run_agent(
            user_query=user_query,
            uploaded_file=uploaded_file
        )
        LATEST_AGENT_STATE = final_state
        return final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/status")
async def get_agent_status_endpoint():
    """Gets the current agent status and audit execution trace."""
    return {
        "status": "active" if LATEST_AGENT_STATE else "idle",
        "last_task": LATEST_AGENT_STATE.get("user_query", "None"),
        "selected_model": LATEST_AGENT_STATE.get("selected_model", "None"),
        "audit_trace": LATEST_AGENT_STATE.get("audit_log", [])
    }
