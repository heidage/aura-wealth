"""
AuraWealth MCP Server — FastMCP over stdio (JSONL transport).

Tools:
  get_portfolio       — portfolio holdings and value from fixtures
  get_user_goals      — financial goals for a user
  get_market_prices   — current prices for ticker symbols
  query_chat_history  — live SQLite query of the messages table
"""

import sys
import sqlite3
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from data.fixtures import PORTFOLIOS, MARKET_PRICES

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("aura-mcp")

DB_PATH = Path(__file__).parent / "aura_wealth.db"


@asynccontextmanager
async def lifespan(app):
    logger.info("hello world")
    yield


mcp = FastMCP("AuraWealth MCP Server", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_portfolio(user_id: str) -> dict:
    """Return portfolio holdings, total value, and risk profile for a user."""
    portfolio = PORTFOLIOS.get(user_id)
    if not portfolio:
        return {"error": f"No portfolio found for user_id={user_id!r}"}
    return {
        "user_id": user_id,
        "total_value": portfolio["total_value"],
        "risk_profile": portfolio["risk_profile"],
        "holdings": portfolio["holdings"],
    }


@mcp.tool()
def get_user_goals(user_id: str) -> dict:
    """Return financial goals and progress for a user."""
    portfolio = PORTFOLIOS.get(user_id)
    if not portfolio:
        return {"error": f"No data for user_id={user_id!r}"}
    return {"user_id": user_id, "goals": portfolio["goals"]}


@mcp.tool()
def get_market_prices(symbols: list[str]) -> dict:
    """Return current market prices for the given ticker symbols."""
    return {
        "prices": {s: MARKET_PRICES.get(s) for s in symbols},
        "unknown": [s for s in symbols if s not in MARKET_PRICES],
    }


@mcp.tool()
def query_chat_history(user_id: str, limit: int = 10) -> dict:
    """Query SQLite messages table for a user's conversation history."""
    if not DB_PATH.exists():
        return {"user_id": user_id, "messages": [], "count": 0, "note": "DB not initialised"}

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, max(1, min(limit, 100))),
        ).fetchall()

    return {
        "user_id": user_id,
        "messages": [dict(r) for r in rows],
        "count": len(rows),
    }


# ---------------------------------------------------------------------------
# Entry point — stdio JSONL transport (MCP default)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
