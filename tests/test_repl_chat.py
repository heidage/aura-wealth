import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_anthropic():
    with patch("repl_chat.client") as mock_client:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Diversify into bonds to reduce volatility.")]
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        yield mock_client


@pytest.mark.asyncio
async def test_chat_turn_appends_user_and_assistant_to_history(mock_anthropic):
    from repl_chat import chat_turn

    history = []
    reply = await chat_turn(history, "What should I do with my portfolio?")

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "What should I do with my portfolio?"}
    assert history[1] == {"role": "assistant", "content": reply}


@pytest.mark.asyncio
async def test_chat_turn_preserves_multi_turn_history(mock_anthropic):
    from repl_chat import chat_turn

    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi, how can I help?"},
    ]
    await chat_turn(history, "What is my risk exposure?")

    assert len(history) == 4
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_turn_passes_full_history_to_api(mock_anthropic):
    from repl_chat import chat_turn

    history = [{"role": "user", "content": "Prior message"}, {"role": "assistant", "content": "Prior reply"}]
    await chat_turn(history, "Follow-up question")

    call_args = mock_anthropic.messages.create.call_args
    messages_sent = call_args.kwargs["messages"]
    # history is mutated before the call: prior 2 + new user msg = 3 at call time
    assert any(m["content"] == "Follow-up question" and m["role"] == "user" for m in messages_sent)
    assert any(m["content"] == "Prior message" for m in messages_sent)
    assert messages_sent[0]["content"] == "Prior message"
