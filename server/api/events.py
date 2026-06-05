from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.auth import get_current_user
from db.models import User
from services.event_bus import subscribe, event_stream

router = APIRouter()


@router.get("/stream")
async def stream_events(current_user: User = Depends(get_current_user)):
    q = subscribe()
    return StreamingResponse(
        event_stream(q),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
