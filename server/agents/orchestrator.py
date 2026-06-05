import anthropic
from data.fixtures import PORTFOLIOS
from agents import portfolio_agent, risk_agent, goals_agent

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


SYSTEM = """You are AuraWealth AI, a personal wealth management assistant.
You receive analysis from specialist agents and synthesize it into a clear,
actionable response for the user. Be concise, warm, and data-driven."""


async def run_orchestrator(
    message: str,
    history: list[dict],
    user_id: str,
    user_role: str,
) -> str:
    # Sequential agentic workflow: Portfolio → Risk → Goals → Synthesize
    portfolio_analysis = await portfolio_agent.run(user_id, message)
    risk_analysis = await risk_agent.run(user_id, portfolio_analysis)
    goals_analysis = await goals_agent.run(user_id, portfolio_analysis, risk_analysis)

    synthesis_prompt = f"""User asked: "{message}"

Portfolio Agent analysis:
{portfolio_analysis}

Risk Agent analysis:
{risk_analysis}

Goals Agent analysis:
{goals_analysis}

Synthesize these into a concise, helpful response for the user."""

    messages = history + [{"role": "user", "content": synthesis_prompt}]

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=messages,
    )
    return response.content[0].text
