from fastapi import APIRouter, Depends
from db.models import User, UserRole
from api.auth import get_current_user
from data.fixtures import PORTFOLIOS, USERS

router = APIRouter()


@router.get("/")
async def get_user_context(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.client:
        portfolio = PORTFOLIOS.get(current_user.id, {})
        return {
            "role": "client",
            "user": {"id": current_user.id, "name": current_user.name},
            "portfolio": portfolio,
            "permissions": ["view_own_portfolio", "chat", "view_own_goals"],
        }

    # Advisor sees aggregated view of all clients
    clients = [u for u in USERS if u["role"] == "client"]
    client_summaries = [
        {
            "id": c["id"],
            "name": c["name"],
            "email": c["email"],
            "portfolio_value": PORTFOLIOS.get(c["id"], {}).get("total_value", 0),
            "risk_profile": PORTFOLIOS.get(c["id"], {}).get("risk_profile", "unknown"),
            "goals_count": len(PORTFOLIOS.get(c["id"], {}).get("goals", [])),
        }
        for c in clients
    ]
    total_aum = sum(s["portfolio_value"] for s in client_summaries)

    return {
        "role": "advisor",
        "user": {"id": current_user.id, "name": current_user.name},
        "aum": total_aum,
        "client_count": len(clients),
        "clients": client_summaries,
        "permissions": ["view_all_portfolios", "chat", "risk_analysis", "rebalance"],
    }
