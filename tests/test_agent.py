import pytest
from backend.agent.graph import run_agent

@pytest.mark.asyncio
async def test_agent_graph_execution():
    query = "Run python calculation and generate word doc approval note"
    final_state = await run_agent(user_query=query)

    assert final_state["task_type"] in ["coding", "document_reasoning", "general"]
    assert final_state["selected_model"] is not None
    assert len(final_state["audit_log"]) >= 5
    assert len(final_state["final_response"]) > 0
