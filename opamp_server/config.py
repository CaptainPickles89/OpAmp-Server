"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration with environment variable overrides."""

    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "./data/registry.db"
    max_body_size: int = 1_048_576  # 1 MB
    rate_limit: str = "100/minute"
    health_snapshot_retention: int = 1000
    effective_config_retention: int = 10
    log_level: str = "INFO"

    model_config = {"env_prefix": "OPAMP_"}


settings = Settings()
