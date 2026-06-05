import anthropic
from data.fixtures import PORTFOLIOS
from agents import portfolio_agent, risk_agent, goals_agent

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


CLIENT_SYSTEM = """You are AuraWealth AI, a personal wealth management assistant.
You receive analysis from specialist agents and synthesize it into a clear,
actionable response for the client. Be concise, warm, and data-driven.
Only discuss the client's own portfolio and goals — never other clients' data."""

ADVISOR_SYSTEM = """You are AuraWealth AI, an advisor command center assistant.
You help wealth advisors manage their book of business, flag clients needing
attention, and surface insights across the entire client portfolio.
Be analytical, direct, and highlight actionable opportunities."""


async def run_orchestrator(
    message: str,
    history: list[dict],
    user_id: str,
    user_role: str,
) -> str:
    if user_role == "advisor":
        return await _run_advisor_workflow(message, history)
    return await _run_client_workflow(message, history, user_id)


async def _run_client_workflow(message: str, history: list[dict], user_id: str) -> str:
    # Sequential: Portfolio → Risk → Goals → Synthesize
    portfolio_analysis = await portfolio_agent.run(user_id, message)
    risk_analysis = await risk_agent.run(user_id, portfolio_analysis)
    goals_analysis = await goals_agent.run(user_id, portfolio_analysis, risk_analysis)

    synthesis_prompt = f"""User asked: "{message}"

Portfolio Agent: {portfolio_analysis}
Risk Agent: {risk_analysis}
Goals Agent: {goals_analysis}

Synthesize into a concise, helpful response."""

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=CLIENT_SYSTEM,
        messages=history + [{"role": "user", "content": synthesis_prompt}],
    )
    return response.content[0].text


async def _run_advisor_workflow(message: str, history: list[dict]) -> str:
    all_portfolios = PORTFOLIOS
    summary = "\n".join(
        f"- {uid}: ${p['total_value']:,.0f} ({p['risk_profile']})"
        for uid, p in all_portfolios.items()
    )
    context = f"All client portfolios:\n{summary}\n\nAdvisor query: {message}"

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=ADVISOR_SYSTEM,
        messages=history + [{"role": "user", "content": context}],
    )
    return response.content[0].text
