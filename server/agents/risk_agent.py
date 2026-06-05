import anthropic
from data.fixtures import PORTFOLIOS

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


SYSTEM = """You are a Risk Analysis Agent for AuraWealth.
Given a portfolio analysis, assess the risk profile.
Cover: concentration risk, volatility exposure, liquidity risk, and
whether the portfolio aligns with the user's stated risk tolerance.
Provide a risk score (1-10) and specific flags."""


async def run(user_id: str, portfolio_analysis: str) -> str:
    portfolio = PORTFOLIOS.get(user_id, {})

    context = f"""Portfolio analysis from previous agent:
{portfolio_analysis}

User risk profile: {portfolio.get('risk_profile', 'unknown')}
Assess the risks."""

    response = await get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": context}],
    )
    return response.content[0].text
