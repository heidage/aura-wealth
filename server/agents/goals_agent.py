import anthropic
from data.fixtures import PORTFOLIOS

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


SYSTEM = """You are a Goals Planning Agent for AuraWealth.
Given portfolio and risk analysis, evaluate the user's financial goals.
For each goal: assess progress, project timeline feasibility, and
recommend specific actions to stay on track. Be encouraging but honest."""


async def run(user_id: str, portfolio_analysis: str, risk_analysis: str) -> str:
    portfolio = PORTFOLIOS.get(user_id, {})
    goals = portfolio.get("goals", [])

    goals_text = "\n".join(
        f"  - {g['name']}: ${g['current']:,.0f} / ${g['target']:,.0f} "
        f"({g['progress']:.1f}%) — target year {g['target_year']}"
        for g in goals
    )

    context = f"""Portfolio analysis: {portfolio_analysis}

Risk analysis: {risk_analysis}

User goals:
{goals_text}

Evaluate goal feasibility and recommend actions."""

    response = await get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": context}],
    )
    return response.content[0].text
