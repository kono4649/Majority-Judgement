from pydantic import BaseModel, EmailStr
from typing import Any


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreatePollRequest(BaseModel):
    title: str
    description: str = ""
    voting_method: str
    options: list[str]
    start_time: str | None = None
    end_time: str | None = None
    method_settings: dict = {}


class UpdatePollRequest(BaseModel):
    title: str
    description: str = ""
    options: list[str]
    start_time: str | None = None
    end_time: str | None = None
    method_settings: dict = {}


class VoteSubmitRequest(BaseModel):
    vote_data: dict[str, Any]
