import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# get_portfolio
# ---------------------------------------------------------------------------

def test_get_portfolio_returns_holdings_for_valid_user():
    from mcp_server import get_portfolio

    result = get_portfolio("user_client_1")

    assert result["user_id"] == "user_client_1"
    assert result["total_value"] == 485000.00
    assert result["risk_profile"] == "moderate"
    assert isinstance(result["holdings"], list)
    assert len(result["holdings"]) > 0
    assert "symbol" in result["holdings"][0]


def test_get_portfolio_returns_error_for_unknown_user():
    from mcp_server import get_portfolio

    result = get_portfolio("nonexistent_user")

    assert "error" in result


# ---------------------------------------------------------------------------
# get_user_goals
# ---------------------------------------------------------------------------

def test_get_user_goals_returns_goals_with_progress():
    from mcp_server import get_user_goals

    result = get_user_goals("user_client_1")

    assert result["user_id"] == "user_client_1"
    goals = result["goals"]
    assert isinstance(goals, list)
    assert len(goals) >= 1
    assert "name" in goals[0]
    assert "progress" in goals[0]
    assert "target_year" in goals[0]


# ---------------------------------------------------------------------------
# get_market_prices
# ---------------------------------------------------------------------------

def test_get_market_prices_returns_known_and_unknown():
    from mcp_server import get_market_prices

    result = get_market_prices(["AAPL", "NVDA", "FAKE_TICKER"])

    assert result["prices"]["AAPL"] == 189.50
    assert result["prices"]["NVDA"] == 875.40
    assert result["prices"]["FAKE_TICKER"] is None
    assert "FAKE_TICKER" in result["unknown"]


# ---------------------------------------------------------------------------
# query_chat_history — SQLite integration
# ---------------------------------------------------------------------------

def test_query_chat_history_reads_from_sqlite(tmp_path):
    from mcp_server import query_chat_history

    db_file = tmp_path / "aura_wealth.db"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(
            "CREATE TABLE messages (role TEXT, content TEXT, created_at TEXT, user_id TEXT)"
        )
        conn.execute(
            "INSERT INTO messages VALUES ('user', 'Hello', '2024-01-01', 'user_client_1')"
        )
        conn.execute(
            "INSERT INTO messages VALUES ('assistant', 'Hi there', '2024-01-01', 'user_client_1')"
        )
        conn.commit()

    with patch("mcp_server.DB_PATH", db_file):
        result = query_chat_history("user_client_1", limit=10)

    assert result["count"] == 2
    roles = {m["role"] for m in result["messages"]}
    assert "user" in roles
    assert "assistant" in roles


def test_query_chat_history_handles_missing_db(tmp_path):
    from mcp_server import query_chat_history

    missing = tmp_path / "no_such_db.db"
    with patch("mcp_server.DB_PATH", missing):
        result = query_chat_history("user_client_1")

    assert result["count"] == 0
    assert result["messages"] == []
    assert "note" in result


# ---------------------------------------------------------------------------
# MCP server registers tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_server_has_required_tools():
    from mcp_server import mcp

    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert "get_portfolio" in tool_names
    assert "get_user_goals" in tool_names
    assert "get_market_prices" in tool_names
    assert "query_chat_history" in tool_names
