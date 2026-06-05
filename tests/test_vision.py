import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO

# Minimal 1x1 red PNG
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
)


def make_mock_vision_response(text: str):
    r = MagicMock()
    r.content = [MagicMock(text=text)]
    return r


@pytest.fixture
def mock_vision_client():
    with patch("api.vision.get_client") as m:
        m.return_value.messages.create = AsyncMock(
            return_value=make_mock_vision_response("I see a financial chart showing upward trends.")
        )
        yield m


async def get_token(async_client):
    resp = await async_client.post(
        "/api/auth/login", data={"username": "alice@example.com", "password": "password123"}
    )
    return resp.json()["access_token"]


async def test_single_image_upload_returns_analysis(async_client, mock_vision_client):
    token = await get_token(async_client)
    resp = await async_client.post(
        "/api/vision/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files=[("files", ("chart.png", BytesIO(PNG_BYTES), "image/png"))],
        data={"message": "Describe this chart"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["images_processed"] == 1
    assert data["response"] == "I see a financial chart showing upward trends."


async def test_multiple_images_all_included_in_api_call(async_client, mock_vision_client):
    token = await get_token(async_client)
    resp = await async_client.post(
        "/api/vision/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files=[
            ("files", ("chart1.png", BytesIO(PNG_BYTES), "image/png")),
            ("files", ("chart2.png", BytesIO(PNG_BYTES), "image/png")),
            ("files", ("chart3.png", BytesIO(PNG_BYTES), "image/png")),
        ],
        data={"message": "Compare these charts"},
    )
    assert resp.status_code == 200
    assert resp.json()["images_processed"] == 3

    call_args = mock_vision_client.return_value.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    image_blocks = [b for b in content if b["type"] == "image"]
    assert len(image_blocks) == 3


async def test_unsupported_file_type_skipped_not_crashed(async_client, mock_vision_client):
    token = await get_token(async_client)
    resp = await async_client.post(
        "/api/vision/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files=[
            ("files", ("report.pdf", BytesIO(b"%PDF-fake"), "application/pdf")),
            ("files", ("chart.png", BytesIO(PNG_BYTES), "image/png")),
        ],
        data={"message": "Analyze"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "report.pdf" in data["skipped_files"]
    assert data["images_processed"] == 1
