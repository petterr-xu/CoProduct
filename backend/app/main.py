from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    admin_api_keys_router,
    admin_audit_logs_router,
    admin_functional_roles_router,
    admin_member_options_router,
    admin_members_router,
    admin_users_router,
    auth_router,
    files_router,
    history_router,
    prereview_router,
)
from app.core.config import get_settings, validate_security_settings
from app.core.db import Base, SessionLocal, engine
from app.core.logging import configure_logging, log_event
from app.core.schema_compat import backfill_default_functional_roles, ensure_runtime_schema_compatibility
from app.model_client import build_model_client
from app.repositories import UserRepository
from app.rag import ensure_builtin_knowledge
from app.services import AuthService

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
    validate_security_settings(settings)
    Base.metadata.create_all(bind=engine)
    applied_upgrades = ensure_runtime_schema_compatibility(engine)
    if applied_upgrades:
        log_event("schema_compat_applied", columns=applied_upgrades)
    with SessionLocal() as db:
        auth_service = AuthService(settings=settings, repo=UserRepository(db))
        auth_service.ensure_bootstrap_identity()
        backfilled_rows = backfill_default_functional_roles(db)
        if backfilled_rows > 0:
            log_event("functional_role_backfilled", rows=backfilled_rows)
        db.commit()
    ensure_builtin_knowledge(SessionLocal, build_model_client(settings))


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


app.include_router(prereview_router, prefix=settings.api_prefix)
app.include_router(history_router, prefix=settings.api_prefix)
app.include_router(files_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_users_router, prefix=settings.api_prefix)
app.include_router(admin_api_keys_router, prefix=settings.api_prefix)
app.include_router(admin_audit_logs_router, prefix=settings.api_prefix)
app.include_router(admin_members_router, prefix=settings.api_prefix)
app.include_router(admin_functional_roles_router, prefix=settings.api_prefix)
app.include_router(admin_member_options_router, prefix=settings.api_prefix)
