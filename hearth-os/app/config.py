from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: Literal["dev", "prod"] = "dev"
    HOUSEHOLD_PIN: str = "4829"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    HOUSEHOLD_ENC_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./data/hearth.db"
    XAI_API_KEY: str = ""
    XAI_MODEL: str = "grok-4"
    XAI_API_URL: str = "https://api.x.ai/v1/chat/completions"
    CRON_TOKEN: str = ""
    TOPS_AD_URL: str = "https://www.topsmarkets.com/WeeklyAd/"
    WEEKLY_CAP: float = 110.0
    APP_VERSION: str = "1.0.0"

    def enc_key(self) -> str:
        return self.HOUSEHOLD_ENC_KEY.strip() or self.SECRET_KEY

    def grok_configured(self) -> bool:
        return bool(self.XAI_API_KEY.strip())

    def refuse_insecure_prod(self) -> None:
        if self.ENV != "prod":
            return
        secret = self.SECRET_KEY.lower()
        if "change-me" in secret:
            raise RuntimeError("prod refuses SECRET_KEY containing 'change-me'")
        if self.HOUSEHOLD_PIN.strip() == "4829":
            raise RuntimeError("prod refuses default HOUSEHOLD_PIN 4829")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
