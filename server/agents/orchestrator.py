import anthropic
from data.fixtures import PORTFOLIOS

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client

SYSTEM_PROMPT = """You are AuraWealth AI, a personal wealth management assistant.
You have access to the user's portfolio data and can answer questions about:
- Portfolio performance and holdings
- Financial goals and progress
- Risk analysis and recommendations
- Market insights and news

Be concise, professional, and data-driven. Always reference specific numbers from the user's portfolio when relevant.
"""


async def run_orchestrator(
    message: str,
    history: list[dict],
    user_id: str,
    user_role: str,
) -> str:
    portfolio = PORTFOLIOS.get(user_id, {})
    portfolio_context = f"\nUser portfolio summary: total value ${portfolio.get('total_value', 0):,.2f}, risk profile: {portfolio.get('risk_profile', 'unknown')}" if portfolio else ""

    messages = history + [{"role": "user", "content": message}]

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT + portfolio_context,
        messages=messages,
    )

    return response.content[0].text
