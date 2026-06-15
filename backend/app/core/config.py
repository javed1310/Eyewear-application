"""
OptiFlow — Application Configuration
Loads all settings from environment variables via Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    # ── App ──
    APP_NAME: str = "OptiFlow"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://optiflow:optiflow@localhost:5432/optiflow"
    DATABASE_URL_SYNC: str = "postgresql://optiflow:optiflow@localhost:5432/optiflow"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── AI — Rx Parsing (Phase 5) ──
    GROQ_API_KEY: str = ""
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.2-90b-vision-preview"
    RX_CONFIDENCE_THRESHOLD: float = 0.85

    # ── Notifications (Phase 6) ──
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "alerts@optiflow.demo"
    RESEND_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    OPS_ALERT_EMAIL: str = "ops@optiflow.demo"
    OPS_ALERT_WHATSAPP: str = ""

    # ── TAT Engine (Phase 6) ──
    TAT_SWEEP_INTERVAL_MINUTES: int = 5
    ALERT_COOLDOWN_MINUTES: int = 60

    # ── SLA Defaults ──
    REWORK_BUFFER_HOURS: int = 24
    DWELL_THRESHOLD_HOURS: int = 4

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
