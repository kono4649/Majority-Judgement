"""
9種類の投票アルゴリズム（app/voting.py）のユニットテスト

各テストは HTTP を使わず関数を直接呼び出す。
"""
import pytest
from app.voting import (
    calculate_approval,
    calculate_borda,
    calculate_condorcet,
    calculate_irv,
    calculate_majority_judgement,
    calculate_negative,
    calculate_plurality,
    calculate_quadratic,
    calculate_results,
    calculate_score,
)

# --------------------------------------------------------------------------
# テスト用ヘルパー
# --------------------------------------------------------------------------

def make_options(*texts):
    return [{"id": i + 1, "text": t, "order_index": i} for i, t in enumerate(texts)]


def make_vote(vote_data: dict):
    return {"vote_data": vote_data}


# --------------------------------------------------------------------------
# 1. 単記投票（Plurality）
# --------------------------------------------------------------------------

class TestPlurality:
    def test_basic_winner(self):
        opts = make_options("A", "B", "C")
        votes = [
            make_vote({"option_id": 1}),
            make_vote({"option_id": 1}),
            make_vote({"option_id": 2}),
        ]
        result = calculate_plurality(votes, opts)
        assert result["winner_id"] == 1
        assert result["ranked"][0]["id"] == 1
        assert result["ranked"][0]["score"] == 2

    def test_no_votes(self):
        opts = make_options("A", "B")
        result = calculate_plurality([], opts)
        assert result["ranked"][0]["score"] == 0

    def test_all_ranks_assigned(self):
        opts = make_options("A", "B", "C")
        votes = [make_vote({"option_id": 1}), make_vote({"option_id": 2})]
        result = calculate_plurality(votes, opts)
        ranks = {r["id"]: r["rank"] for r in result["ranked"]}
        assert ranks[1] == 1
        assert ranks[2] == 2
        assert ranks[3] == 3


# --------------------------------------------------------------------------
# 2. 承認投票（Approval）
# --------------------------------------------------------------------------

class TestApproval:
    def test_basic_winner(self):
        opts = make_options("A", "B", "C")
        votes = [
            make_vote({"option_ids": [1, 2]}),
            make_vote({"option_ids": [1, 3]}),
            make_vote({"option_ids": [2]}),
        ]
        result = calculate_approval(votes, opts)
        assert result["winner_id"] == 1
        assert result["ranked"][0]["score"] == 2

    def test_empty_votes(self):
        opts = make_options("A", "B")
        result = calculate_approval([], opts)
        assert all(r["score"] == 0 for r in result["ranked"])


# --------------------------------------------------------------------------
# 3. ボルダ・カウント（Borda）
# --------------------------------------------------------------------------

class TestBorda:
    def test_basic(self):
        opts = make_options("A", "B", "C")
        # A>B>C が2票、B>A>C が1票
        votes = [
            make_vote({"rankings": {"1": 1, "2": 2, "3": 3}}),
            make_vote({"rankings": {"1": 1, "2": 2, "3": 3}}),
            make_vote({"rankings": {"2": 1, "1": 2, "3": 3}}),
        ]
        result = calculate_borda(votes, opts)
        # A: (3-1)*2 + (3-2)*1 = 4+1 = 5
        # B: (3-2)*2 + (3-1)*1 = 2+2 = 4
        # C: 0
        assert result["winner_id"] == 1
        assert result["ranked"][0]["score"] == 5

    def test_max_score_detail(self):
        opts = make_options("A", "B")
        votes = [make_vote({"rankings": {"1": 1, "2": 2}})]
        result = calculate_borda(votes, opts)
        assert result["details"]["max_score"] == (2 - 1) * 1


# --------------------------------------------------------------------------
# 4. 代替投票（IRV）
# --------------------------------------------------------------------------

class TestIRV:
    def test_majority_first_round(self):
        opts = make_options("A", "B", "C")
        # A が過半数
        votes = [
            make_vote({"order": [1, 2, 3]}),
            make_vote({"order": [1, 3, 2]}),
            make_vote({"order": [2, 1, 3]}),
        ]
        result = calculate_irv(votes, opts)
        assert result["winner_id"] == 1

    def test_elimination_leads_to_winner(self):
        opts = make_options("A", "B", "C")
        # C が最下位で脱落 → A が過半数
        votes = [
            make_vote({"order": [1, 2, 3]}),
            make_vote({"order": [1, 3, 2]}),
            make_vote({"order": [2, 1, 3]}),
            make_vote({"order": [3, 2, 1]}),
        ]
        result = calculate_irv(votes, opts)
        assert result["winner_id"] is not None
        assert "rounds" in result["details"]

    def test_no_votes(self):
        opts = make_options("A", "B")
        result = calculate_irv([], opts)
        assert result["winner_id"] is None or result["ranked"] == []


# --------------------------------------------------------------------------
# 5. コンドルセ（Condorcet）
# --------------------------------------------------------------------------

