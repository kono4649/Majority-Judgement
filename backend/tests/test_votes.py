"""
匿名投票 API のテスト

カバー範囲:
- GET  /api/vote/{public_id}         フォーム取得
- GET  /api/vote/{public_id}/status  投票済みチェック
- POST /api/vote/{public_id}         投票送信・重複防止
"""
import pytest
from fastapi.testclient import TestClient


def _create_poll(auth_client: TestClient, method: str = "plurality", options=None) -> dict:
    if options is None:
        options = ["A", "B", "C"]
    resp = auth_client.post(
        "/api/polls/",
        json={
            "title": "テスト",
            "description": "",
            "voting_method": method,
            "options": options,
            "method_settings": {},
            "start_time": None,
            "end_time": None,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------
# フォーム取得
# --------------------------------------------------------------------------

class TestGetVotePoll:
    def test_get_existing_poll(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        resp = auth_client.get(f"/api/vote/{poll['public_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["public_id"] == poll["public_id"]
        assert len(data["options"]) == 3

    def test_get_nonexistent_poll(self, client: TestClient):
        resp = client.get("/api/vote/nonexistent-id")
        assert resp.status_code == 404


# --------------------------------------------------------------------------
# 投票済みステータス
# --------------------------------------------------------------------------

class TestVoteStatus:
    def test_status_before_vote(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        # 別クライアント（クッキーなし）でステータス確認
        from fastapi.testclient import TestClient as TC
        from app.main import app
        from .conftest import override_get_db
        from app.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        with TC(app) as anon:
            resp = anon.get(f"/api/vote/{poll['public_id']}/status")
            assert resp.status_code == 200
            assert resp.json()["already_voted"] is False

    def test_status_after_vote(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        opt_id = poll["options"][0]["id"]
        auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_id": opt_id}},
        )
        resp = auth_client.get(f"/api/vote/{poll['public_id']}/status")
        assert resp.status_code == 200
        assert resp.json()["already_voted"] is True


# --------------------------------------------------------------------------
# 投票送信
# --------------------------------------------------------------------------

class TestSubmitVote:
    def test_vote_plurality(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        opt_id = poll["options"][0]["id"]
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_id": opt_id}},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_duplicate_vote_rejected(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        opt_id = poll["options"][0]["id"]
        auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_id": opt_id}},
        )
        resp2 = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_id": opt_id}},
        )
        assert resp2.status_code == 409

    def test_vote_nonexistent_poll(self, client: TestClient):
        resp = client.post(
            "/api/vote/nonexistent-id",
            json={"vote_data": {"option_id": 1}},
        )
        assert resp.status_code == 404

    def test_vote_sets_voter_cookie(self, auth_client: TestClient):
        poll = _create_poll(auth_client)
        opt_id = poll["options"][0]["id"]
        # クッキーのないリクエスト（auth_client のクッキーをクリア）
        auth_client.cookies.clear()
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_id": opt_id}},
        )
        assert resp.status_code == 200
        assert "voter_id" in resp.cookies

    def test_vote_approval(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="approval")
        opt_ids = [o["id"] for o in poll["options"][:2]]
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"option_ids": opt_ids}},
        )
        assert resp.status_code == 200

    def test_vote_score(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="score")
        scores = {str(o["id"]): 3 for o in poll["options"]}
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"scores": scores}},
        )
        assert resp.status_code == 200

    def test_vote_majority_judgement(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="majority_judgement")
        grades = {str(o["id"]): "良い" for o in poll["options"]}
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"grades": grades}},
        )
        assert resp.status_code == 200

    def test_vote_ranking(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="borda")
        order = [o["id"] for o in poll["options"]]
        rankings = {str(oid): idx + 1 for idx, oid in enumerate(order)}
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"rankings": rankings}},
        )
        assert resp.status_code == 200

    def test_vote_quadratic(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="quadratic")
        votes = {str(o["id"]): 2 for o in poll["options"][:1]}
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"votes": votes}},
        )
        assert resp.status_code == 200

    def test_vote_negative(self, auth_client: TestClient):
        poll = _create_poll(auth_client, method="negative")
        votes = {str(poll["options"][0]["id"]): 1, str(poll["options"][1]["id"]): -1}
        resp = auth_client.post(
            f"/api/vote/{poll['public_id']}",
            json={"vote_data": {"votes": votes}},
        )
        assert resp.status_code == 200
