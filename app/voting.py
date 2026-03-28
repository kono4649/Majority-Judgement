"""
9種類の投票方式の集計アルゴリズム

各関数のシグネチャ:
  calculate_*(votes: list[dict], options: list[dict]) -> dict
  votes: [{"vote_data": {...}}, ...]
  options: [{"id": int, "text": str, "order_index": int}, ...]

返り値:
  {
      "ranked": [{"id": int, "text": str, "score": ..., "rank": int}, ...],
      "winner_id": int | None,
      "details": {...}  # 方式固有の詳細情報
  }
"""

from collections import defaultdict
from typing import Any


def _make_result(options_map: dict, scores: dict, details: dict = None) -> dict:
    """共通の結果フォーマットを生成"""
    ranked = sorted(
        [
            {"id": oid, "text": options_map[oid], "score": scores.get(oid, 0)}
            for oid in options_map
        ],
        key=lambda x: x["score"],
        reverse=True,
    )
    for i, item in enumerate(ranked):
        item["rank"] = i + 1
    winner_id = ranked[0]["id"] if ranked else None
    return {"ranked": ranked, "winner_id": winner_id, "details": details or {}}


# ---------------------------------------------------------------------------
# 1. 単記投票（Plurality）
# ---------------------------------------------------------------------------
def calculate_plurality(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    counts = defaultdict(int)
    for v in votes:
        oid = v["vote_data"].get("option_id")
        if oid is not None:
            counts[int(oid)] += 1
    scores = {oid: counts[oid] for oid in options_map}
    return _make_result(options_map, scores, {"total_votes": len(votes)})


# ---------------------------------------------------------------------------
# 2. 承認投票（Approval Voting）
# ---------------------------------------------------------------------------
def calculate_approval(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    counts = defaultdict(int)
    for v in votes:
        for oid in v["vote_data"].get("option_ids", []):
            counts[int(oid)] += 1
    scores = {oid: counts[oid] for oid in options_map}
    return _make_result(options_map, scores, {"total_voters": len(votes)})


# ---------------------------------------------------------------------------
# 3. ボルダ・カウント（Borda Count）
# ---------------------------------------------------------------------------
def calculate_borda(votes: list, options: list) -> dict:
    """1位 = n-1点, 2位 = n-2点, ..., 最下位 = 0点"""
    options_map = {o["id"]: o["text"] for o in options}
    n = len(options)
    scores = defaultdict(int)
    for v in votes:
        rankings = v["vote_data"].get("rankings", {})  # {"opt_id": rank(1始まり)}
        for oid_str, rank in rankings.items():
            oid = int(oid_str)
            if oid in options_map:
                scores[oid] += n - int(rank)
    final_scores = {oid: scores[oid] for oid in options_map}
    return _make_result(options_map, final_scores, {"max_score": (n - 1) * len(votes)})


# ---------------------------------------------------------------------------
# 4. 代替投票（IRV: Instant Runoff Voting）
# ---------------------------------------------------------------------------
def calculate_irv(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    remaining = set(options_map.keys())
    all_orders = []
    for v in votes:
        order = [int(x) for x in v["vote_data"].get("order", [])]
        all_orders.append(order)

    rounds = []
    eliminated = []

    while len(remaining) > 1:
        counts = defaultdict(int)
        for order in all_orders:
            for oid in order:
                if oid in remaining:
                    counts[oid] += 1
                    break

        total = sum(counts.values())
        round_info = {
            "counts": {oid: counts[oid] for oid in remaining},
            "total": total,
        }
        rounds.append(round_info)

        # 過半数チェック
        for oid in remaining:
            if total > 0 and counts[oid] > total / 2:
                return {
                    "ranked": [
                        {"id": oid, "text": options_map[oid], "score": counts[oid], "rank": 1}
                    ],
                    "winner_id": oid,
                    "details": {"rounds": rounds, "eliminated": eliminated},
                }

        # 最低票候補を除外
        if not counts:
            break
        min_count = min(counts[oid] for oid in remaining)
        to_eliminate = [oid for oid in remaining if counts[oid] == min_count]
        for oid in to_eliminate:
            remaining.discard(oid)
            eliminated.append({"id": oid, "text": options_map[oid]})

    winner_id = next(iter(remaining)) if remaining else None
    ranked = []
    if winner_id:
        ranked = [{"id": winner_id, "text": options_map[winner_id], "score": 0, "rank": 1}]
    return {"ranked": ranked, "winner_id": winner_id, "details": {"rounds": rounds, "eliminated": eliminated}}


# ---------------------------------------------------------------------------
# 5. コンドルセ方式（Condorcet Method）
# ---------------------------------------------------------------------------
def calculate_condorcet(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    opt_list = list(options_map.keys())
    # pairwise[a][b] = Aを好む投票者数
    pairwise = {a: {b: 0 for b in opt_list} for a in opt_list}

    for v in votes:
        order = [int(x) for x in v["vote_data"].get("order", [])]
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                if a in pairwise and b in pairwise[a]:
                    pairwise[a][b] += 1

    # コンドルセ勝者を探す
    win_counts = {}
    for a in opt_list:
        wins = sum(1 for b in opt_list if a != b and pairwise[a][b] > pairwise[b][a])
        win_counts[a] = wins

    condorcet_winner = None
    for a in opt_list:
        if win_counts[a] == len(opt_list) - 1:
            condorcet_winner = a
            break

    scores = {oid: win_counts[oid] for oid in options_map}
    result = _make_result(options_map, scores)
    result["winner_id"] = condorcet_winner
    result["details"] = {
        "pairwise": {str(a): {str(b): pairwise[a][b] for b in opt_list} for a in opt_list},
        "condorcet_winner": condorcet_winner,
        "has_cycle": condorcet_winner is None and len(votes) > 0,
    }
    return result


# ---------------------------------------------------------------------------
# 6. スコア投票（Score Voting）
# ---------------------------------------------------------------------------
def calculate_score(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    totals = defaultdict(float)
    counts = defaultdict(int)
    for v in votes:
        for oid_str, score in v["vote_data"].get("scores", {}).items():
            oid = int(oid_str)
            if oid in options_map:
                totals[oid] += float(score)
                counts[oid] += 1

    averages = {}
    for oid in options_map:
        averages[oid] = round(totals[oid] / counts[oid], 2) if counts[oid] > 0 else 0.0

    result = _make_result(options_map, averages)
    result["details"] = {
        "averages": averages,
        "totals": dict(totals),
        "vote_counts": dict(counts),
    }
    return result


# ---------------------------------------------------------------------------
# 7. マジョリティ・ジャッジメント（Majority Judgement）
# ---------------------------------------------------------------------------
MJ_GRADE_LABELS = ["拒否", "不良", "許容", "良い", "とても良い", "優秀"]
MJ_GRADE_VALUES = {label: i for i, label in enumerate(MJ_GRADE_LABELS)}


def _mj_median_with_tiebreak(grade_list: list) -> float:
    """
    MJの中央値評価を計算（タイブレーク付き）
    タイが続く場合はスコアに±0.1を加算してランクを安定化
    """
    if not grade_list:
        return -1.0
    sorted_grades = sorted(grade_list)
    n = len(sorted_grades)
    # 中央値インデックス
    mid = n // 2
    base = float(sorted_grades[mid])
    # タイブレーク: 中央値より上の割合 vs 下の割合
    upper = sum(1 for g in sorted_grades if g > sorted_grades[mid])
    lower = sum(1 for g in sorted_grades if g < sorted_grades[mid])
    if upper > lower:
        base += 0.1
    elif lower > upper:
        base -= 0.1
    return base


def calculate_majority_judgement(votes: list, options: list) -> dict:
    options_map = {o["id"]: o["text"] for o in options}
    grade_lists: dict[int, list] = {oid: [] for oid in options_map}

    for v in votes:
        for oid_str, grade in v["vote_data"].get("grades", {}).items():
            oid = int(oid_str)
            if oid in grade_lists:
                grade_val = MJ_GRADE_VALUES.get(grade, -1)
                if grade_val >= 0:
                    grade_lists[oid].append(grade_val)

    medians = {}
    grade_distributions = {}
    for oid in options_map:
        medians[oid] = _mj_median_with_tiebreak(grade_lists[oid])
        dist = defaultdict(int)
        for g in grade_lists[oid]:
            dist[MJ_GRADE_LABELS[g]] += 1
        grade_distributions[oid] = dict(dist)

    result = _make_result(options_map, medians)
    result["details"] = {
        "grade_distributions": {str(k): v for k, v in grade_distributions.items()},
        "median_labels": {
            str(oid): MJ_GRADE_LABELS[int(medians[oid])] if medians[oid] >= 0 else "未評価"
            for oid in options_map
        },
    }
    return result


# ---------------------------------------------------------------------------
# 8. クアドラティック・ボーティング（Quadratic Voting）
# ---------------------------------------------------------------------------
def calculate_quadratic(votes: list, options: list) -> dict:
    """
    各投票者がクレジット予算内で票を配分。コスト = 票数²
    投票データ: {"votes": {"opt_id": num_votes, ...}}  (正の整数)
    """
    options_map = {o["id"]: o["text"] for o in options}
    totals = defaultdict(int)
    for v in votes:
        for oid_str, num_votes in v["vote_data"].get("votes", {}).items():
            oid = int(oid_str)
            if oid in options_map:
                totals[oid] += int(num_votes)

    scores = {oid: totals[oid] for oid in options_map}
    return _make_result(options_map, scores, {"total_voters": len(votes)})


# ---------------------------------------------------------------------------
# 9. 負の投票（Negative Voting）
# ---------------------------------------------------------------------------
def calculate_negative(votes: list, options: list) -> dict:
    """
    各投票者が各候補に +1 または -1 を投じられる。
    投票データ: {"votes": {"opt_id": 1|-1, ...}}
    """
    options_map = {o["id"]: o["text"] for o in options}
    totals = defaultdict(int)
    positives = defaultdict(int)
    negatives = defaultdict(int)

    for v in votes:
        for oid_str, val in v["vote_data"].get("votes", {}).items():
            oid = int(oid_str)
            val = int(val)
            if oid in options_map:
                totals[oid] += val
                if val > 0:
                    positives[oid] += 1
                elif val < 0:
                    negatives[oid] += 1

    scores = {oid: totals[oid] for oid in options_map}
    result = _make_result(options_map, scores)
    result["details"] = {
        "positives": {str(k): positives[k] for k in options_map},
        "negatives": {str(k): negatives[k] for k in options_map},
    }
    return result


# ---------------------------------------------------------------------------
# ディスパッチャ
# ---------------------------------------------------------------------------
CALCULATORS = {
    "plurality": calculate_plurality,
    "approval": calculate_approval,
    "borda": calculate_borda,
    "irv": calculate_irv,
    "condorcet": calculate_condorcet,
    "score": calculate_score,
    "majority_judgement": calculate_majority_judgement,
    "quadratic": calculate_quadratic,
    "negative": calculate_negative,
}


def calculate_results(voting_method: str, votes: list, options: list) -> dict:
    calculator = CALCULATORS.get(voting_method)
    if calculator is None:
        raise ValueError(f"Unknown voting method: {voting_method}")
    return calculator(votes, options)


# ---------------------------------------------------------------------------
# CSV生成
# ---------------------------------------------------------------------------
import csv
import io


def votes_to_csv(poll, votes: list, options: list) -> str:
    """投票データをCSV文字列に変換"""
    output = io.StringIO()
    writer = csv.writer(output)

    opt_texts = {str(o["id"]): o["text"] for o in options}
    opt_ids = [str(o["id"]) for o in options]

    method = poll.voting_method

    # ヘッダー
    if method in ("plurality",):
        header = ["投票番号", "投票日時", "選択肢"]
    elif method in ("approval", "negative", "quadratic", "score"):
        header = ["投票番号", "投票日時"] + [opt_texts.get(oid, oid) for oid in opt_ids]
    elif method in ("borda", "irv", "condorcet"):
        header = ["投票番号", "投票日時"] + [opt_texts.get(oid, oid) for oid in opt_ids]
    elif method == "majority_judgement":
        header = ["投票番号", "投票日時"] + [opt_texts.get(oid, oid) for oid in opt_ids]
    else:
        header = ["投票番号", "投票日時", "投票データ"]

    writer.writerow(header)

    for i, v in enumerate(votes, 1):
        ts = v.get("created_at", "")
        data = v.get("vote_data", {})
        row = [i, ts]

        if method == "plurality":
            selected_id = str(data.get("option_id", ""))
            row.append(opt_texts.get(selected_id, selected_id))

        elif method == "approval":
            selected = [str(x) for x in data.get("option_ids", [])]
            row += ["1" if oid in selected else "0" for oid in opt_ids]

        elif method in ("borda", "irv", "condorcet"):
            rankings = {}
            if "rankings" in data:
                rankings = {str(k): str(v_r) for k, v_r in data["rankings"].items()}
            elif "order" in data:
                rankings = {str(oid): str(idx + 1) for idx, oid in enumerate(data["order"])}
            row += [rankings.get(oid, "") for oid in opt_ids]

        elif method == "score":
            scores_d = {str(k): str(v_s) for k, v_s in data.get("scores", {}).items()}
            row += [scores_d.get(oid, "") for oid in opt_ids]

        elif method == "majority_judgement":
            grades_d = {str(k): str(g) for k, g in data.get("grades", {}).items()}
            row += [grades_d.get(oid, "") for oid in opt_ids]

        elif method in ("quadratic", "negative"):
            votes_d = {str(k): str(v_v) for k, v_v in data.get("votes", {}).items()}
            row += [votes_d.get(oid, "0") for oid in opt_ids]

        else:
            row.append(str(data))

        writer.writerow(row)

    return output.getvalue()
