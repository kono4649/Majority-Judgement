import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    creator_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closes_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    creator: Mapped["User"] = relationship("User", back_populates="polls")  # noqa: F821
    options: Mapped[list["Option"]] = relationship("Option", back_populates="poll", order_by="Option.display_order")
    grades: Mapped[list["Grade"]] = relationship("Grade", back_populates="poll", order_by="Grade.value.desc()")


class Option(Base):
    __tablename__ = "options"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id: Mapped[str] = mapped_column(String, ForeignKey("polls.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    poll: Mapped["Poll"] = relationship("Poll", back_populates="options")
    votes: Mapped[list["Vote"]] = relationship("Vote", back_populates="option")


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id: Mapped[str] = mapped_column(String, ForeignKey("polls.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # higher = better

    poll: Mapped["Poll"] = relationship("Poll", back_populates="grades")
    votes: Mapped[list["Vote"]] = relationship("Vote", back_populates="grade")


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id: Mapped[str] = mapped_column(String, ForeignKey("polls.id"), nullable=False)
    option_id: Mapped[str] = mapped_column(String, ForeignKey("options.id"), nullable=False)
    grade_id: Mapped[str] = mapped_column(String, ForeignKey("grades.id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    voter_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # for anonymous voting
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    poll: Mapped["Poll"] = relationship("Poll")
    option: Mapped["Option"] = relationship("Option", back_populates="votes")
    grade: Mapped["Grade"] = relationship("Grade", back_populates="votes")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="votes")  # noqa: F821
