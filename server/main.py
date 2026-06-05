from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.database import init_db
from api.auth import router as auth_router
from api.chat import router as chat_router
from api.portfolio import router as portfolio_router
from api.admin import router as admin_router
from api.stream import router as stream_router
from api.context import router as context_router
from api.vision import router as vision_router
from api.rag import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AuraWealth API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(stream_router, prefix="/api/stream", tags=["stream"])
app.include_router(context_router, prefix="/api/context", tags=["context"])
app.include_router(vision_router, prefix="/api/vision", tags=["vision"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])


@app.get("/health")
async def health():
    return {"status": "ok"}
