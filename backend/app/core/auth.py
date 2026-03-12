from __future__ import annotations

from dataclasses import replace

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.logging import log_event
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AuthService, AuthServiceError


def _auth_error(message: str, *, error_code: str = "AUTH_ERROR", code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    return HTTPException(status_code=code, detail={"error_code": error_code, "message": message})


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return token or None


def _legacy_user_context() -> CurrentUserContext:
    settings = get_settings()
    return CurrentUserContext(
        user_id="legacy_user",
        org_id=settings.default_org_id,
        role="OWNER",
        email="legacy@coproduct.local",
        display_name="Legacy Token User",
        status="ACTIVE",
        session_id=None,
        auth_mode="legacy",
    )


def verify_api_token(authorization: str | None = Header(default=None)) -> None:
    """Legacy static token validator kept for migration fallback."""
    settings = get_settings()
    if authorization is None:
        raise _auth_error("Missing Authorization header")

    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise _auth_error("Invalid API token")


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUserContext:
    """Main auth dependency supporting `legacy | hybrid | jwt` modes."""
    settings = get_settings()
    auth_mode = settings.auth_mode

    if auth_mode == "legacy":
        verify_api_token(authorization)
        return _legacy_user_context()

    access_token = _extract_bearer_token(authorization)
    if not access_token:
        if auth_mode == "hybrid":
            try:
                verify_api_token(authorization)
                log_event("auth_legacy_fallback", auth_mode=auth_mode)
                return replace(_legacy_user_context(), auth_mode="hybrid")
            except HTTPException:
                pass
        raise _auth_error("Missing or invalid Authorization header")

    auth_service = AuthService(settings=settings, repo=UserRepository(db))
    try:
        return auth_service.get_current_user_from_access_token(access_token)
    except AuthServiceError as exc:
        if auth_mode == "hybrid":
            try:
                verify_api_token(authorization)
                log_event("auth_legacy_fallback", auth_mode=auth_mode, reason=exc.error_code)
                return replace(_legacy_user_context(), auth_mode="hybrid")
            except HTTPException:
                pass
        raise _auth_error(exc.message, error_code=exc.error_code, code=exc.http_status) from exc
