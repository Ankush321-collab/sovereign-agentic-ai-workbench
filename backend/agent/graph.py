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

async def run_agent(user_query: str, uploaded_file: str | None = None) -> AgentState:
    """
    Helper function to initialize AgentState and run the LangGraph agent graph.
    """
    initial_state: AgentState = {
        "user_query": user_query,
        "uploaded_file": uploaded_file,
        "task_type": "general",
        "selected_model": "Sarvam-30B",
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
