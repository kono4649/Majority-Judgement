import uuid
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.poll import Poll, Option, Grade, Vote
from app.models.user import User
from app.schemas.poll import (
    PollCreate,
    PollResponse,
    VoteInput,
    PollResults,
    OptionResult,
    GradeDistribution,
    GradeResponse,
)
from app.services.mj_algorithm import OptionScore, compute_rankings, _lower_median

router = APIRouter(prefix="/polls", tags=["polls"])


@router.post("", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
async def create_poll(
    body: PollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = Poll(
        id=str(uuid.uuid4()),
        title=body.title,
        description=body.description,
        creator_id=current_user.id,
        closes_at=body.closes_at,
    )
    db.add(poll)
    await db.flush()

    for i, opt_in in enumerate(body.options):
        option = Option(
            id=str(uuid.uuid4()),
            poll_id=poll.id,
            name=opt_in.name,
            display_order=i,
        )
        db.add(option)

    for grade_in in body.grades:
        grade = Grade(
            id=str(uuid.uuid4()),
            poll_id=poll.id,
            label=grade_in.label,
            value=grade_in.value,
        )
        db.add(grade)

    await db.commit()

    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .where(Poll.id == poll.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[PollResponse])
async def list_polls(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .order_by(Poll.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(
    poll_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="投票が見つかりません")
    return poll


@router.post("/{poll_id}/vote", status_code=status.HTTP_201_CREATED)
async def submit_vote(
    poll_id: str,
    body: VoteInput,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="投票が見つかりません")
    if not poll.is_open:
        raise HTTPException(status_code=400, detail="この投票は終了しています")

    option_ids = {o.id for o in poll.options}
    grade_ids = {g.id for g in poll.grades}

    # Validate submitted votes
    for option_id, grade_id in body.votes.items():
        if option_id not in option_ids:
            raise HTTPException(status_code=400, detail=f"無効な選択肢ID: {option_id}")
        if grade_id not in grade_ids:
            raise HTTPException(status_code=400, detail=f"無効な評価ID: {grade_id}")

    # Prevent duplicate voting (same user or same anonymous token)
    if current_user:
        existing = await db.execute(
            select(Vote).where(Vote.poll_id == poll_id, Vote.user_id == current_user.id)
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="既にこの投票に参加しています")
    elif body.voter_token:
        existing = await db.execute(
            select(Vote).where(Vote.poll_id == poll_id, Vote.voter_token == body.voter_token)
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="既にこの投票に参加しています")

    voter_token = body.voter_token or str(uuid.uuid4())

    for option_id, grade_id in body.votes.items():
        vote = Vote(
            id=str(uuid.uuid4()),
            poll_id=poll_id,
            option_id=option_id,
            grade_id=grade_id,
            user_id=current_user.id if current_user else None,
            voter_token=voter_token,
        )
        db.add(vote)

    await db.commit()
    return {"voter_token": voter_token, "message": "投票が完了しました"}


@router.get("/{poll_id}/results", response_model=PollResults)
async def get_results(
    poll_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="投票が見つかりません")
    if poll.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="この投票結果を閲覧する権限がありません")

    votes_result = await db.execute(
        select(Vote).where(Vote.poll_id == poll_id)
    )
    votes = votes_result.scalars().all()

    grade_map = {g.id: g for g in poll.grades}
    grade_value_map = {g.id: g.value for g in poll.grades}

    # votes_by_option: option_id -> list of grade values
    votes_by_option: dict[str, list[int]] = defaultdict(list)
    # counts_by_option_grade: option_id -> grade_id -> count
    counts_by_option_grade: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    # Count unique voters
    voter_tokens: set[str] = set()
    for vote in votes:
        votes_by_option[vote.option_id].append(grade_value_map[vote.grade_id])
        counts_by_option_grade[vote.option_id][vote.grade_id] += 1
        voter_tokens.add(vote.voter_token or vote.user_id or vote.id)

    total_voters = len(voter_tokens)

    option_scores = [
        OptionScore(
            option_id=opt.id,
            name=opt.name,
            grades=sorted(votes_by_option.get(opt.id, [])),
        )
        for opt in poll.options
    ]

    ranked = compute_rankings(option_scores)

    option_name_map = {o.id: o.name for o in poll.options}

    option_results = []
    for rank, score in ranked:
        grade_values = score.grades
        n = len(grade_values)
        median_val = _lower_median(grade_values) if grade_values else 0

        # Find the grade object whose value == median_val (closest)
        best_grade = min(
            poll.grades,
            key=lambda g: abs(g.value - median_val),
        )

        dist = []
        for grade in sorted(poll.grades, key=lambda g: g.value, reverse=True):
            count = counts_by_option_grade[score.option_id].get(grade.id, 0)
            pct = (count / n * 100) if n > 0 else 0
            dist.append(
                GradeDistribution(
                    grade_id=grade.id,
                    label=grade.label,
                    value=grade.value,
                    count=count,
                    percentage=round(pct, 1),
                )
            )

        option_results.append(
            OptionResult(
                option_id=score.option_id,
                name=score.name,
                median_grade=GradeResponse.model_validate(best_grade),
                median_value=float(median_val),
                rank=rank,
                total_votes=n,
                grade_distribution=dist,
            )
        )

    return PollResults(
        poll_id=poll.id,
        title=poll.title,
        total_voters=total_voters,
        results=option_results,
    )


@router.patch("/{poll_id}/close", response_model=PollResponse)
async def close_poll(
    poll_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Poll)
        .options(selectinload(Poll.options), selectinload(Poll.grades))
        .where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="投票が見つかりません")
    if poll.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="権限がありません")
    poll.is_open = False
    await db.commit()
    await db.refresh(poll)
    return poll
