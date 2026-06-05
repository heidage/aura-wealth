import pytest


async def get_token(async_client, email, password):
    resp = await async_client.post(
        "/api/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_client_context_contains_own_portfolio_only(async_client):
    token = await get_token(async_client, "alice@example.com", "password123")
    resp = await async_client.get("/api/context/", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "client"
    assert "portfolio" in data
    assert data["portfolio"]["total_value"] == 485000.00
    # client context must NOT expose other clients
    assert "clients" not in data
    assert "aum" not in data


async def test_advisor_context_contains_all_clients_and_aum(async_client):
    token = await get_token(async_client, "advisor@aurawealth.com", "advisor123")
    resp = await async_client.get("/api/context/", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "advisor"
    assert data["client_count"] == 2
    assert data["aum"] == 485000.00 + 1250000.00
    client_ids = [c["id"] for c in data["clients"]]
    assert "user_client_1" in client_ids
    assert "user_client_2" in client_ids


async def test_different_users_have_isolated_chat_history(async_client, mock_orchestrator):
    token_alice = await get_token(async_client, "alice@example.com", "password123")
    token_bob = await get_token(async_client, "bob@example.com", "password123")

    await async_client.post(
        "/api/chat/",
        json={"message": "Alice secret question"},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    await async_client.post(
        "/api/chat/",
        json={"message": "Bob secret question"},
        headers={"Authorization": f"Bearer {token_bob}"},
    )

    alice_history = (await async_client.get(
        "/api/chat/history", headers={"Authorization": f"Bearer {token_alice}"}
    )).json()
    bob_history = (await async_client.get(
        "/api/chat/history", headers={"Authorization": f"Bearer {token_bob}"}
    )).json()

    alice_contents = [m["content"] for m in alice_history]
    bob_contents = [m["content"] for m in bob_history]

    assert "Alice secret question" in alice_contents
    assert "Bob secret question" not in alice_contents
    assert "Bob secret question" in bob_contents
    assert "Alice secret question" not in bob_contents
