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
    auth_mode: str = "jwt"  # legacy | hybrid | jwt

    database_url: str = "postgresql+psycopg://coproduct:coproduct@localhost:5432/coproduct"
    database_echo: bool = False

    jwt_secret: str = "dev-jwt-secret-change-me"
    refresh_token_secret: str = "dev-refresh-secret-change-me"
    csrf_secret: str = "dev-csrf-secret-change-me"
    api_key_pepper: str = "dev-api-key-pepper-change-me"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 1209600
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: str | None = None
    refresh_cookie_name: str = "refresh_token"
    csrf_cookie_name: str = "csrf_token"
    refresh_cookie_path: str = "/api/auth"
    csrf_cookie_path: str = "/"

    default_org_id: str = "org_default"
    bootstrap_owner_email: str = "owner@coproduct.local"
    bootstrap_owner_display_name: str = "Bootstrap Owner"
    bootstrap_owner_api_key: str = "cpk_dev_bootstrap_owner_key_change_me"

    max_text_length: int = 12000
    normalized_text_limit: int = 8000
    upload_dir: str = "./uploaded_files"
    upload_max_size_mb: int = 20
    cors_allow_origins: str = "http://localhost:3000"

    # Agent model runtime.
    model_mode: str = "heuristic"  # heuristic | cloud
    model_provider: str = "openai_compatible"
    model_api_key: str | None = None
    model_base_url: str = "https://api.deepseek.com"
    model_chat_model: str = "deepseek-chat"
    model_embedding_model: str | None = None
    model_timeout_seconds: float = 30.0
    model_structured_retries: int = 1
    model_temperature: float = 0.0

    # Phase 1.5 async workflow submission runtime.
    workflow_queue_maxsize: int = 128
    workflow_worker_count: int = 1
    workflow_enqueue_timeout_seconds: float = 0.5
    workflow_task_timeout_seconds: float = 180.0
    workflow_max_retries: int = 0
    workflow_recover_limit: int = 200


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def validate_security_settings(settings: Settings) -> None:
    """Validate authentication-related settings before app startup."""
    allowed_auth_modes = {"legacy", "hybrid", "jwt"}
    if settings.auth_mode not in allowed_auth_modes:
        raise RuntimeError(f"Unsupported COPRODUCT_AUTH_MODE: {settings.auth_mode}")

    if not settings.refresh_cookie_path.startswith("/"):
        raise RuntimeError("COPRODUCT_REFRESH_COOKIE_PATH must start with '/'")
    if not settings.csrf_cookie_path.startswith("/"):
        raise RuntimeError("COPRODUCT_CSRF_COOKIE_PATH must start with '/'")

    if settings.app_env.lower() != "prod":
        return

    if settings.auth_mode in {"legacy", "hybrid"}:
        raise RuntimeError("COPRODUCT_AUTH_MODE must be `jwt` in production")

    if settings.api_token == "dev-token":
        raise RuntimeError("COPRODUCT_API_TOKEN cannot be `dev-token` in production")

    insecure_defaults = {
        "dev-jwt-secret-change-me",
        "dev-refresh-secret-change-me",
        "dev-csrf-secret-change-me",
        "dev-api-key-pepper-change-me",
    }
    if (
        not settings.jwt_secret
        or not settings.refresh_token_secret
        or not settings.csrf_secret
        or not settings.api_key_pepper
        or settings.jwt_secret in insecure_defaults
        or settings.refresh_token_secret in insecure_defaults
        or settings.csrf_secret in insecure_defaults
        or settings.api_key_pepper in insecure_defaults
    ):
        raise RuntimeError("JWT/refresh/csrf/api-key secrets must be explicitly configured in production")
