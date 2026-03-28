import hashlib
import hmac
import json
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.config import MJ_GRADES, VOTING_METHODS, settings
from app.database import get_db

router = APIRouter(prefix="/vote", tags=["vote"])
templates = Jinja2Templates(directory="templates")

VOTER_COOKIE = "voter_id"
VOTER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


def _get_or_create_voter_id(request: Request, response=None):
    voter_id = request.cookies.get(VOTER_COOKIE)
    is_new = voter_id is None
    if is_new:
        voter_id = secrets.token_urlsafe(32)
    return voter_id, is_new


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


# ----------------------------- 投票ページ -----------------------------

@router.get("/{public_id}", response_class=HTMLResponse)
async def vote_page(public_id: str, request: Request, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.public_id == public_id).first()
    if not poll:
        return templates.TemplateResponse(
            "vote.html",
            {"request": request, "error": "投票フォームが見つかりません。"},
            status_code=404,
        )

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

    is_active = _is_poll_active(poll)
    options = poll.options

    return templates.TemplateResponse(
        "vote.html",
        {
            "request": request,
            "poll": poll,
            "options": options,
            "already_voted": already_voted,
            "is_active": is_active,
            "voting_methods": VOTING_METHODS,
            "mj_grades": MJ_GRADES,
            "method_settings": poll.method_settings or {},
        },
    )


# ----------------------------- 投票送信 -----------------------------

@router.post("/{public_id}")
async def submit_vote(
    public_id: str,
    request: Request,
    vote_data_json: str = Form(...),
    db: Session = Depends(get_db),
):
    poll = db.query(models.Poll).filter(models.Poll.public_id == public_id).first()
    if not poll:
        return templates.TemplateResponse(
            "vote.html",
            {"request": request, "error": "投票フォームが見つかりません。"},
            status_code=404,
        )

    if not _is_poll_active(poll):
        return templates.TemplateResponse(
            "vote.html",
            {
                "request": request,
                "poll": poll,
                "options": poll.options,
                "error": "この投票は現在受け付けていません。",
                "is_active": False,
                "voting_methods": VOTING_METHODS,
                "mj_grades": MJ_GRADES,
                "method_settings": poll.method_settings or {},
            },
        )

    # 投票者IDの取得または生成
    voter_id, is_new = _get_or_create_voter_id(request)
    fp = _make_fingerprint(voter_id, poll.public_id)

    # 重複チェック
    existing = (
        db.query(models.Vote)
        .filter(models.Vote.poll_id == poll.id, models.Vote.voter_fingerprint == fp)
        .first()
    )
    if existing:
        resp = templates.TemplateResponse(
            "vote.html",
            {
                "request": request,
                "poll": poll,
                "options": poll.options,
                "already_voted": True,
                "is_active": True,
                "voting_methods": VOTING_METHODS,
                "mj_grades": MJ_GRADES,
                "method_settings": poll.method_settings or {},
            },
        )
        return resp

    # 投票データのパース
    try:
        vote_data = json.loads(vote_data_json)
    except (json.JSONDecodeError, ValueError):
        return templates.TemplateResponse(
            "vote.html",
            {
                "request": request,
                "poll": poll,
                "options": poll.options,
                "error": "投票データが不正です。",
                "is_active": True,
                "voting_methods": VOTING_METHODS,
                "mj_grades": MJ_GRADES,
                "method_settings": poll.method_settings or {},
            },
        )

    # 投票を保存
    vote = models.Vote(
        poll_id=poll.id,
        voter_fingerprint=fp,
        vote_data=vote_data,
    )
    db.add(vote)
    db.commit()

    # レスポンス（クッキー設定）
    resp = RedirectResponse(url=f"/vote/{public_id}/thanks", status_code=302)
    if is_new:
        resp.set_cookie(
            key=VOTER_COOKIE,
            value=voter_id,
            httponly=True,
            max_age=VOTER_COOKIE_MAX_AGE,
            samesite="lax",
        )
    return resp


# ----------------------------- サンクスページ -----------------------------

@router.get("/{public_id}/thanks", response_class=HTMLResponse)
async def thanks_page(public_id: str, request: Request, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.public_id == public_id).first()
    if not poll:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        "thanks.html",
        {"request": request, "poll": poll, "voting_methods": VOTING_METHODS},
    )
