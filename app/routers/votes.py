import hashlib
import hmac
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import models
from app.config import MJ_GRADES, VOTING_METHODS, settings
from app.database import get_db
from app.schemas import VoteSubmitRequest

router = APIRouter(prefix="/vote", tags=["vote"])

VOTER_COOKIE = "voter_id"
VOTER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


def _make_fingerprint(voter_id: str, poll_public_id: str) -> str:
    key = settings.SECRET_KEY.encode()
    msg = f"{voter_id}:{poll_public_id}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def _is_poll_active(poll: models.Poll) -> bool:
    now = datetime.utcnow()
    if poll.start_time and now < poll.start_time:
        return False
    if poll.end_time and now > poll.end_time:
        return False
    return True


def _get_poll_or_404(public_id: str, db: Session) -> models.Poll:
    poll = db.query(models.Poll).filter(models.Poll.public_id == public_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="投票フォームが見つかりません。")
    return poll


def _serialize_public_poll(poll: models.Poll) -> dict:
    return {
        "public_id": poll.public_id,
        "title": poll.title,
        "description": poll.description,
        "voting_method": poll.voting_method,
        "voting_method_label": VOTING_METHODS.get(poll.voting_method, poll.voting_method),
        "method_settings": poll.method_settings or {},
        "start_time": poll.start_time.strftime("%Y-%m-%dT%H:%M") if poll.start_time else None,
        "end_time": poll.end_time.strftime("%Y-%m-%dT%H:%M") if poll.end_time else None,
        "options": [
            {"id": o.id, "text": o.text, "order_index": o.order_index}
            for o in poll.options
        ],
        "mj_grades": MJ_GRADES,
        "is_active": _is_poll_active(poll),
    }


# ----------------------------- 投票フォーム取得 (公開) -----------------------------

@router.get("/{public_id}")
async def get_vote_poll(public_id: str, db: Session = Depends(get_db)):
    poll = _get_poll_or_404(public_id, db)
    return _serialize_public_poll(poll)


# ----------------------------- 投票済みステータス確認 -----------------------------

@router.get("/{public_id}/status")
async def get_vote_status(public_id: str, request: Request, db: Session = Depends(get_db)):
    poll = _get_poll_or_404(public_id, db)
    voter_id = request.cookies.get(VOTER_COOKIE, "")
    already_voted = False
    if voter_id:
        fp = _make_fingerprint(voter_id, poll.public_id)
        existing = (
            db.query(models.Vote)
            .filter(models.Vote.poll_id == poll.id, models.Vote.voter_fingerprint == fp)
            .first()
        )
        already_voted = existing is not None

    return {"already_voted": already_voted, "is_active": _is_poll_active(poll)}


# ----------------------------- 投票送信 -----------------------------

@router.post("/{public_id}")
async def submit_vote(
    public_id: str,
    body: VoteSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    poll = _get_poll_or_404(public_id, db)

    if not _is_poll_active(poll):
        raise HTTPException(status_code=400, detail="この投票は現在受け付けていません。")

    voter_id = request.cookies.get(VOTER_COOKIE)
    is_new_voter = voter_id is None
    if is_new_voter:
        voter_id = secrets.token_urlsafe(32)

    fp = _make_fingerprint(voter_id, poll.public_id)

    existing = (
        db.query(models.Vote)
        .filter(models.Vote.poll_id == poll.id, models.Vote.voter_fingerprint == fp)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="すでにこの投票に参加済みです。")

    vote = models.Vote(
        poll_id=poll.id,
        voter_fingerprint=fp,
        vote_data=body.vote_data,
    )
    db.add(vote)
    db.commit()

    response = JSONResponse({"success": True})
    if is_new_voter:
        response.set_cookie(
            key=VOTER_COOKIE,
            value=voter_id,
            httponly=True,
            max_age=VOTER_COOKIE_MAX_AGE,
            samesite="lax",
        )
    return response
