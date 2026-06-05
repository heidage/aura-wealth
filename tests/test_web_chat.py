import pytest


async def get_token(async_client, email="alice@example.com", password="password123"):
    resp = await async_client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_chat_returns_ai_response(async_client, mock_orchestrator):
    token = await get_token(async_client)
    resp = await async_client.post(
        "/api/chat/",
        json={"message": "What is my portfolio value?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["response"] == "Your portfolio is well-diversified."
    mock_orchestrator.assert_called_once()


async def test_chat_history_persists_across_turns(async_client, mock_orchestrator):
    token = await get_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    await async_client.post("/api/chat/", json={"message": "First message"}, headers=headers)
    await async_client.post("/api/chat/", json={"message": "Second message"}, headers=headers)

    history_resp = await async_client.get("/api/chat/history", headers=headers)
    assert history_resp.status_code == 200
    messages = history_resp.json()
    roles = [m["role"] for m in messages]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 2


async def test_chat_isolated_per_user(async_client, mock_orchestrator):
    token_alice = await get_token(async_client, "alice@example.com", "password123")
    token_bob = await get_token(async_client, "bob@example.com", "password123")

    await async_client.post(
        "/api/chat/",
        json={"message": "Alice's private message"},
        headers={"Authorization": f"Bearer {token_alice}"},
    )

    bob_history = await async_client.get(
        "/api/chat/history",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    contents = [m["content"] for m in bob_history.json()]
    assert "Alice's private message" not in contents
