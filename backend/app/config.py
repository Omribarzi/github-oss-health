from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    github_token: str
    environment: str = "development"
    api_rate_limit_safety_threshold: int = 500
    deep_analysis_max_requests_per_run: int = 5000

    # Health index weights (configurable)
    health_index_weight_velocity: float = 0.25
    health_index_weight_responsiveness: float = 0.25
    health_index_weight_contributors: float = 0.25
    health_index_weight_adoption: float = 0.25

    # Universe criteria
    min_stars: int = 2000
    max_age_months: int = 24
    max_days_since_push: int = 90

    class Config:
        env_file = ".env"


settings = Settings()
