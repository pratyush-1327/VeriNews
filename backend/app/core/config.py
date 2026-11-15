from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VeriNews API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/verinews"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/verinews"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # City Geolocation Hubs
    SUPPORTED_CITIES: List[str] = [
        "delhi",
        "jaipur",
        "mumbai",
        "bengaluru",
        "chennai",
        "kolkata",
    ]

    CITY_METADATA: Dict[str, Dict[str, Any]] = {
        "delhi": {"lat": 28.6139, "lng": 77.2090, "name": "New Delhi"},
        "jaipur": {"lat": 26.9124, "lng": 75.7873, "name": "Jaipur"},
        "mumbai": {"lat": 19.0760, "lng": 72.8777, "name": "Mumbai"},
        "bengaluru": {"lat": 12.9716, "lng": 77.5946, "name": "Bengaluru"},
        "chennai": {"lat": 13.0827, "lng": 80.2707, "name": "Chennai"},
        "kolkata": {"lat": 22.5726, "lng": 88.3639, "name": "Kolkata"},
    }

    # API Keys for Phase 2 & 3
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GOOGLE_FACT_CHECK_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # Security & Admin for Phase 5
    ADMIN_SECRET_KEY: str = "verinews-admin-secret-2026"
    RATE_LIMIT_PER_MINUTE: int = 30
    MAX_SCRAPE_BYTES: int = 5 * 1024 * 1024  # 5MB max payload

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
