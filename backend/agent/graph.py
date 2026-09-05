import logging
from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState
from backend.agent.nodes import (
    planner_node,
    router_node,
    tool_selector_node,
    tool_executor_node,
    reflection_node,
    finalizer_node
)

logger = logging.getLogger("agent_graph")

def create_agent_graph():
    """
    Constructs the central LangGraph orchestrator graph:
    Planner -> Router -> Tool Selector -> Tool Executor -> Reflection -> Finalizer -> END
    """
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("router", router_node)
    workflow.add_node("tool_selector", tool_selector_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("finalizer", finalizer_node)

    # Set Entry Point
    workflow.set_entry_point("planner")

    # Define Linear / Conditional Flow Edges
    workflow.add_edge("planner", "router")
    workflow.add_edge("router", "tool_selector")
    workflow.add_edge("tool_selector", "tool_executor")
    workflow.add_edge("tool_executor", "reflection")
    workflow.add_edge("reflection", "finalizer")
    workflow.add_edge("finalizer", END)

    return workflow.compile()

# Singleton compiled agent graph instance
agent_executor = create_agent_graph()

import json
from backend.agent.nodes import stream_local_llm

async def stream_agent(user_query: str, uploaded_file: str | None = None):
    """
    Asynchronous generator yielding real-time SSE events:
    - plan: strategy and execution steps
    - router: selected model, task classification, and rationale
    - rag: retrieved context chunks from local knowledge base
    - ocr: multimodal inspection extracted tags/tables (if file uploaded)
    - tool_start: tool execution initiated (with code if python sandbox)
    - tool_output: tool execution telemetry / stdout
    - reflection: compliance & deliverable validation
    - token: real-time streaming LLM response tokens
    - deliverables: generated file links (.docx, .xlsx, .pptx, .py)
    - done: final state & audit summary
    """
    state: AgentState = {
        "user_query": user_query,
        "uploaded_file": uploaded_file,
        "task_type": "general",
        "selected_model": "qwen2.5:7b-instruct",
        "routing_reason": "",
        "context": [],
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "generated_files": [],
        "audit_log": []
    }

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    # 1. PLANNER
    state = await planner_node(state)
    yield sse("plan", {
        "step": "Planner",
        "details": state["audit_log"][-1]["details"] if state["audit_log"] else "Plan formulated",
        "timestamp": state["audit_log"][-1]["timestamp"] if state["audit_log"] else ""
    })

    # 2. ROUTER
    state = await router_node(state)
    yield sse("router", {
        "step": "Router",
        "model": state["selected_model"],
        "task": state["task_type"],
        "reason": state["routing_reason"],
        "timestamp": state["audit_log"][-1]["timestamp"] if state["audit_log"] else ""
    })

    # 3. TOOL SELECTOR & RAG
    state = await tool_selector_node(state)
    if state.get("context"):
        yield sse("rag", {
            "step": "RAG",
            "sources": state["context"][:3],
            "count": len(state["context"])
        })

    # 4. TOOL EXECUTOR (with live tool_start and tool_output events)
    for call in state.get("tool_calls", []):
        tname = call["tool"]
        targs = call.get("args", {})
        code_content = targs.get("code") if tname == "run_code" else None
        
        yield sse("tool_start", {
            "tool": tname,
            "args": targs,
            "code": code_content,
            "description": f"Executing {tname}..."
        })

    state = await tool_executor_node(state)

    for res in state.get("tool_results", []):
        tname = res.get("tool")
        tresult = res.get("result", {})
        stdout_txt = tresult.get("stdout") if isinstance(tresult, dict) else None
        
        yield sse("tool_output", {
            "tool": tname,
            "result": tresult,
            "stdout": stdout_txt,
            "success": "error" not in res
        })

    # 5. REFLECTION
    state = await reflection_node(state)
    yield sse("reflection", {
        "step": "Reflection",
        "details": state["audit_log"][-1]["details"] if state["audit_log"] else "Reflection complete",
        "files": state.get("generated_files", [])
    })

    # 6. STREAMING LLM ANSWER
    accumulated_answer = []
    yield sse("thought_start", {"message": "Synthesizing answer from grounded context & tool outputs..."})
    
    async for token in stream_local_llm(
        user_query=user_query,
        selected_model=state["selected_model"],
        task_type=state["task_type"],
        context=state["context"],
        tool_results=state["tool_results"],
        uploaded_file=uploaded_file
    ):
        accumulated_answer.append(token)
        yield sse("token", {"delta": token})

    llm_full_text = "".join(accumulated_answer)

    # 7. DELIVERABLES
    from backend.config import OUTPUTS_DIR
    deliverable_objects = []
    for fname in state.get("generated_files", []):
        fpath = OUTPUTS_DIR / fname
        fsize = fpath.stat().st_size if fpath.exists() else 0
        ext = fname.split(".")[-1].lower() if "." in fname else "file"
        deliverable_objects.append({
            "name": fname,
            "type": ext,
            "size": fsize,
            "path": f"data/outputs/{fname}"
        })

    if deliverable_objects:
        yield sse("deliverables", {"files": deliverable_objects})

    # 8. DONE
    # Assemble full state final response
    state = await finalizer_node(state)
    state["final_response"] = llm_full_text or state["final_response"]
    yield sse("done", {
        "final_response": state["final_response"],
        "selected_model": state["selected_model"],
        "task_type": state["task_type"],
        "generated_files": deliverable_objects,
        "audit_log": state["audit_log"]
    })


async def run_agent(user_query: str, uploaded_file: str | None = None) -> AgentState:
    """
    Helper function to initialize AgentState and run the LangGraph agent graph synchronously.
    """
    initial_state: AgentState = {
        "user_query": user_query,
        "uploaded_file": uploaded_file,
        "task_type": "general",
        "selected_model": "qwen2.5:7b-instruct",
        "routing_reason": "",
        "context": [],
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "generated_files": [],
        "audit_log": []
    }

    final_state = await agent_executor.ainvoke(initial_state)
    return final_state
