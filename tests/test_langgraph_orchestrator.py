import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_router_classifies_portfolio_query():
    from agents.langgraph_orchestrator import _classify_agents

    agents = _classify_agents("What is my portfolio allocation and holdings?")
    assert "portfolio" in agents
    assert "risk" not in agents
    assert "goals" not in agents


def test_router_classifies_mixed_query():
    from agents.langgraph_orchestrator import _classify_agents

    agents = _classify_agents("How is my risk exposure affecting my retirement goal?")
    assert "risk" in agents
    assert "goals" in agents


def test_router_falls_back_to_all_agents_for_generic_query():
    from agents.langgraph_orchestrator import _classify_agents

    agents = _classify_agents("How am I doing?")
    assert set(agents) == {"portfolio", "risk", "goals"}


@pytest.mark.asyncio
async def test_langgraph_orchestrator_routes_and_synthesizes():
    from agents.langgraph_orchestrator import run_langgraph_orchestrator

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Your portfolio looks healthy.")]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with (
        patch("agents.langgraph_orchestrator.get_client", return_value=mock_client),
        patch("agents.portfolio_agent.get_client", return_value=AsyncMock(
            messages=AsyncMock(create=AsyncMock(return_value=mock_response))
        )),
        patch("agents.risk_agent.get_client", return_value=AsyncMock(
            messages=AsyncMock(create=AsyncMock(return_value=mock_response))
        )),
        patch("agents.goals_agent.get_client", return_value=AsyncMock(
            messages=AsyncMock(create=AsyncMock(return_value=mock_response))
        )),
        patch("agents.langgraph_orchestrator.hybrid_search", return_value=[]),
    ):
        result = await run_langgraph_orchestrator(
            "How is my portfolio allocation?",
            [],
            "user1",
        )

    assert isinstance(result, str)
    assert len(result) > 0
