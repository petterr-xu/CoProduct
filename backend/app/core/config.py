from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COPRODUCT_",
        extra="ignore",
    )

    app_name: str = "CoProduct Backend"
    app_env: str = "dev"
    app_debug: bool = False
    api_prefix: str = "/api"
    api_token: str = "dev-token"

    database_url: str = "postgresql+psycopg://coproduct:coproduct@localhost:5432/coproduct"
    database_echo: bool = False

    max_text_length: int = 12000
    normalized_text_limit: int = 8000
    upload_dir: str = "./uploaded_files"
    upload_max_size_mb: int = 20
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
