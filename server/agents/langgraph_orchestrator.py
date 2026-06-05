"""
Hierarchical LangGraph orchestrator — replaces the sequential agent chain.

Graph topology:
  START → router → [conditional] → portfolio | risk | goals | synthesizer
  portfolio → [conditional] → risk | goals | synthesizer
  risk → [conditional] → goals | synthesizer
  goals → synthesizer → END

The router dynamically selects which expert nodes to invoke based on query
intent, so a pure risk question never pays the latency cost of portfolio/goals.
"""

import anthropic
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from data.fixtures import PORTFOLIOS
from rag.hybrid_search import hybrid_search

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class WealthState(TypedDict):
    query: str
    history: list[dict]
    user_id: str
    active_agents: list[str]
    portfolio_output: str
    risk_output: str
    goals_output: str
    rag_context: str
    response: str


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

_PORTFOLIO_KEYWORDS = {"portfolio", "holdings", "allocation", "stock", "etf", "fund", "invest", "asset"}
_RISK_KEYWORDS = {"risk", "volatile", "volatility", "exposure", "safe", "loss", "drawdown", "hedge"}
_GOALS_KEYWORDS = {"goal", "retire", "retirement", "save", "saving", "target", "plan", "future", "timeline"}


def _classify_agents(query: str) -> list[str]:
    words = set(query.lower().split())
    agents: list[str] = []
    if words & _PORTFOLIO_KEYWORDS:
        agents.append("portfolio")
    if words & _RISK_KEYWORDS:
        agents.append("risk")
    if words & _GOALS_KEYWORDS:
        agents.append("goals")
    return agents or ["portfolio", "risk", "goals"]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def router_node(state: WealthState) -> dict:
    active = _classify_agents(state["query"])

    rag_context = ""
    try:
        hits = hybrid_search(state["query"], n_results=3, candidate_k=15)
        if hits:
            snippets = "\n".join(
                f"- [{h['metadata']['source']}] {h['text'][:200]}" for h in hits
            )
            rag_context = f"Relevant financial research:\n{snippets}"
    except Exception:
        pass

    return {"active_agents": active, "rag_context": rag_context}


async def portfolio_node(state: WealthState) -> dict:
    from agents.portfolio_agent import run
    output = await run(state["user_id"], state["query"])
    return {"portfolio_output": output}


async def risk_node(state: WealthState) -> dict:
    from agents.risk_agent import run
    output = await run(state["user_id"], state.get("portfolio_output", ""))
    return {"risk_output": output}


async def goals_node(state: WealthState) -> dict:
    from agents.goals_agent import run
    output = await run(
        state["user_id"],
        state.get("portfolio_output", ""),
        state.get("risk_output", ""),
    )
    return {"goals_output": output}


async def synthesizer_node(state: WealthState) -> dict:
    parts = []
    if state.get("rag_context"):
        parts.append(state["rag_context"])
    if state.get("portfolio_output"):
        parts.append(f"Portfolio Agent:\n{state['portfolio_output']}")
    if state.get("risk_output"):
        parts.append(f"Risk Agent:\n{state['risk_output']}")
    if state.get("goals_output"):
        parts.append(f"Goals Agent:\n{state['goals_output']}")

    synthesis_prompt = (
        f'User asked: "{state["query"]}"\n\n'
        + "\n\n".join(parts)
        + "\n\nSynthesize into a concise, actionable response."
    )

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are AuraWealth AI. Synthesize expert analyses into a clear, "
            "helpful response. Be concise and data-driven."
        ),
        messages=state["history"] + [{"role": "user", "content": synthesis_prompt}],
    )
    return {"response": response.content[0].text}


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _after_router(state: WealthState) -> Literal["portfolio", "risk", "goals", "synthesizer"]:
    active = state["active_agents"]
    if "portfolio" in active:
        return "portfolio"
    if "risk" in active:
        return "risk"
    if "goals" in active:
        return "goals"
    return "synthesizer"


def _after_portfolio(state: WealthState) -> Literal["risk", "goals", "synthesizer"]:
    active = state["active_agents"]
    if "risk" in active:
        return "risk"
    if "goals" in active:
        return "goals"
    return "synthesizer"


def _after_risk(state: WealthState) -> Literal["goals", "synthesizer"]:
    if "goals" in state["active_agents"]:
        return "goals"
    return "synthesizer"


# ---------------------------------------------------------------------------
# Graph compilation (singleton)
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    g = StateGraph(WealthState)

    g.add_node("router", router_node)
    g.add_node("portfolio", portfolio_node)
    g.add_node("risk", risk_node)
    g.add_node("goals", goals_node)
    g.add_node("synthesizer", synthesizer_node)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", _after_router, ["portfolio", "risk", "goals", "synthesizer"])
    g.add_conditional_edges("portfolio", _after_portfolio, ["risk", "goals", "synthesizer"])
    g.add_conditional_edges("risk", _after_risk, ["goals", "synthesizer"])
    g.add_edge("goals", "synthesizer")
    g.add_edge("synthesizer", END)

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_langgraph_orchestrator(
    message: str,
    history: list[dict],
    user_id: str,
) -> str:
    initial_state: WealthState = {
        "query": message,
        "history": history,
        "user_id": user_id,
        "active_agents": [],
        "portfolio_output": "",
        "risk_output": "",
        "goals_output": "",
        "rag_context": "",
        "response": "",
    }
    result = await get_graph().ainvoke(initial_state)
    return result["response"]
