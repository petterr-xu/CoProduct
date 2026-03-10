from __future__ import annotations

from fastapi import FastAPI

from app.api import files_router, history_router, prereview_router
from app.core.config import get_settings
from app.core.db import Base, engine
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


app.include_router(prereview_router, prefix=settings.api_prefix)
app.include_router(history_router, prefix=settings.api_prefix)
app.include_router(files_router, prefix=settings.api_prefix)

