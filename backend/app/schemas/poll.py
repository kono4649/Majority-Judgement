from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


DEFAULT_GRADES = [
    {"label": "最高", "value": 5},
    {"label": "優良", "value": 4},
    {"label": "良好", "value": 3},
    {"label": "普通", "value": 2},
    {"label": "不良", "value": 1},
    {"label": "不適切", "value": 0},
]


class GradeInput(BaseModel):
    label: str
    value: int


class OptionInput(BaseModel):
    name: str


class PollCreate(BaseModel):
    title: str
    description: Optional[str] = None
    options: list[OptionInput]
    grades: list[GradeInput] = [GradeInput(**g) for g in DEFAULT_GRADES]
    closes_at: Optional[datetime] = None
    is_public: bool = True


class PollUpdate(BaseModel):
    closes_at: Optional[datetime] = None
    is_public: Optional[bool] = None

    @field_validator("options")
    @classmethod
    def options_not_empty(cls, v):
        if len(v) < 2:
            raise ValueError("最低2つの選択肢が必要です")
        return v

    @field_validator("grades")
    @classmethod
    def grades_not_empty(cls, v):
        if len(v) < 2:
            raise ValueError("最低2つの評価が必要です")
        return v


class GradeResponse(BaseModel):
    id: str
    label: str
    value: int

    model_config = {"from_attributes": True}


class OptionResponse(BaseModel):
    id: str
    name: str
    display_order: int

    model_config = {"from_attributes": True}


class PollResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    is_open: bool
    is_public: bool
    created_at: datetime
    closes_at: Optional[datetime]
    creator_id: str
    options: list[OptionResponse]
    grades: list[GradeResponse]

    model_config = {"from_attributes": True}


class VoteInput(BaseModel):
    """Key: option_id, Value: grade_id"""
    votes: dict[str, str]
    voter_token: Optional[str] = None


class GradeDistribution(BaseModel):
    grade_id: str
    label: str
    value: int
    count: int
    percentage: float


class OptionResult(BaseModel):
    option_id: str
    name: str
    median_grade: GradeResponse
    median_value: float
    rank: int
    total_votes: int
    grade_distribution: list[GradeDistribution]


class PollResults(BaseModel):
    poll_id: str
    title: str
    total_voters: int
    results: list[OptionResult]
