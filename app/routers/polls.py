from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.config import VOTING_METHODS, settings
from app.database import get_db
from app.routers.auth import get_current_user, require_user
from app.schemas import CreatePollRequest, UpdatePollRequest
from app.voting import calculate_results, votes_to_csv

router = APIRouter(prefix="/polls", tags=["polls"])


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _poll_is_active(poll: models.Poll) -> bool:
    now = datetime.utcnow()
    if poll.start_time and now < poll.start_time:
        return False
    if poll.end_time and now > poll.end_time:
        return False
    return True


def _serialize_poll(poll: models.Poll, include_votes: bool = False) -> dict:
    return {
        "id": poll.id,
        "public_id": poll.public_id,
        "title": poll.title,
        "description": poll.description,
        "voting_method": poll.voting_method,
        "voting_method_label": VOTING_METHODS.get(poll.voting_method, poll.voting_method),
        "method_settings": poll.method_settings or {},
        "start_time": poll.start_time.strftime("%Y-%m-%dT%H:%M") if poll.start_time else None,
        "end_time": poll.end_time.strftime("%Y-%m-%dT%H:%M") if poll.end_time else None,
        "created_at": poll.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "options": [
            {"id": o.id, "text": o.text, "order_index": o.order_index}
            for o in poll.options
        ],
        "vote_count": len(poll.votes),
        "is_active": _poll_is_active(poll),
    }


def _require_creator(poll_id: int, user: models.User, db: Session) -> models.Poll:
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="投票フォームが見つかりません。")
    if poll.creator_id != user.id:
        raise HTTPException(status_code=403, detail="権限がありません。")
    return poll


# ----------------------------- 一覧 -----------------------------

@router.get("/")
async def list_polls(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    polls = (
        db.query(models.Poll)
        .filter(models.Poll.creator_id == user.id)
        .order_by(models.Poll.created_at.desc())
        .all()
    )
    return [_serialize_poll(p) for p in polls]


# ----------------------------- 作成 -----------------------------

@router.post("/")
async def create_poll(
    body: CreatePollRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    if body.voting_method not in VOTING_METHODS:
        raise HTTPException(status_code=422, detail="無効な投票方式です。")

    option_list = [o.strip() for o in body.options if o.strip()]
    if len(option_list) < 2:
        raise HTTPException(status_code=422, detail="選択肢は2つ以上必要です。")

    poll = models.Poll(
        title=body.title.strip(),
        description=body.description.strip(),
        voting_method=body.voting_method,
        method_settings=body.method_settings,
        creator_id=user.id,
        start_time=_parse_dt(body.start_time),
        end_time=_parse_dt(body.end_time),
    )
    db.add(poll)
    db.flush()

    for idx, text in enumerate(option_list):
        db.add(models.PollOption(poll_id=poll.id, text=text, order_index=idx))

    db.commit()
    db.refresh(poll)
    return _serialize_poll(poll)


# ----------------------------- 取得 -----------------------------

@router.get("/{poll_id}")
async def get_poll(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    poll = _require_creator(poll_id, user, db)
    return _serialize_poll(poll)


# ----------------------------- 更新 -----------------------------

@router.put("/{poll_id}")
async def update_poll(
    poll_id: int,
    body: UpdatePollRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    poll = _require_creator(poll_id, user, db)

    option_list = [o.strip() for o in body.options if o.strip()]
    if len(option_list) < 2:
        raise HTTPException(status_code=422, detail="選択肢は2つ以上必要です。")

    poll.title = body.title.strip()
    poll.description = body.description.strip()
    poll.method_settings = body.method_settings
    poll.start_time = _parse_dt(body.start_time)
    poll.end_time = _parse_dt(body.end_time)
    poll.updated_at = datetime.utcnow()

    if len(poll.votes) == 0:
        for opt in list(poll.options):
            db.delete(opt)
        db.flush()
        for idx, text in enumerate(option_list):
            db.add(models.PollOption(poll_id=poll.id, text=text, order_index=idx))
    else:
        for idx, text in enumerate(option_list):
            if idx < len(poll.options):
                poll.options[idx].text = text
                poll.options[idx].order_index = idx

    db.commit()
    db.refresh(poll)
    return _serialize_poll(poll)


# ----------------------------- 削除 -----------------------------

@router.delete("/{poll_id}")
async def delete_poll(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    poll = _require_creator(poll_id, user, db)
    db.delete(poll)
    db.commit()
    return {"message": "削除しました。"}


# ----------------------------- 結果 -----------------------------

@router.get("/{poll_id}/results")
async def get_results(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    poll = _require_creator(poll_id, user, db)

    options = [{"id": o.id, "text": o.text, "order_index": o.order_index} for o in poll.options]
    votes_data = [
        {"vote_data": v.vote_data, "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        for v in poll.votes
    ]

    result = None
    if votes_data:
        result = calculate_results(poll.voting_method, votes_data, options)

    return {
        "poll": _serialize_poll(poll),
        "options": options,
        "total_votes": len(votes_data),
        "result": result,
        "vote_url": f"{settings.BASE_URL}/vote/{poll.public_id}",
    }


# ----------------------------- CSV ダウンロード -----------------------------

@router.get("/{poll_id}/results/csv")
async def download_csv(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    poll = _require_creator(poll_id, user, db)

    options = [{"id": o.id, "text": o.text} for o in poll.options]
    votes_data = [
        {"vote_data": v.vote_data, "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        for v in poll.votes
    ]

    csv_content = votes_to_csv(poll, votes_data, options)
    filename = f"votes_{poll.public_id[:8]}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
