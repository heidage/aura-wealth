import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


def _text_response(text: str):
    block = MagicMock()
    block.text = text
    block.type = "text"
    r = MagicMock()
    r.stop_reason = "end_turn"
    r.content = [block]
    return r


def _tool_use_response(tool_id: str, query: str):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "web_search"
    tool_block.id = tool_id
    tool_block.input = {"query": query, "max_results": 3}

    r = MagicMock()
    r.stop_reason = "tool_use"
    r.content = [tool_block]
    return r


_FAKE_SEARCH_RESULTS = [
    {"title": "Fed holds rates steady", "snippet": "Federal Reserve kept rates at 5.25%.", "url": "https://example.com/1"},
    {"title": "S&P 500 rises 0.5%", "snippet": "Equities gained on strong earnings.", "url": "https://example.com/2"},
]


@pytest.mark.asyncio
async def test_market_agent_calls_web_search_tool():
    """Agent invokes web_search tool, receives results, returns grounded text."""
    from agents.market_agent import run

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=[
        _tool_use_response("tid_1", "current interest rates 2024"),
        _text_response("Fed held rates at 5.25%. Equities rose on strong earnings."),
    ])

    with (
        patch("agents.market_agent.get_client", return_value=mock_client),
        patch("agents.market_agent.execute_web_search", return_value=_FAKE_SEARCH_RESULTS),
    ):
        result = await run("What are current interest rates?")

    assert "5.25" in result or "Fed" in result or "rate" in result.lower()
    assert mock_client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_market_agent_returns_text_on_direct_answer():
    """If Claude answers without tool use, result is returned immediately."""
    from agents.market_agent import run

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_text_response(
        "Markets are currently closed for the weekend."
    ))

    with patch("agents.market_agent.get_client", return_value=mock_client):
        result = await run("Are markets open today?")

    assert "Markets" in result or "market" in result.lower()
    assert mock_client.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_market_node_routes_on_market_keywords():
    """LangGraph router includes 'market' agent for market-related queries."""
    from agents.langgraph_orchestrator import _classify_agents

    agents = _classify_agents("What is the current market trend for tech stocks today?")
    assert "market" in agents


def test_execute_web_search_returns_list_on_error():
    """execute_web_search returns error entry rather than raising."""
    from agents.market_agent import execute_web_search

    with patch("agents.market_agent.DDGS", side_effect=Exception("network error")):
        results = execute_web_search("test query")

    assert isinstance(results, list)
    assert len(results) == 1
    assert "error" in results[0]["title"].lower()
