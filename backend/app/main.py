import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, Base, AsyncSessionLocal
from app.models.user import User
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

    # Create initial superuser from environment variables if configured
    if settings.INITIAL_SUPERUSER_EMAIL and settings.INITIAL_SUPERUSER_PASSWORD:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.is_superuser == True)  # noqa: E712
            )
            if result.scalar_one_or_none() is None:
                superuser = User(
                    id=str(uuid.uuid4()),
                    email=settings.INITIAL_SUPERUSER_EMAIL,
                    username=settings.INITIAL_SUPERUSER_USERNAME,
                    hashed_password=get_password_hash(settings.INITIAL_SUPERUSER_PASSWORD),
                    is_superuser=True,
                )
                db.add(superuser)
                await db.commit()
                logger.info("Initial superuser created: %s", settings.INITIAL_SUPERUSER_EMAIL)

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
