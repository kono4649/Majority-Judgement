import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$"
)


def validate_password(password: str) -> bool:
    """パスワード複雑性チェック: 8文字以上, 大小英字, 数字, 記号を含む"""
    return bool(PASSWORD_PATTERN.match(password))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_activation_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def make_voter_fingerprint(voter_token: str, poll_public_id: str) -> str:
    """投票者トークンと投票IDを組み合わせてHMAC指紋を生成（重複投票防止用）"""
    key = settings.SECRET_KEY.encode()
    msg = f"{voter_token}:{poll_public_id}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()
