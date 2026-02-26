from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://mj_user:mj_password@db:5432/mj_db"
    SECRET_KEY: str = "changeme-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Initial superuser (created automatically on first startup)
    INITIAL_SUPERUSER_EMAIL: str = ""
    INITIAL_SUPERUSER_USERNAME: str = "admin"
    INITIAL_SUPERUSER_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
