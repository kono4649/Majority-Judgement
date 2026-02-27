"""
テスト用設定ファイル
SQLite インメモリデータベースを使用してテスト環境を構築します。
"""
import uuid
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# テスト用環境変数を設定（インポート前に設定）
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["INITIAL_SUPERUSER_EMAIL"] = "admin@test.com"
os.environ["INITIAL_SUPERUSER_USERNAME"] = "admin"
os.environ["INITIAL_SUPERUSER_PASSWORD"] = "AdminPass123!"

import app.models  # noqa: F401 - ensure all models are registered
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.core.security import get_password_hash


# SQLite インメモリデータベースエンジン
# StaticPool を使用して全接続が同一のインメモリDBを共有するようにする
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッションを提供する依存性オーバーライド"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """セッション全体で共有するイベントループを作成"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """テスト用データベーステーブルを作成し、スーパーユーザーを初期化"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # スーパーユーザーを作成
    async with TestSessionLocal() as db:
        superuser = User(
            id=str(uuid.uuid4()),
            email="admin@test.com",
            username="admin",
            hashed_password=get_password_hash("AdminPass123!"),
            is_superuser=True,
        )
        db.add(superuser)
        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """テスト用 HTTP クライアント（セッション全体で共有）"""
    fastapi_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
