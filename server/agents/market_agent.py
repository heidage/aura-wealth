"""
Market Intelligence Agent — uses Claude tool use to ground responses
in live web search results via DuckDuckGo.
"""
import json
import anthropic
from duckduckgo_search import DDGS

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


WEB_SEARCH_TOOL: dict = {
    "name": "web_search",
    "description": (
        "Search the web for current financial news, market prices, "
        "economic indicators, and company data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for current market information",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return (1–5)",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}

SYSTEM = """You are a Market Intelligence Agent for AuraWealth.
You have a web_search tool to retrieve live financial news, prices, and macro data.
Always call web_search at least once before answering market-related questions.
Cite sources by title. Be concise and highlight what matters for the client's portfolio."""


def execute_web_search(query: str, max_results: int = 3) -> list[dict]:
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
            for r in raw
        ]
    except Exception as e:
        return [{"title": "Search error", "snippet": str(e), "url": ""}]


async def run(query: str, portfolio_context: str = "") -> str:
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Portfolio context: {portfolio_context}\n\nUser query: {query}"
                if portfolio_context
                else query
            ),
        }
    ]

    for _ in range(4):  # max 4 agentic rounds
        response = await get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM,
            tools=[WEB_SEARCH_TOOL],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "web_search":
                    results = execute_web_search(
                        block.input.get("query", query),
                        block.input.get("max_results", 3),
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(results),
                        }
                    )
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return "Unable to retrieve market data at this time."
