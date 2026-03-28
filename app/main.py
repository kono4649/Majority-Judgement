from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth as auth_router
from app.routers import polls as polls_router
from app.routers import votes as votes_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="投票アプリ API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api")
app.include_router(polls_router.router, prefix="/api")
app.include_router(votes_router.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
