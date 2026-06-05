# AuraWealth

Consumer wealth management app — agentic AI advisor for clients and a command center for advisors.

## Stack

- **Backend**: Python + FastAPI (async), SQLite, Redis, ChromaDB
- **Frontend**: React + Vite + Tailwind CSS
- **AI**: Anthropic SDK (claude-sonnet-4-6), LangGraph, OpenAI embeddings, Ollama

## Quick Start

### Backend

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env  # add your API keys
uvicorn main:app --reload
```

### Frontend

```bash
cd client
npm install
npm run dev
```

## Architecture

```mermaid
graph TD
    Browser["Browser (React)"]

    subgraph FastAPI
        Auth["Auth (JWT)"]
        ChatAPI["POST /api/chat"]
        EventsSSE["GET /api/events/stream (SSE)"]
        PricesSSE["GET /api/stream/prices (SSE)"]
        VisionAPI["POST /api/vision/analyze"]
        RAGAPI["GET /api/rag/search\nGET /api/rag/hybrid-search"]
    end

    subgraph Guardrails
        Validator["13 injection patterns\nPII redaction"]
    end

    subgraph LangGraph["LangGraph Orchestrator"]
        Router["Router Node"]
        Portfolio["PortfolioAgent"]
        Risk["RiskAgent"]
        Goals["GoalsAgent"]
        Market["MarketAgent"]
        Synthesizer["Synthesizer"]
    end

    subgraph RAG["RAG Pipeline"]
        Semantic["ChromaDB\n(text-embedding-3-small)"]
        BM25["BM25 Re-ranker"]
        HybridSearch["Hybrid Search\n0.5×semantic + 0.5×BM25"]
    end

    subgraph EventBus["Async Event Bus"]
        Queue["asyncio.Queue"]
        Redis["Redis pub/sub"]
    end

    subgraph MCP["MCP Server (stdio)"]
        Tools["4 tools: portfolio\nprices, history, context"]
    end

    SQLite[("SQLite\nUsers + Messages")]
    DuckDuckGo["DuckDuckGo DDGS"]

    Browser -->|login| Auth
    Browser -->|chat| ChatAPI
    Browser -->|SSE| EventsSSE
    Browser -->|SSE| PricesSSE

    ChatAPI --> Validator
    Validator -->|sanitized| LangGraph
    Router --> Portfolio
    Router --> Risk
    Router --> Goals
    Router --> Market
    Market -->|tool_use| DuckDuckGo
    Portfolio & Risk & Goals & Market --> Synthesizer
    Synthesizer -->|response| ChatAPI
    ChatAPI -->|publish| Queue
    Queue -->|broadcast| EventsSSE

    Redis -->|pub/sub| PricesSSE
    RAGAPI --> HybridSearch
    HybridSearch --> Semantic
    HybridSearch --> BM25

    ChatAPI --> SQLite
    Auth --> SQLite
    MCP --> SQLite
```

## Demo Users

| Email | Password | Role |
|-------|----------|------|
| alice@example.com | password123 | Client |
| bob@example.com | password123 | Client |
| advisor@aurawealth.com | advisor123 | Advisor |
