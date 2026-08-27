from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "dev-secret"
    jwt_secret: str = "dev-jwt"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    encryption_key: str = "dev-encryption-key-must-be-32b!!"
    settings_secret: str = ""  # SETTINGS_SECRET — bootstrap only; falls back to encryption_key
    operator_pin: str = ""
    confirmation_pin: str = ""
    default_language: Literal["en", "tr", "ar"] = "en"
    cors_origins: str = "http://localhost:5173"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    rate_limit_chat_per_minute: int = 20
    rate_limit_analysis_per_minute: int = 6
    bot_min_order_interval_seconds: int = 30

    database_url: str = "postgresql+asyncpg://zorro:zorro@localhost:5432/zorro"
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""
    quick_model: str = "claude-sonnet-5"
    deep_model: str = "claude-fable-5"

    oanda_api_key: str = ""  # bootstrap; Settings overlay key is OANDA_API_TOKEN
    oanda_account_id: str = ""
    oanda_environment: str = "practice"
    oanda_base_url: str = "https://api-fxpractice.oanda.com"

    twelve_data_api_key: str = ""
    twelve_data_base_url: str = "https://api.twelvedata.com"
    price_divergence_bps: float = 15.0

    finnhub_api_key: str = ""
    finnhub_base_url: str = "https://finnhub.io/api/v1"

    metaapi_token: str = ""
    metaapi_account_id: str = ""
    metaapi_region: str = "new-york"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_allowed_chat_id: str = ""

    sentry_dsn: str = ""
    public_app_url: str = ""
    webhook_base_url: str = ""

    operator_email: str = "operator@local"
    operator_password: str = "change-me"

    sample_floor: int = 30
    max_target_atr_distance: float = 25.0
    tp1_min_atr: float = 2.5
    spread_abnormal_multiplier: float = 3.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
