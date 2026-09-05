from fastapi import APIRouter, HTTPException
from backend.agent.state import ChatRequest, ChatResponse
from backend.agent.graph import run_agent

router = APIRouter(tags=["Chat"])

@router.post("/api/chat", response_model=ChatResponse)
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat API Endpoint.
    Invokes the LangGraph Agent to route, retrieve, plan, execute tools, and respond.
    """
    try:
        final_state = await run_agent(
            user_query=request.message,
            uploaded_file=request.file_id
        )

        return ChatResponse(
            response=final_state.get("final_response", ""),
            task_type=final_state.get("task_type", "general"),
            model=final_state.get("selected_model", "Sarvam-30B"),
            routing_reason=final_state.get("routing_reason", ""),
            sources=final_state.get("context", []),
            files=final_state.get("generated_files", []),
            trace=final_state.get("audit_log", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")
