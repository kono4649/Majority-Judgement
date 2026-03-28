"""
テスト共通フィクスチャ
- インメモリ SQLite + テーブル自動作成
- TestClient（同期）を使用
- ユーザー登録・ログイン済みクライアントを提供
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# インメモリ SQLite（テスト専用）- 共有キャッシュで全接続が同一DBを参照
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """各テスト前にテーブルを再作成し、後に削除"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """DB依存をオーバーライドした TestClient"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# ヘルパー
# --------------------------------------------------------------------------

def register_and_activate(client: TestClient, email: str, password: str) -> None:
    """ユーザー登録 → DEV_MODE でアクティベーショントークンをDBから取得してアクティベート"""
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "password_confirm": password},
    )
    assert resp.status_code == 200, resp.text

    # アクティベーショントークンをDBから直接取得
    db = next(override_get_db())
    from app import models
    user = db.query(models.User).filter(models.User.email == email).first()
    token = user.activation_token
    db.close()

    resp2 = client.get(f"/api/auth/activate/{token}", follow_redirects=False)
    assert resp2.status_code in (200, 302, 307)


def login(client: TestClient, email: str, password: str) -> None:
    """ログイン（クッキーをクライアントに保持させる）"""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text


@pytest.fixture
def auth_client(client: TestClient):
    """登録・アクティベーション・ログイン済みの TestClient"""
    email = "test@example.com"
    password = "Test1234!"
    register_and_activate(client, email, password)
    login(client, email, password)
    return client
