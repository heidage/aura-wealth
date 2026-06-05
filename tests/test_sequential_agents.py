import pytest
from unittest.mock import AsyncMock, patch, call


def make_mock_response(text: str):
    from unittest.mock import MagicMock
    r = MagicMock()
    r.content = [MagicMock(text=text)]
    return r


@pytest.fixture
def mock_anthropic_clients():
    """Patch all three agent clients + orchestrator client."""
    with (
        patch("agents.portfolio_agent.get_client") as p,
        patch("agents.risk_agent.get_client") as r,
        patch("agents.goals_agent.get_client") as g,
        patch("agents.orchestrator.get_client") as o,
    ):
        p.return_value.messages.create = AsyncMock(return_value=make_mock_response("Portfolio: 60% equity, 40% cash."))
        r.return_value.messages.create = AsyncMock(return_value=make_mock_response("Risk score: 6/10. High cash drag."))
        g.return_value.messages.create = AsyncMock(return_value=make_mock_response("Retirement on track. House goal needs more contribution."))
        o.return_value.messages.create = AsyncMock(return_value=make_mock_response("Your portfolio is solid but consider deploying cash."))
        yield {"portfolio": p, "risk": r, "goals": g, "orchestrator": o}


@pytest.mark.asyncio
async def test_sequential_workflow_calls_all_three_agents(mock_anthropic_clients):
    from agents.orchestrator import run_orchestrator

    await run_orchestrator("How is my portfolio?", [], "user_client_1", "client")

    assert mock_anthropic_clients["portfolio"].return_value.messages.create.called
    assert mock_anthropic_clients["risk"].return_value.messages.create.called
    assert mock_anthropic_clients["goals"].return_value.messages.create.called


@pytest.mark.asyncio
async def test_risk_agent_receives_portfolio_output(mock_anthropic_clients):
    from agents.orchestrator import run_orchestrator

    await run_orchestrator("Assess my risk", [], "user_client_1", "client")

    risk_call_args = mock_anthropic_clients["risk"].return_value.messages.create.call_args
    messages = risk_call_args.kwargs["messages"]
    combined_content = " ".join(m["content"] for m in messages)
    assert "Portfolio: 60% equity, 40% cash." in combined_content


@pytest.mark.asyncio
async def test_goals_agent_receives_both_prior_outputs(mock_anthropic_clients):
    from agents.orchestrator import run_orchestrator

    await run_orchestrator("Am I on track for retirement?", [], "user_client_1", "client")

    goals_call_args = mock_anthropic_clients["goals"].return_value.messages.create.call_args
    messages = goals_call_args.kwargs["messages"]
    combined_content = " ".join(m["content"] for m in messages)
    assert "Portfolio: 60% equity, 40% cash." in combined_content
    assert "Risk score: 6/10. High cash drag." in combined_content
