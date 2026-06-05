import anthropic
from data.fixtures import PORTFOLIOS

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


SYSTEM = """You are a Portfolio Analysis Agent for AuraWealth.
Analyze the user's portfolio holdings, allocation, and performance.
Return a concise structured analysis covering: total value, asset allocation breakdown,
top holdings, and any concentration concerns. Be data-driven and specific."""


async def run(user_id: str, query: str) -> str:
    portfolio = PORTFOLIOS.get(user_id, {})
    holdings = portfolio.get("holdings", [])
    total = portfolio.get("total_value", 0)

    holdings_text = "\n".join(
        f"  - {h['symbol']}: {h['allocation']:.1f}% (${h['value']:,.0f})"
        for h in holdings
    )

    context = f"""User portfolio:
Total value: ${total:,.2f}
Risk profile: {portfolio.get('risk_profile', 'unknown')}
Holdings:
{holdings_text}

User query: {query}"""

    response = await get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": context}],
    )
    return response.content[0].text
