from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    swarm_max_steps: int = Field(default=6, alias="SWARM_MAX_STEPS")
    swarm_memory_dir: str = Field(default="memory/", alias="SWARM_MEMORY_DIR")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


def get_settings() -> Settings:
    return Settings()

