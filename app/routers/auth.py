from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
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
from app.schemas import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


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
        raise HTTPException(status_code=401, detail="ログインが必要です。")
    return user


# ----------------------------- 登録 -----------------------------

@router.post("/register")
async def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if body.password != body.password_confirm:
        raise HTTPException(status_code=422, detail="パスワードが一致しません。")

    if not validate_password(body.password):
        raise HTTPException(
            status_code=422,
            detail="パスワードは8文字以上で、大文字・小文字・数字・記号をそれぞれ1文字以上含めてください。",
        )

    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="このメールアドレスはすでに登録されています。")

    token = generate_activation_token()
    user = models.User(
        email=body.email,
        hashed_password=hash_password(body.password),
        is_active=False,
        activation_token=token,
    )
    db.add(user)
    db.commit()

    background_tasks.add_task(send_activation_email, body.email, token)

    return {
        "message": f"登録メールを {body.email} に送信しました。メール内のリンクをクリックしてアカウントを有効化してください。"
    }


# ----------------------------- アクティベーション -----------------------------

@router.get("/activate/{token}")
async def activate(token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.activation_token == token).first()
    if not user:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=invalid_token")
    user.is_active = True
    user.activation_token = None
    db.commit()
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?activated=1")


# ----------------------------- ログイン -----------------------------

@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが間違っています。")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="アカウントが有効化されていません。登録メールをご確認ください。")

    access_token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse({"user": {"id": user.id, "email": user.email}})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


# ----------------------------- ログアウト -----------------------------

@router.post("/logout")
async def logout():
    response = JSONResponse({"message": "ログアウトしました。"})
    response.delete_cookie("access_token")
    return response


# ----------------------------- 現在ユーザー取得 -----------------------------

@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未認証です。")
    return {"id": user.id, "email": user.email}
