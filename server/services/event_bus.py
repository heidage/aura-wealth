"""Async event bus: asyncio.Queue-based broadcast to SSE subscribers."""
import asyncio
import json
from typing import AsyncGenerator

_subscribers: list[asyncio.Queue] = []


async def publish(event: dict) -> None:
    for q in _subscribers:
        await q.put(event)


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    try:
        _subscribers.remove(q)
    except ValueError:
        pass


async def event_stream(q: asyncio.Queue) -> AsyncGenerator[str, None]:
    try:
        while True:
            event = await q.get()
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        unsubscribe(q)
