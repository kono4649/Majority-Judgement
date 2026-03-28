"""
投票フォーム CRUD・結果 API のテスト

カバー範囲:
- POST   /api/polls/       作成
- GET    /api/polls/       一覧
- GET    /api/polls/{id}   取得
- PUT    /api/polls/{id}   更新
- DELETE /api/polls/{id}   削除
- GET    /api/polls/{id}/results
- GET    /api/polls/{id}/results/csv
"""
from fastapi.testclient import TestClient


POLL_BASE = {
    "title": "テスト投票",
    "description": "説明文",
    "voting_method": "plurality",
    "options": ["選択肢A", "選択肢B", "選択肢C"],
    "method_settings": {},
    "start_time": None,
    "end_time": None,
}


def create_poll(client: TestClient, overrides: dict = None) -> dict:
    body = {**POLL_BASE, **(overrides or {})}
    resp = client.post("/api/polls/", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------
# 作成
# --------------------------------------------------------------------------

class TestCreatePoll:
    def test_create_success(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        assert poll["title"] == "テスト投票"
        assert poll["voting_method"] == "plurality"
        assert len(poll["options"]) == 3

    def test_create_requires_auth(self, client: TestClient):
        resp = client.post("/api/polls/", json=POLL_BASE)
        assert resp.status_code == 401

    def test_create_too_few_options(self, auth_client: TestClient):
        resp = auth_client.post("/api/polls/", json={**POLL_BASE, "options": ["1つだけ"]})
        assert resp.status_code == 422

    def test_create_invalid_method(self, auth_client: TestClient):
        resp = auth_client.post("/api/polls/", json={**POLL_BASE, "voting_method": "unknown"})
        assert resp.status_code == 422

    def test_create_all_methods(self, auth_client: TestClient):
        methods = [
            "plurality", "approval", "borda", "irv", "condorcet",
            "score", "majority_judgement", "quadratic", "negative",
        ]
        for method in methods:
            poll = create_poll(auth_client, {"voting_method": method})
            assert poll["voting_method"] == method


# --------------------------------------------------------------------------
# 一覧・取得
# --------------------------------------------------------------------------

class TestGetPolls:
    def test_list_polls(self, auth_client: TestClient):
        create_poll(auth_client)
        create_poll(auth_client, {"title": "2つ目"})
        resp = auth_client.get("/api/polls/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_requires_auth(self, client: TestClient):
        resp = client.get("/api/polls/")
        assert resp.status_code == 401

    def test_get_poll(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        resp = auth_client.get(f"/api/polls/{poll['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == poll["id"]

    def test_get_poll_not_found(self, auth_client: TestClient):
        resp = auth_client.get("/api/polls/9999")
        assert resp.status_code == 404

    def test_get_poll_other_user(self, client: TestClient):
        from .conftest import login, register_and_activate

        # ユーザー1でポール作成
        register_and_activate(client, "user1@example.com", "Test1234!")
        login(client, "user1@example.com", "Test1234!")
        poll = create_poll(client)

        # ユーザー2でログイン
        register_and_activate(client, "user2@example.com", "Test1234!")
        login(client, "user2@example.com", "Test1234!")

        resp = client.get(f"/api/polls/{poll['id']}")
        assert resp.status_code == 403


# --------------------------------------------------------------------------
# 更新
# --------------------------------------------------------------------------

class TestUpdatePoll:
    def test_update_poll(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        resp = auth_client.put(
            f"/api/polls/{poll['id']}",
            json={
                "title": "変更後タイトル",
                "description": "",
                "options": ["新A", "新B"],
                "method_settings": {},
                "start_time": None,
                "end_time": None,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "変更後タイトル"

    def test_update_requires_auth(self, client: TestClient):
        body = {
            "title": "X",
            "description": "",
            "options": ["A", "B"],
            "method_settings": {},
            "start_time": None,
            "end_time": None,
        }
        resp = client.put("/api/polls/1", json=body)
        assert resp.status_code == 401

    def test_update_too_few_options(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        resp = auth_client.put(
            f"/api/polls/{poll['id']}",
            json={
                "title": "X",
                "description": "",
                "options": ["1つ"],
                "method_settings": {},
                "start_time": None,
                "end_time": None,
            },
        )
        assert resp.status_code == 422


# --------------------------------------------------------------------------
# 削除
# --------------------------------------------------------------------------

class TestDeletePoll:
    def test_delete_poll(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        resp = auth_client.delete(f"/api/polls/{poll['id']}")
        assert resp.status_code == 200
        resp2 = auth_client.get(f"/api/polls/{poll['id']}")
        assert resp2.status_code == 404

    def test_delete_requires_auth(self, client: TestClient):
        resp = client.delete("/api/polls/1")
        assert resp.status_code == 401


# --------------------------------------------------------------------------
# 結果・CSV
# --------------------------------------------------------------------------

class TestPollResults:
    def test_results_no_votes(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        resp = auth_client.get(f"/api/polls/{poll['id']}/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_votes"] == 0
        assert data["result"] is None

    def test_results_with_votes(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        public_id = poll["public_id"]
        opt_id = poll["options"][0]["id"]

        # 匿名投票を1票入れる
        auth_client.post(
            f"/api/vote/{public_id}",
            json={"vote_data": {"option_id": opt_id}},
        )

        resp = auth_client.get(f"/api/polls/{poll['id']}/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_votes"] == 1
        assert data["result"] is not None

    def test_csv_download(self, auth_client: TestClient):
        poll = create_poll(auth_client)
        public_id = poll["public_id"]
        opt_id = poll["options"][0]["id"]
        auth_client.post(
            f"/api/vote/{public_id}",
            json={"vote_data": {"option_id": opt_id}},
        )

        resp = auth_client.get(f"/api/polls/{poll['id']}/results/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "選択肢A" in resp.text or "選択肢B" in resp.text or "選択肢C" in resp.text

    def test_results_requires_auth(self, client: TestClient):
        resp = client.get("/api/polls/1/results")
        assert resp.status_code == 401
