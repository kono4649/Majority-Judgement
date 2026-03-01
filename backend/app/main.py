import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.db.session import engine, Base
import app.models  # noqa: F401 - ensure models are registered

logger = logging.getLogger(__name__)


async def wait_for_db(retries: int = 10, delay: float = 2.0) -> None:
    """Wait for the database to be ready, retrying with backoff."""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established.")
            return
        except Exception as exc:
            if attempt == retries:
                raise RuntimeError(f"Database not available after {retries} attempts") from exc
            logger.warning(
                "Database not ready (attempt %d/%d): %s. Retrying in %.0fs...",
                attempt, retries, exc, delay,
            )
            await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add is_public column to existing polls table if it doesn't exist
        await conn.execute(
            text(
                "ALTER TABLE polls ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )

    yield


app = FastAPI(
    title="Majority Judgement API",
    description="マジョリティ・ジャッジメント方式の投票プラットフォーム",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
