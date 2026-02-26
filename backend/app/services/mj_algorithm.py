"""
Majority Judgement ranking algorithm.

Steps:
1. Compute the median grade for each option (lower median for even count).
2. Tiebreak: repeatedly remove one vote equal to the current median and
   recompute until a difference emerges.
"""
from dataclasses import dataclass, field


@dataclass
class OptionScore:
    option_id: str
    name: str
    grades: list[int] = field(default_factory=list)  # sorted list of grade values


def _lower_median(grades: list[int]) -> int:
    """Return the lower median of a sorted list."""
    n = len(grades)
    if n == 0:
        return -1
    return grades[(n - 1) // 2]


def _mj_rank_key(grades: list[int]) -> tuple:
    """
    Produce a comparison key for Majority Judgement tiebreaking.
    Returns a tuple of successive medians obtained by the sequential-removal method.
    Higher is better.
    """
    remaining = sorted(grades)
    key = []
    while remaining:
        m = _lower_median(remaining)
        key.append(m)
        # Remove one occurrence of the median
        idx = remaining.index(m)
        remaining.pop(idx)
    return tuple(key)


def compute_rankings(options: list[OptionScore]) -> list[tuple[int, OptionScore]]:
    """
    Return a list of (rank, OptionScore) sorted by MJ rank (best first).
    """
    ranked = sorted(options, key=lambda o: _mj_rank_key(o.grades), reverse=True)

    results: list[tuple[int, OptionScore]] = []
    rank = 1
    for i, opt in enumerate(ranked):
        if i > 0:
            prev = ranked[i - 1]
            if _mj_rank_key(opt.grades) < _mj_rank_key(prev.grades):
                rank = i + 1
        results.append((rank, opt))
    return results
