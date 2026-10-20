import os
import secrets
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Product & Analytics Management System"
    API_V1_STR: str = "/api/v1"

    # =========================================================
    # Database Settings
    # =========================================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "store_db"
    DATABASE_URL: Optional[str] = None

    # =========================================================
    # Security / JWT Settings
    # =========================================================
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Login protection
    MAX_LOGIN_ATTEMPTS: int = 3
    LOGIN_LOCKOUT_MINUTES: int = 15

    # =========================================================
    # Machine Learning Settings
    # =========================================================
    MODEL_ARTIFACT_DIR: Path = Field(
        default_factory=lambda:
        Path(__file__).resolve().parents[2] / "model_artifacts"
    )

    MIN_TRAINING_RECORDS: int = 60
    MIN_TRAINING_DAYS: int = 35
    MAX_FORECAST_HORIZON_DAYS: int = 90

    # =========================================================
    # Gemini API Settings
    # =========================================================
    GEMINI_API_KEY: Optional[str] = os.getenv(
        "GEMINI_API_KEY",
        ""
    )

    # =========================================================
    # SQLAlchemy Database URL
    # =========================================================
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Encode username/password so special characters such as
        # @, :, /, #, %, etc. do not break the database URL.
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)

        return (
            f"mysql+pymysql://"
            f"{encoded_user}:{encoded_password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )

    # =========================================================
    # Environment Configuration
    # config.py -> core -> app -> backend -> .env
    # =========================================================
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            ),
            ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()