from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import files_router, history_router, prereview_router
from app.core.config import get_settings
from app.core.db import Base, SessionLocal, engine
from app.core.logging import configure_logging
from app.model_client import build_model_client
from app.rag import ensure_builtin_knowledge

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

# Allow browser-based frontend apps to call backend APIs in local development.
allow_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_builtin_knowledge(SessionLocal, build_model_client(settings))


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


app.include_router(prereview_router, prefix=settings.api_prefix)
app.include_router(history_router, prefix=settings.api_prefix)
app.include_router(files_router, prefix=settings.api_prefix)
