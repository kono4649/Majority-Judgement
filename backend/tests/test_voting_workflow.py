"""
業務フロー統合テスト

以下の業務フローを検証します:
1. ユーザーを登録する（誰でも登録可能）
2. 登録したアカウントでログインし、投票フォームを作成する
3. 不特定多数が投票する
4. 投票フォームを作成したアカウントのみが投票結果を確認する
"""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestVotingWorkflow:
    """業務フロー全体の統合テスト（順番に実行）"""

    # テスト間で状態を共有するクラス変数
    user_token: str = ""
    other_user_token: str = ""
    poll_id: str = ""
    poll_options: list = []
    poll_grades: list = []

    # ── STEP 1: ユーザーを登録する ──────────────────────────────────────────

    async def test_step1_register_user(self, client: AsyncClient):
        """STEP 1: 誰でもユーザー登録できること"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@test.com",
                "username": "testuser",
                "password": "UserPass123!",
            },
        )
        assert response.status_code == 201, (
            f"ユーザー登録に失敗: {response.text}"
        )
        data = response.json()
        assert data["email"] == "user@test.com"
        assert data["username"] == "testuser"

    async def test_step1_register_another_user(self, client: AsyncClient):
        """STEP 1: 別のユーザーも登録できること（投票結果確認テスト用）"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@test.com",
                "username": "otheruser",
                "password": "OtherPass123!",
            },
        )
        assert response.status_code == 201, (
            f"別ユーザーの登録に失敗: {response.text}"
        )

    async def test_step1_duplicate_email_rejected(self, client: AsyncClient):
        """STEP 1 (異常系): 重複メールアドレスでの登録が拒否されること"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@test.com",
                "username": "anotheruser",
                "password": "Pass123!",
            },
        )
        assert response.status_code == 400, "重複メールアドレスで登録できてしまった"

    # ── STEP 2: ログインして投票フォームを作成する ────────────────────────────

    async def test_step2_user_login(self, client: AsyncClient):
        """STEP 2a: ユーザーがログインできること"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "UserPass123!"},
        )
        assert response.status_code == 200, (
            f"ユーザーのログインに失敗: {response.text}"
        )
        data = response.json()
        assert "access_token" in data, "access_token がレスポンスに含まれていない"
        TestVotingWorkflow.user_token = data["access_token"]

    async def test_step2_wrong_password_fails(self, client: AsyncClient):
        """STEP 2 (異常系): 誤ったパスワードでのログインが拒否されること"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401, "誤ったパスワードでログインできてしまった"

    async def test_step2_other_user_login(self, client: AsyncClient):
        """STEP 2a: 別のユーザーもログインできること（後のテスト用）"""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "other@test.com", "password": "OtherPass123!"},
        )
        assert response.status_code == 200
        TestVotingWorkflow.other_user_token = response.json()["access_token"]

    async def test_step2_create_poll(self, client: AsyncClient):
        """STEP 2b: ログイン済みユーザーが投票フォームを作成できること"""
        assert TestVotingWorkflow.user_token, "STEP 2a が完了していない"
        response = await client.post(
            "/api/v1/polls",
            json={
                "title": "好きなプログラミング言語",
                "description": "あなたが最も好きなプログラミング言語を評価してください",
                "options": [
                    {"name": "Python"},
                    {"name": "TypeScript"},
                    {"name": "Rust"},
                ],
                "grades": [
                    {"label": "最高", "value": 5},
                    {"label": "良い", "value": 3},
                    {"label": "普通", "value": 1},
                ],
            },
            headers={"Authorization": f"Bearer {TestVotingWorkflow.user_token}"},
        )
        assert response.status_code == 201, (
            f"投票フォームの作成に失敗: {response.text}"
        )
        data = response.json()
        assert data["title"] == "好きなプログラミング言語"
        assert len(data["options"]) == 3
        assert len(data["grades"]) == 3
        assert data["is_open"] is True

        TestVotingWorkflow.poll_id = data["id"]
        TestVotingWorkflow.poll_options = data["options"]
        TestVotingWorkflow.poll_grades = data["grades"]

    async def test_step2_unauthenticated_cannot_create_poll(self, client: AsyncClient):
        """STEP 2 (異常系): 未認証では投票フォーム作成が拒否されること"""
        response = await client.post(
            "/api/v1/polls",
            json={
                "title": "テスト",
                "options": [{"name": "A"}, {"name": "B"}],
            },
            # Authorization ヘッダーなし
        )
        assert response.status_code == 401, "未認証で投票フォーム作成できてしまった"

    # ── STEP 3: 不特定多数が投票する ─────────────────────────────────────────

    async def test_step3_anonymous_vote_1(self, client: AsyncClient):
        """STEP 3a: 匿名ユーザー1が投票できること"""
        assert TestVotingWorkflow.poll_id, "STEP 2 が完了していない"
        options = TestVotingWorkflow.poll_options
        grades = TestVotingWorkflow.poll_grades
        votes = {opt["id"]: grades[0]["id"] for opt in options}
        votes[options[0]["id"]] = grades[0]["id"]  # Python -> 最高
        votes[options[1]["id"]] = grades[1]["id"]  # TypeScript -> 良い
        votes[options[2]["id"]] = grades[2]["id"]  # Rust -> 普通

        response = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={
                "votes": votes,
                "voter_token": str(uuid.uuid4()),
            },
            # 認証なし（匿名投票）
        )
        assert response.status_code == 201, (
            f"匿名投票1 に失敗: {response.text}"
        )
        assert "voter_token" in response.json()

    async def test_step3_anonymous_vote_2(self, client: AsyncClient):
        """STEP 3b: 匿名ユーザー2が投票できること"""
        options = TestVotingWorkflow.poll_options
        grades = TestVotingWorkflow.poll_grades
        votes = {
            options[0]["id"]: grades[2]["id"],  # Python -> 普通
            options[1]["id"]: grades[0]["id"],  # TypeScript -> 最高
            options[2]["id"]: grades[0]["id"],  # Rust -> 最高
        }

        response = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={
                "votes": votes,
                "voter_token": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 201, (
            f"匿名投票2 に失敗: {response.text}"
        )

    async def test_step3_authenticated_user_can_vote(self, client: AsyncClient):
        """STEP 3c: 認証済みユーザー（別ユーザー）が投票できること"""
        options = TestVotingWorkflow.poll_options
        grades = TestVotingWorkflow.poll_grades
        votes = {
            options[0]["id"]: grades[1]["id"],  # Python -> 良い
            options[1]["id"]: grades[1]["id"],  # TypeScript -> 良い
            options[2]["id"]: grades[0]["id"],  # Rust -> 最高
        }

        response = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={"votes": votes},
            headers={"Authorization": f"Bearer {TestVotingWorkflow.other_user_token}"},
        )
        assert response.status_code == 201, (
            f"認証済みユーザーの投票に失敗: {response.text}"
        )

    async def test_step3_duplicate_vote_rejected(self, client: AsyncClient):
        """STEP 3 (異常系): 同じユーザーが2回投票できないこと"""
        options = TestVotingWorkflow.poll_options
        grades = TestVotingWorkflow.poll_grades
        votes = {opt["id"]: grades[0]["id"] for opt in options}

        response = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={"votes": votes},
            headers={"Authorization": f"Bearer {TestVotingWorkflow.other_user_token}"},
        )
        assert response.status_code == 400, "同じユーザーが2回投票できてしまった"
        assert "既にこの投票に参加しています" in response.json()["detail"]

    async def test_step3_duplicate_anonymous_token_rejected(self, client: AsyncClient):
        """STEP 3 (異常系): 同じ匿名トークンで2回投票できないこと"""
        options = TestVotingWorkflow.poll_options
        grades = TestVotingWorkflow.poll_grades
        votes = {opt["id"]: grades[0]["id"] for opt in options}
        token = str(uuid.uuid4())

        r1 = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={"votes": votes, "voter_token": token},
        )
        assert r1.status_code == 201

        r2 = await client.post(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/vote",
            json={"votes": votes, "voter_token": token},
        )
        assert r2.status_code == 400, "同じ匿名トークンで2回投票できてしまった"

    # ── STEP 4: 投票フォームを作成したアカウントのみが投票結果を確認する ───────

    async def test_step4_creator_can_view_results(self, client: AsyncClient):
        """STEP 4a: 投票フォームの作成者が結果を確認できること"""
        assert TestVotingWorkflow.user_token, "STEP 2 が完了していない"
        response = await client.get(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/results",
            headers={"Authorization": f"Bearer {TestVotingWorkflow.user_token}"},
        )
        assert response.status_code == 200, (
            f"投票フォーム作成者が結果を確認できない: {response.text}"
        )
        data = response.json()
        assert data["poll_id"] == TestVotingWorkflow.poll_id
        assert "results" in data
        assert len(data["results"]) == 3, "結果に3つの選択肢がない"
        for result in data["results"]:
            assert "rank" in result
            assert "median_grade" in result
            assert result["total_votes"] > 0, f"{result['name']} の投票数が0"

    async def test_step4_non_creator_cannot_view_results(self, client: AsyncClient):
        """
        STEP 4b【重要】: 投票フォームを作成していない別のユーザーが結果を
        確認できないこと（403 Forbidden が返ること）
        """
        assert TestVotingWorkflow.other_user_token, "other_user_token が未設定"
        response = await client.get(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/results",
            headers={"Authorization": f"Bearer {TestVotingWorkflow.other_user_token}"},
        )
        assert response.status_code == 403, (
            f"【バグ】作成者以外のユーザーが投票結果を閲覧できてしまいました。"
            f"ステータスコード: {response.status_code}, レスポンス: {response.text}"
        )

    async def test_step4_unauthenticated_cannot_view_results(self, client: AsyncClient):
        """STEP 4c (異常系): 未認証では結果確認が拒否されること"""
        response = await client.get(
            f"/api/v1/polls/{TestVotingWorkflow.poll_id}/results",
            # Authorization ヘッダーなし
        )
        assert response.status_code == 401, "未認証で投票結果を閲覧できてしまった"
