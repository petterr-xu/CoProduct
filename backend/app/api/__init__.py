"""API routers."""

from app.api.files import router as files_router
from app.api.history import router as history_router
from app.api.prereview import router as prereview_router
from app.api.auth import router as auth_router
from app.api.admin_users import router as admin_users_router
from app.api.admin_api_keys import router as admin_api_keys_router
from app.api.admin_audit_logs import router as admin_audit_logs_router

__all__ = [
    "prereview_router",
    "history_router",
    "files_router",
    "auth_router",
    "admin_users_router",
    "admin_api_keys_router",
    "admin_audit_logs_router",
]
