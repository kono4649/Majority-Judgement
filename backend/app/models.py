import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    activation_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    polls = relationship("Poll", back_populates="creator")


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True, default=_new_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    voting_method = Column(String, nullable=False)
    # 投票方式固有の設定 (例: スコア最大値, クアドラティックのクレジット数)
    method_settings = Column(JSON, nullable=True, default=dict)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", back_populates="polls")
    options = relationship(
        "PollOption",
        back_populates="poll",
        order_by="PollOption.order_index",
        cascade="all, delete-orphan",
    )
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    text = Column(String, nullable=False)
    order_index = Column(Integer, default=0)

    poll = relationship("Poll", back_populates="options")


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    # 投票者フィンガープリント (HMAC(voter_token + poll_public_id) をハッシュ化)
    voter_fingerprint = Column(String, nullable=False, index=True)
    vote_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    poll = relationship("Poll", back_populates="votes")
