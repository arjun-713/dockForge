from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DockForge API"
    app_version: str = "0.1.0"

    database_url: str = "sqlite:///./playground.db"
    docker_socket: str = "/var/run/docker.sock"
    max_build_timeout: int = 60
    max_run_timeout: int = 30
    submission_memory_limit: str = "256m"
    submission_cpu_quota: int = 50000
    problems_dir: str = "/app/problems"
    max_submission_size_bytes: int = 32_768


@lru_cache
def get_settings() -> Settings:
    return Settings()
