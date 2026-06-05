import pytest
import services.event_bus as event_bus_module


@pytest.fixture(autouse=True)
def reset_event_bus():
    event_bus_module._subscribers.clear()
    yield
    event_bus_module._subscribers.clear()


async def test_publish_delivers_to_subscriber():
    """Event published lands in subscriber queue."""
    q = event_bus_module.subscribe()
    await event_bus_module.publish({"type": "test", "value": 1})
    event = q.get_nowait()
    assert event == {"type": "test", "value": 1}


async def test_multiple_subscribers_all_receive_event():
    """All subscribers receive the same published event."""
    q1 = event_bus_module.subscribe()
    q2 = event_bus_module.subscribe()
    await event_bus_module.publish({"type": "broadcast", "value": 99})
    assert q1.get_nowait() == {"type": "broadcast", "value": 99}
    assert q2.get_nowait() == {"type": "broadcast", "value": 99}


async def test_chat_endpoint_publishes_agent_response_event(async_client, mock_orchestrator):
    """POST /api/chat/ publishes agent_response event to event bus."""
    login = await async_client.post(
        "/api/auth/login",
        data={"username": "alice@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    q = event_bus_module.subscribe()

    resp = await async_client.post(
        "/api/chat/",
        json={"message": "What is my portfolio?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    event = q.get_nowait()
    assert event["type"] == "agent_response"
    assert event["response"] == mock_orchestrator.return_value
    assert "user_id" in event
