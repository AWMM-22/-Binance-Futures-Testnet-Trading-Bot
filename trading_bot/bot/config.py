from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigError


class Settings(BaseSettings):
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://testnet.binancefuture.com"

    model_config = SettingsConfigDict(
        env_prefix="BINANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:  # pragma: no cover - defensive
        raise ConfigError("Failed to load configuration") from exc
