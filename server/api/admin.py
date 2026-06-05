from fastapi import APIRouter, Depends, HTTPException
from db.models import User, UserRole
from api.auth import get_current_user
from data.fixtures import PORTFOLIOS, USERS

router = APIRouter()


def require_advisor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.advisor:
        raise HTTPException(status_code=403, detail="Advisor access only")
    return current_user


@router.get("/clients")
async def list_clients(advisor: User = Depends(require_advisor)):
    clients = [u for u in USERS if u["role"] == "client"]
    return [
        {
            **c,
            "portfolio_value": PORTFOLIOS.get(c["id"], {}).get("total_value", 0),
            "risk_profile": PORTFOLIOS.get(c["id"], {}).get("risk_profile", "unknown"),
        }
        for c in clients
    ]


@router.get("/risk-analysis/{client_id}")
async def risk_analysis(client_id: str, advisor: User = Depends(require_advisor)):
    portfolio = PORTFOLIOS.get(client_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Client not found")

    holdings = portfolio["holdings"]
    total = portfolio["total_value"]

    equity = sum(h["value"] for h in holdings if h["symbol"] not in ("BND", "CASH"))
    bonds = sum(h["value"] for h in holdings if h["symbol"] == "BND")
    cash = sum(h["value"] for h in holdings if h["symbol"] == "CASH")

    return {
        "client_id": client_id,
        "risk_profile": portfolio["risk_profile"],
        "allocation": {
            "equity_pct": round(equity / total * 100, 2),
            "bonds_pct": round(bonds / total * 100, 2),
            "cash_pct": round(cash / total * 100, 2),
        },
        "concentration_risk": [
            h for h in holdings if h["allocation"] > 10
        ],
        "flags": [
            "High cash allocation — consider rebalancing"
            if cash / total > 0.5 else None,
            "Concentrated single-stock risk"
            if any(h["allocation"] > 15 for h in holdings if h["symbol"] != "CASH") else None,
        ],
    }
