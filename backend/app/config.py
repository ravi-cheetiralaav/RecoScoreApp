"""Configuration settings for RecoScoreApp."""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "RecoScoreApp"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./recoscore.db"

    # Facebook Graph API (optional)
    facebook_access_token: str = ""
    facebook_page_id: str = "stock.swami.859262"

    # Market data provider
    market_data_provider: str = "mock"  # yfinance | mock (set "yfinance" for live data)

    # Ingestion adapter: "facebook" | "mock"
    ingestion_adapter: str = "mock"

    # LLM settings (optional)
    openai_api_key: str = ""
    use_llm_extraction: bool = False

    # Scoring thresholds
    good_threshold: float = 0.05   # +5%
    bad_threshold: float = -0.05   # -5%

    # Scheduling
    score_recompute_interval_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
