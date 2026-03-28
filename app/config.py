from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24時間

    DATABASE_URL: str = "sqlite:///./voting_app.db"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@votingapp.local"

    BASE_URL: str = "http://localhost:8000"
    DEV_MODE: bool = True  # TrueならコンソールにアクティベーションURLを表示

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

VOTING_METHODS = {
    "plurality": "単記投票（多数決）",
    "approval": "承認投票",
    "borda": "ボルダ・カウント",
    "irv": "代替投票（IRV）",
    "condorcet": "コンドルセ方式",
    "score": "スコア投票",
    "majority_judgement": "マジョリティ・ジャッジメント",
    "quadratic": "クアドラティック・ボーティング",
    "negative": "負の投票",
}

MJ_GRADES = ["拒否", "不良", "許容", "良い", "とても良い", "優秀"]
MJ_GRADE_COLORS = ["#dc3545", "#fd7e14", "#ffc107", "#20c997", "#0dcaf0", "#0d6efd"]
