"""Application configuration and settings."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core
    env: str = "development"
    secret_key: str = "ledgeros-dev-super-secret-key-32chars"
    host: str = "0.0.0.0"
    port: int = 8000

    # Database: Supports SQLite async for rapid local run and PostgreSQL (Neon) for production
    database_url: str = "sqlite+aiosqlite:///./ledgeros.db"
    sync_database_url: str = "sqlite:///./ledgeros.db"

    # Redis
    redis_url: str | None = None

    # LLM Settings
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "gemini/gemini-2.5-flash"

    # Razorpay
    razorpay_key_id: str = "rzp_test_dummykey123"
    razorpay_key_secret: str = "dummysecret456"
    razorpay_webhook_secret: str = "dummywebhooksecret789"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    finrca_data_dir: Path = Path("external/FinRCA-AI-Bench/data/benchmark")


settings = Settings()
