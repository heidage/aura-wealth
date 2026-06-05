from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.auth import get_current_user
from db.models import User
from data.fixtures import MARKET_PRICES
import asyncio
import json
import random

router = APIRouter()


async def price_stream():
    prices = dict(MARKET_PRICES)
    while True:
        for symbol in prices:
            delta = prices[symbol] * random.uniform(-0.002, 0.002)
            prices[symbol] = round(prices[symbol] + delta, 2)

        yield f"data: {json.dumps(prices)}\n\n"
        await asyncio.sleep(1)


@router.get("/prices")
async def stream_prices(current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        price_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
