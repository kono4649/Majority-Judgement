import asyncio
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.auth import (
    create_access_token,
    decode_access_token,
    generate_activation_token,
    hash_password,
    validate_password,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.email_utils import send_activation_email

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None
    return user


def require_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/auth/login"})
    return user


# ----------------------------- 登録 -----------------------------

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = []

    if password != password_confirm:
        errors.append("パスワードが一致しません。")

    if not validate_password(password):
        errors.append(
            "パスワードは8文字以上で、大文字・小文字・数字・記号をそれぞれ1文字以上含めてください。"
        )

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        errors.append("このメールアドレスはすでに登録されています。")

    if errors:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "email": email},
        )

    token = generate_activation_token()
    user = models.User(
        email=email,
        hashed_password=hash_password(password),
        is_active=False,
        activation_token=token,
    )
    db.add(user)
    db.commit()

    asyncio.create_task(send_activation_email(email, token))

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "success": True,
            "message": f"登録メールを {email} に送信しました。メール内のリンクをクリックしてアカウントを有効化してください。",
        },
    )


# ----------------------------- アクティベーション -----------------------------

@router.get("/activate/{token}")
async def activate(token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.activation_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="無効または期限切れのアクティベーションリンクです。")
    user.is_active = True
    user.activation_token = None
    db.commit()
    return RedirectResponse(url="/auth/login?activated=1")


# ----------------------------- ログイン -----------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, activated: int = 0):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "activated": activated == 1},
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "メールアドレスまたはパスワードが間違っています。"},
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "アカウントが有効化されていません。登録メールをご確認ください。"},
        )

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return resp


# ----------------------------- ログアウト -----------------------------

@router.post("/logout")
async def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("access_token")
    return resp
