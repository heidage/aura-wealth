"""
Tests for the agentic workflow pipeline.
Client queries now route through LangGraph orchestrator with dynamic agent selection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_mock_response(text: str):
    r = MagicMock()
    r.content = [MagicMock(text=text)]
    return r


def _mock_client(text: str):
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=make_mock_response(text))
    return client


@pytest.fixture
def mock_all_clients():
    with (
        patch("agents.portfolio_agent.get_client", return_value=_mock_client("Portfolio: 60% equity, 40% cash.")),
        patch("agents.risk_agent.get_client", return_value=_mock_client("Risk score: 6/10. High cash drag.")),
        patch("agents.goals_agent.get_client", return_value=_mock_client("Retirement on track.")),
        patch("agents.langgraph_orchestrator.get_client", return_value=_mock_client("Your portfolio is solid.")),
        patch("agents.langgraph_orchestrator.hybrid_search", return_value=[]),
    ):
        yield


@pytest.mark.asyncio
async def test_generic_query_calls_all_three_agents(mock_all_clients):
    """Generic query (no keywords) → router dispatches all three expert agents."""
    from agents.orchestrator import run_orchestrator

    with (
        patch("agents.portfolio_agent.get_client", return_value=_mock_client("Portfolio: 60% equity.")) as p_mock,
        patch("agents.risk_agent.get_client", return_value=_mock_client("Risk: moderate.")) as r_mock,
        patch("agents.goals_agent.get_client", return_value=_mock_client("Goals on track.")) as g_mock,
        patch("agents.langgraph_orchestrator.get_client", return_value=_mock_client("Summary.")),
        patch("agents.langgraph_orchestrator.hybrid_search", return_value=[]),
    ):
        await run_orchestrator("How am I doing overall?", [], "user_client_1", "client")
        assert p_mock.return_value.messages.create.called
        assert r_mock.return_value.messages.create.called
        assert g_mock.return_value.messages.create.called


@pytest.mark.asyncio
async def test_risk_agent_receives_portfolio_output():
    """Risk node receives portfolio_output from state when both agents are active."""
    from agents.langgraph_orchestrator import WealthState, portfolio_node, risk_node

    state: WealthState = {
        "query": "What is my risk exposure on my portfolio?",
        "history": [],
        "user_id": "user_client_1",
        "active_agents": ["portfolio", "risk"],
        "portfolio_output": "",
        "risk_output": "",
        "goals_output": "",
        "rag_context": "",
        "response": "",
    }

    portfolio_text = "Portfolio: 60% equity, 40% cash."
    risk_text = "Risk score: 6/10."

    with (
        patch("agents.portfolio_agent.get_client", return_value=_mock_client(portfolio_text)),
        patch("agents.risk_agent.get_client", return_value=_mock_client(risk_text)),
    ):
        state.update(await portfolio_node(state))
        assert state["portfolio_output"] == portfolio_text

        state.update(await risk_node(state))
        assert state["risk_output"] == risk_text


@pytest.mark.asyncio
async def test_goals_agent_receives_prior_outputs():
    """Goals node receives both portfolio and risk outputs via LangGraph state."""
    from agents.langgraph_orchestrator import WealthState, goals_node

    portfolio_text = "Portfolio: 60% equity, 40% cash."
    risk_text = "Risk score: 6/10. High cash drag."
    goals_text = "Retirement on track."

    state: WealthState = {
        "query": "Am I on track for retirement?",
        "history": [],
        "user_id": "user_client_1",
        "active_agents": ["portfolio", "risk", "goals"],
        "portfolio_output": portfolio_text,
        "risk_output": risk_text,
        "goals_output": "",
        "rag_context": "",
        "response": "",
    }

    with patch("agents.goals_agent.get_client", return_value=_mock_client(goals_text)):
        result = await goals_node(state)

    assert result["goals_output"] == goals_text
