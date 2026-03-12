from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.user_context import CurrentUserContext
from app.repositories import UserRepository
from app.services import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_auth_service(db: Session) -> AuthService:
    settings = get_settings()
    return AuthService(settings=settings, repo=UserRepository(db))


def _set_auth_cookies(*, response: Response, settings: Settings, refresh_token: str, csrf_token: str) -> None:
    base_kwargs = {
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
        "domain": settings.auth_cookie_domain,
    }
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=True,
        path=settings.refresh_cookie_path,
        **base_kwargs,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=False,
        path=settings.csrf_cookie_path,
        **base_kwargs,
    )


def _clear_auth_cookies(*, response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        domain=settings.auth_cookie_domain,
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path=settings.csrf_cookie_path,
        domain=settings.auth_cookie_domain,
    )


class LoginRequest(BaseModel):
    apiKey: str = Field(min_length=20, max_length=128)
    deviceInfo: str | None = Field(default=None, max_length=255)


class LoginUser(BaseModel):
    id: str
    email: str
    displayName: str
    role: str
    orgId: str
    status: str


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    user: LoginUser


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int


class LogoutRequest(BaseModel):
    allDevices: bool = False


class AuthContextOrg(BaseModel):
    orgId: str
    orgName: str


class AuthContextResponse(BaseModel):
    user: LoginUser
    activeOrg: AuthContextOrg | None
    availableOrgs: list[AuthContextOrg]
    scopeMode: str


@router.post("/key-login", response_model=LoginResponse)
def key_login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate with API key and issue access/refresh tokens."""
    service = _build_auth_service(db)
    settings = get_settings()
    try:
        result = service.login_with_api_key(
            api_key=payload.apiKey,
            device_info=payload.deviceInfo,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
    except AuthServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.http_status,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "AUTH_ERROR", "message": "Login failed"},
        ) from exc

    _set_auth_cookies(
        response=response,
        settings=settings,
        refresh_token=result.refresh_token,
        csrf_token=result.csrf_token,
    )
    return LoginResponse(
        accessToken=result.access_token,
        expiresIn=result.expires_in,
        user=LoginUser(
            id=result.user.user_id,
            email=result.user.email,
            displayName=result.user.display_name,
            role=result.user.role,
            orgId=result.user.org_id,
            status=result.user.status,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)) -> RefreshResponse:
    """Rotate refresh token session and issue a new access token."""
    service = _build_auth_service(db)
    settings = get_settings()

    refresh_cookie = request.cookies.get(settings.refresh_cookie_name)
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")
    try:
        result = service.refresh_access_token(
            refresh_token=refresh_cookie,
            csrf_header=csrf_header,
            csrf_cookie=csrf_cookie,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
    except AuthServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.http_status,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "AUTH_ERROR", "message": "Refresh failed"},
        ) from exc

    _set_auth_cookies(
        response=response,
        settings=settings,
        refresh_token=result.refresh_token,
        csrf_token=result.csrf_token,
    )
    return RefreshResponse(accessToken=result.access_token, expiresIn=result.expires_in)


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    request: Request,
    response: Response,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke current or all sessions for current user and clear auth cookies."""
    service = _build_auth_service(db)
    settings = get_settings()
    try:
        service.logout(
            refresh_token=request.cookies.get(settings.refresh_cookie_name),
            current_user=current_user,
            all_devices=payload.allDevices,
        )
        db.commit()
    except AuthServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.http_status,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "AUTH_ERROR", "message": "Logout failed"},
        ) from exc

    _clear_auth_cookies(response=response, settings=settings)
    return {"success": True}


@router.get("/me", response_model=LoginUser)
def me(current_user: CurrentUserContext = Depends(get_current_user)) -> LoginUser:
    """Return current authenticated user profile."""
    return LoginUser(
        id=current_user.user_id,
        email=current_user.email,
        displayName=current_user.display_name,
        role=current_user.role,
        orgId=current_user.org_id,
        status=current_user.status,
    )


@router.get("/context", response_model=AuthContextResponse)
def auth_context(
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthContextResponse:
    """Return authenticated user context including active and available organizations."""
    service = _build_auth_service(db)
    context = service.get_auth_context(current_user=current_user)

    return AuthContextResponse(
        user=LoginUser(
            id=context.user.user_id,
            email=context.user.email,
            displayName=context.user.display_name,
            role=context.user.role,
            orgId=context.user.org_id,
            status=context.user.status,
        ),
        activeOrg=(
            AuthContextOrg(orgId=context.active_org.org_id, orgName=context.active_org.org_name)
            if context.active_org is not None
            else None
        ),
        availableOrgs=[AuthContextOrg(orgId=item.org_id, orgName=item.org_name) for item in context.available_orgs],
        scopeMode=context.scope_mode,
    )
