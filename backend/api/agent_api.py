from fastapi import APIRouter, HTTPException
from backend.agent.state import ChatRequest
from backend.agent.graph import run_agent

router = APIRouter(tags=["Agent"])

# Global audit trace store for status inspection
LATEST_AGENT_STATE = {}

@router.post("/agent/run")
async def run_agent_endpoint(request: ChatRequest):
    """
    Direct Agent Run Endpoint.
    Runs the agent and returns complete AgentState including state variables and trace log.
    """
    global LATEST_AGENT_STATE
    try:
        final_state = await run_agent(
            user_query=request.message,
            uploaded_file=request.file_id
        )
        LATEST_AGENT_STATE = final_state
        return final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/status")
async def get_agent_status_endpoint():
    """
    Gets the current agent status and audit execution trace.
    """
    return {
        "status": "active" if LATEST_AGENT_STATE else "idle",
        "last_task": LATEST_AGENT_STATE.get("user_query", "None"),
        "selected_model": LATEST_AGENT_STATE.get("selected_model", "None"),
        "audit_trace": LATEST_AGENT_STATE.get("audit_log", [])
    }
