import pytest
import json
from data.fixtures import MARKET_PRICES


async def test_direct_price_stream_yields_all_symbols():
    from api.stream import direct_price_stream

    gen = direct_price_stream()
    chunk = await gen.__anext__()

    assert chunk.startswith("data: ")
    prices = json.loads(chunk.replace("data: ", "").strip())
    for symbol in MARKET_PRICES:
        assert symbol in prices
        assert isinstance(prices[symbol], float)


async def test_direct_price_stream_prices_fluctuate():
    from api.stream import direct_price_stream

    gen = direct_price_stream()
    tick1 = json.loads((await gen.__anext__()).replace("data: ", "").strip())
    tick2 = json.loads((await gen.__anext__()).replace("data: ", "").strip())

    # At least one symbol must change between ticks
    changed = any(tick1[s] != tick2[s] for s in MARKET_PRICES)
    assert changed


async def test_price_fluctuation_within_sane_bounds():
    from api.stream import direct_price_stream

    gen = direct_price_stream()
    initial = json.loads((await gen.__anext__()).replace("data: ", "").strip())

    for _ in range(10):
        tick = json.loads((await gen.__anext__()).replace("data: ", "").strip())
        for symbol, base_price in initial.items():
            # Price should never move more than 5% from initial in 10 ticks
            assert abs(tick[symbol] - base_price) / base_price < 0.05


async def test_stream_endpoint_requires_auth(async_client):
    resp = await async_client.get("/api/stream/prices")
    assert resp.status_code == 401
