from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Annotated
from api.auth import get_current_user
from db.models import User
import anthropic
import base64

router = APIRouter()

SUPPORTED_MEDIA_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
}

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB per image (Claude limit)

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


def _to_image_block(data: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(data).decode("utf-8"),
        },
    }


@router.post("/analyze")
async def analyze_images(
    files: Annotated[list[UploadFile], File(description="One or more image files")],
    message: Annotated[str, Form()] = "What do you see in this image? Relate it to wealth management if possible.",
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    content: list[dict] = []
    skipped: list[str] = []

    for upload in files:
        raw_type = upload.content_type or ""
        media_type = SUPPORTED_MEDIA_TYPES.get(raw_type)

        if not media_type:
            skipped.append(upload.filename or "unknown")
            continue

        data = await upload.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"{upload.filename} exceeds 5 MB per-image limit",
            )
        content.append(_to_image_block(data, media_type))

    if not content:
        return {
            "response": "No supported image types found.",
            "skipped_files": skipped,
            "supported_types": list(SUPPORTED_MEDIA_TYPES.keys()),
        }

    content.append({"type": "text", "text": message})

    response = await get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )

    return {
        "response": response.content[0].text,
        "images_processed": len(content) - 1,
        "skipped_files": skipped,
    }
