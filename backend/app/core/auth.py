from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def verify_api_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_ERROR", "message": "Missing Authorization header"},
        )

    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTH_ERROR", "message": "Invalid API token"},
        )

