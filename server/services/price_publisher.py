"""Background service: publishes simulated price ticks to Redis pub/sub."""
import asyncio
import json
import random
import redis.asyncio as aioredis
from data.fixtures import MARKET_PRICES

CHANNEL = "prices"


async def publish_prices(redis_url: str = "redis://localhost:6379"):
    r = aioredis.from_url(redis_url)
    prices = dict(MARKET_PRICES)
    try:
        while True:
            for symbol in prices:
                delta = prices[symbol] * random.uniform(-0.002, 0.002)
                prices[symbol] = round(prices[symbol] + delta, 2)
            await r.publish(CHANNEL, json.dumps(prices))
            await asyncio.sleep(1)
    finally:
        await r.aclose()


async def subscribe_prices(redis_url: str = "redis://localhost:6379"):
    """Async generator — yields price dicts from Redis pub/sub."""
    r = aioredis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(CHANNEL)
        await r.aclose()
