"""API routers."""

from app.api.files import router as files_router
from app.api.history import router as history_router
from app.api.prereview import router as prereview_router

__all__ = ["prereview_router", "history_router", "files_router"]
