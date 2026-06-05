from fastapi import APIRouter, Depends, HTTPException
from db.models import User
from api.auth import get_current_user
from data.fixtures import PORTFOLIOS

router = APIRouter()


@router.get("/")
async def get_portfolio(current_user: User = Depends(get_current_user)):
    portfolio = PORTFOLIOS.get(current_user.id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("/all")
async def get_all_portfolios(current_user: User = Depends(get_current_user)):
    if current_user.role.value != "advisor":
        raise HTTPException(status_code=403, detail="Advisor access only")
    return PORTFOLIOS
