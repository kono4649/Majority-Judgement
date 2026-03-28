"""
認証APIのテスト

カバー範囲:
- POST /api/auth/register
- GET  /api/auth/activate/{token}
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
"""
import pytest
from fastapi.testclient import TestClient

from .conftest import login, register_and_activate

EMAIL = "user@example.com"
PASSWORD = "Test1234!"


# --------------------------------------------------------------------------
# 登録
# --------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self, client: TestClient):
        resp = client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD},
        )
        assert resp.status_code == 200
        assert "登録メールを" in resp.json()["message"]

    def test_register_duplicate_email(self, client: TestClient):
        for _ in range(2):
            client.post(
                "/api/auth/register",
                json={"email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD},
            )
        resp = client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD},
        )
        assert resp.status_code == 409

    def test_register_password_mismatch(self, client: TestClient):
        resp = client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "password_confirm": "Different9!"},
        )
        assert resp.status_code == 422

    def test_register_weak_password(self, client: TestClient):
        resp = client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": "short", "password_confirm": "short"},
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("pw", [
        "alllowercase1!",   # 大文字なし
        "ALLUPPERCASE1!",   # 小文字なし
        "NoDigitHere!",     # 数字なし
        "NoSpecial1234",    # 記号なし
        "Short1!",          # 8文字未満
    ])
    def test_register_invalid_passwords(self, client: TestClient, pw: str):
        resp = client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": pw, "password_confirm": pw},
        )
        assert resp.status_code == 422


# --------------------------------------------------------------------------
# アクティベーション
# --------------------------------------------------------------------------

class TestActivation:
    def test_activate_success(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD},
        )
        from app import models
        from .conftest import override_get_db
        db = next(override_get_db())
        user = db.query(models.User).filter(models.User.email == EMAIL).first()
        token = user.activation_token
        db.close()

        resp = client.get(f"/api/auth/activate/{token}", follow_redirects=False)
        assert resp.status_code in (200, 302, 307)

    def test_activate_invalid_token(self, client: TestClient):
        resp = client.get("/api/auth/activate/invalidtoken", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "error=invalid_token" in resp.headers.get("location", "")


# --------------------------------------------------------------------------
# ログイン
# --------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client: TestClient):
        register_and_activate(client, EMAIL, PASSWORD)
        resp = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_login_wrong_password(self, client: TestClient):
        register_and_activate(client, EMAIL, PASSWORD)
        resp = client.post("/api/auth/login", json={"email": EMAIL, "password": "Wrong1234!"})
        assert resp.status_code == 401

    def test_login_not_activated(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD},
        )
        resp = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        assert resp.status_code == 403

    def test_login_unknown_email(self, client: TestClient):
        resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
        assert resp.status_code == 401


# --------------------------------------------------------------------------
# ログアウト・me
# --------------------------------------------------------------------------

class TestMeAndLogout:
    def test_me_authenticated(self, auth_client: TestClient):
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_me_unauthenticated(self, client: TestClient):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_logout(self, auth_client: TestClient):
        resp = auth_client.post("/api/auth/logout")
        assert resp.status_code == 200
        # ログアウト後は /me が 401
        resp2 = auth_client.get("/api/auth/me")
        assert resp2.status_code == 401