class TestCondorcet:
    def test_condorcet_winner(self):
        opts = make_options("A", "B", "C")
        # A が全ての一対比較に勝つ
        votes = [
            make_vote({"order": [1, 2, 3]}),
            make_vote({"order": [1, 3, 2]}),
            make_vote({"order": [1, 2, 3]}),
        ]
        result = calculate_condorcet(votes, opts)
        assert result["winner_id"] == 1
        assert result["details"]["has_cycle"] is False

    def test_no_condorcet_winner_cycle(self):
        opts = make_options("A", "B", "C")
        # A>B>C, B>C>A, C>A>B → 循環
        votes = [
            make_vote({"order": [1, 2, 3]}),
            make_vote({"order": [2, 3, 1]}),
            make_vote({"order": [3, 1, 2]}),
        ]
        result = calculate_condorcet(votes, opts)
        assert result["winner_id"] is None
        assert result["details"]["has_cycle"] is True

    def test_pairwise_matrix_present(self):
        opts = make_options("A", "B")
        votes = [make_vote({"order": [1, 2]})]
        result = calculate_condorcet(votes, opts)
        assert "pairwise" in result["details"]


# --------------------------------------------------------------------------
# 6. スコア投票（Score）
# --------------------------------------------------------------------------

class TestScore:
    def test_average_score(self):
        opts = make_options("A", "B")
        votes = [
            make_vote({"scores": {"1": 5, "2": 3}}),
            make_vote({"scores": {"1": 3, "2": 4}}),
        ]
        result = calculate_score(votes, opts)
        assert result["winner_id"] == 1
        assert result["ranked"][0]["score"] == 4.0

    def test_zero_votes(self):
        opts = make_options("A", "B")
        result = calculate_score([], opts)
        assert all(r["score"] == 0.0 for r in result["ranked"])


# --------------------------------------------------------------------------
# 7. マジョリティ・ジャッジメント（MJ）
# --------------------------------------------------------------------------

class TestMajorityJudgement:
    def test_median_grade(self):
        opts = make_options("A", "B")
        # A: [優秀, 優秀, 良い] → 中央値 優秀(5)
        # B: [拒否, 許容, 良い] → 中央値 許容(2)
        votes = [
            make_vote({"grades": {"1": "優秀", "2": "拒否"}}),
            make_vote({"grades": {"1": "優秀", "2": "許容"}}),
            make_vote({"grades": {"1": "良い", "2": "良い"}}),
        ]
        result = calculate_majority_judgement(votes, opts)
        assert result["winner_id"] == 1

    def test_grade_distribution_in_details(self):
        opts = make_options("A")
        votes = [
            make_vote({"grades": {"1": "良い"}}),
            make_vote({"grades": {"1": "優秀"}}),
        ]
        result = calculate_majority_judgement(votes, opts)
        dist = result["details"]["grade_distributions"]["1"]
        assert dist.get("良い") == 1
        assert dist.get("優秀") == 1

    def test_no_votes(self):
        opts = make_options("A")
        result = calculate_majority_judgement([], opts)
        assert result["details"]["median_labels"]["1"] == "未評価"


# --------------------------------------------------------------------------
# 8. クアドラティック・ボーティング（Quadratic）
# --------------------------------------------------------------------------

class TestQuadratic:
    def test_basic(self):
        opts = make_options("A", "B")
        votes = [
            make_vote({"votes": {"1": 3, "2": 1}}),
            make_vote({"votes": {"1": 2, "2": 2}}),
        ]
        result = calculate_quadratic(votes, opts)
        # A: 3+2=5, B: 1+2=3
        assert result["winner_id"] == 1
        assert result["ranked"][0]["score"] == 5

    def test_zero_votes(self):
        opts = make_options("A", "B")
        result = calculate_quadratic([], opts)
        assert all(r["score"] == 0 for r in result["ranked"])


# --------------------------------------------------------------------------
# 9. 負の投票（Negative）
# --------------------------------------------------------------------------

class TestNegative:
    def test_basic(self):
        opts = make_options("A", "B", "C")
        votes = [
            make_vote({"votes": {"1": 1, "2": -1, "3": 0}}),
            make_vote({"votes": {"1": 1, "2": 1, "3": -1}}),
        ]
        result = calculate_negative(votes, opts)
        # A: +2, B: 0, C: -1
        assert result["winner_id"] == 1
        assert result["ranked"][0]["score"] == 2

    def test_details_contain_positives_negatives(self):
        opts = make_options("A")
        votes = [
            make_vote({"votes": {"1": 1}}),
            make_vote({"votes": {"1": -1}}),
        ]
        result = calculate_negative(votes, opts)
        assert result["details"]["positives"]["1"] == 1
        assert result["details"]["negatives"]["1"] == 1


# --------------------------------------------------------------------------
# ディスパッチャ
# --------------------------------------------------------------------------

class TestDispatcher:
    def test_all_methods_callable(self):
        methods = [
            "plurality", "approval", "borda", "irv", "condorcet",
            "score", "majority_judgement", "quadratic", "negative",
        ]
        opts = make_options("X", "Y")
        for m in methods:
            result = calculate_results(m, [], opts)
            assert "ranked" in result
            assert "winner_id" in result

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            calculate_results("unknown_method", [], make_options("X"))
