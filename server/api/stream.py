from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.auth import get_current_user
from db.models import User
from data.fixtures import MARKET_PRICES
import asyncio
import json
import os
import random

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def direct_price_stream():
    """Fallback: generate price ticks in-process."""
    prices = dict(MARKET_PRICES)
    while True:
        for symbol in prices:
            delta = prices[symbol] * random.uniform(-0.002, 0.002)
            prices[symbol] = round(prices[symbol] + delta, 2)
        yield f"data: {json.dumps(prices)}\n\n"
        await asyncio.sleep(1)


async def redis_price_stream():
    """Primary: subscribe to Redis pub/sub channel."""
    from services.price_publisher import subscribe_prices
    async for prices in subscribe_prices(REDIS_URL):
        yield f"data: {json.dumps(prices)}\n\n"


async def price_stream():
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, socket_connect_timeout=0.5)
        await r.ping()
        await r.aclose()
        async for chunk in redis_price_stream():
            yield chunk
    except Exception:
        async for chunk in direct_price_stream():
            yield chunk


@router.get("/prices")
async def stream_prices(current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        price_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
