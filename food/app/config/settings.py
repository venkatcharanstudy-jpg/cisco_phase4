from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Smart Food Ordering & Restaurant Assistant"
    database_url: str
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    llm_timeout_seconds: float = 30.0
    internal_api_base_url: str = "http://127.0.0.1:8000"
    max_upload_mb: int = 5
    chat_rate_limit_per_minute: int = 20
    pending_action_ttl_minutes: int = 15
    max_tool_iterations: int = 4
    history_turns: int = 12
    knowledge_base_dir: str = "knowledge_base"


@lru_cache
def get_settings() -> Settings:
    return Settings()
