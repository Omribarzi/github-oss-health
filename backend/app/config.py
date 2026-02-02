from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "sqlite:///:memory:"
    environment: str = "development"

    # Auth
    secret_key: str = "change-me-in-production-il-cre-marketplace-2024"
    access_token_expire_minutes: int = 1440  # 24 hours
    algorithm: str = "HS256"

    # Admin
    admin_api_key: Optional[str] = None

    # Israeli market defaults
    default_currency: str = "ILS"
    default_area_unit: str = "sqm"
    default_country: str = "IL"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
