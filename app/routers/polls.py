import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.config import VOTING_METHODS, settings
from app.database import get_db
from app.routers.auth import get_current_user
from app.voting import calculate_results, votes_to_csv

router = APIRouter(prefix="/polls", tags=["polls"])
templates = Jinja2Templates(directory="templates")


def _require_creator(poll_id: int, user, db: Session):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="投票フォームが見つかりません。")
    if poll.creator_id != user.id:
        raise HTTPException(status_code=403, detail="権限がありません。")
    return poll


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


# ----------------------------- ダッシュボード -----------------------------

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    polls = (
        db.query(models.Poll)
        .filter(models.Poll.creator_id == user.id)
        .order_by(models.Poll.created_at.desc())
        .all()
    )
    now = datetime.utcnow()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "polls": polls,
            "voting_methods": VOTING_METHODS,
            "now": now,
            "base_url": settings.BASE_URL,
        },
    )


# ----------------------------- 投票フォーム作成 -----------------------------

@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse(
        "create_poll.html",
        {"request": request, "user": user, "voting_methods": VOTING_METHODS},
    )


@router.post("/create")
async def create_poll(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    voting_method: str = Form(...),
    options: str = Form(...),          # JSON array of option texts
    start_time: str = Form(""),
    end_time: str = Form(""),
    method_settings: str = Form("{}"), # JSON
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")

    if voting_method not in VOTING_METHODS:
        raise HTTPException(status_code=400, detail="無効な投票方式です。")

    try:
        option_list = json.loads(options)
        if not isinstance(option_list, list) or len(option_list) < 2:
            raise ValueError
        option_list = [str(o).strip() for o in option_list if str(o).strip()]
        if len(option_list) < 2:
            raise ValueError
    except (ValueError, json.JSONDecodeError):
        return templates.TemplateResponse(
            "create_poll.html",
            {
                "request": request,
                "user": user,
                "voting_methods": VOTING_METHODS,
                "error": "選択肢は2つ以上必要です。",
            },
        )

    try:
        settings_dict = json.loads(method_settings) if method_settings else {}
    except json.JSONDecodeError:
        settings_dict = {}

    poll = models.Poll(
        title=title.strip(),
        description=description.strip(),
        voting_method=voting_method,
        method_settings=settings_dict,
        creator_id=user.id,
        start_time=_parse_datetime(start_time),
        end_time=_parse_datetime(end_time),
    )
    db.add(poll)
    db.flush()

    for idx, text in enumerate(option_list):
        opt = models.PollOption(poll_id=poll.id, text=text, order_index=idx)
        db.add(opt)

    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


# ----------------------------- 投票フォーム編集 -----------------------------

@router.get("/{poll_id}/edit", response_class=HTMLResponse)
async def edit_page(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    poll = _require_creator(poll_id, user, db)
    return templates.TemplateResponse(
        "edit_poll.html",
        {
            "request": request,
            "user": user,
            "poll": poll,
            "voting_methods": VOTING_METHODS,
        },
    )


@router.post("/{poll_id}/edit")
async def edit_poll(
    poll_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    options: str = Form(...),
    start_time: str = Form(""),
    end_time: str = Form(""),
    method_settings: str = Form("{}"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    poll = _require_creator(poll_id, user, db)

    try:
        option_list = json.loads(options)
        option_list = [str(o).strip() for o in option_list if str(o).strip()]
        if len(option_list) < 2:
            raise ValueError
    except (ValueError, json.JSONDecodeError):
        return templates.TemplateResponse(
            "edit_poll.html",
            {
                "request": request,
                "user": user,
                "poll": poll,
                "voting_methods": VOTING_METHODS,
                "error": "選択肢は2つ以上必要です。",
            },
        )

    try:
        settings_dict = json.loads(method_settings) if method_settings else {}
    except json.JSONDecodeError:
        settings_dict = {}

    poll.title = title.strip()
    poll.description = description.strip()
    poll.method_settings = settings_dict
    poll.start_time = _parse_datetime(start_time)
    poll.end_time = _parse_datetime(end_time)
    poll.updated_at = datetime.utcnow()

    # 選択肢を更新（既存票がある場合は追加のみ）
    existing_count = len(poll.votes)
    if existing_count == 0:
        # 票がなければ全削除して再作成
        for opt in list(poll.options):
            db.delete(opt)
        db.flush()
        for idx, text in enumerate(option_list):
            opt = models.PollOption(poll_id=poll.id, text=text, order_index=idx)
            db.add(opt)
    else:
        # 既存票がある場合はテキストのみ更新
        for idx, text in enumerate(option_list):
            if idx < len(poll.options):
                poll.options[idx].text = text
                poll.options[idx].order_index = idx

    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


# ----------------------------- 投票フォーム削除 -----------------------------

@router.post("/{poll_id}/delete")
async def delete_poll(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    poll = _require_creator(poll_id, user, db)
    db.delete(poll)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


# ----------------------------- 結果表示 -----------------------------

@router.get("/{poll_id}/results", response_class=HTMLResponse)
async def results_page(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    poll = _require_creator(poll_id, user, db)

    options = [{"id": o.id, "text": o.text, "order_index": o.order_index} for o in poll.options]
    votes_data = [
        {"vote_data": v.vote_data, "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        for v in poll.votes
    ]

    result = None
    if votes_data:
        result = calculate_results(poll.voting_method, votes_data, options)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "user": user,
            "poll": poll,
            "options": options,
            "total_votes": len(votes_data),
            "result": result,
            "voting_methods": VOTING_METHODS,
            "base_url": settings.BASE_URL,
        },
    )


# ----------------------------- CSV ダウンロード -----------------------------

@router.get("/{poll_id}/results/csv")
async def download_csv(poll_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
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
