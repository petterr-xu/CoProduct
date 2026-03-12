from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Engine, and_, inspect, select, text, update
from sqlalchemy.orm import Session

from app.models import FunctionalRoleModel, MembershipModel, OrganizationModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Runtime compatibility patch list for legacy SQLite databases.
# `create_all` only creates missing tables, it does not add missing columns.
_LEGACY_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "requests": [
        ("org_id", "VARCHAR(64)"),
        ("created_by_user_id", "VARCHAR(64)"),
    ],
    "sessions": [
        ("org_id", "VARCHAR(64)"),
        ("created_by_user_id", "VARCHAR(64)"),
    ],
    "uploaded_files": [
        ("org_id", "VARCHAR(64)"),
        ("created_by_user_id", "VARCHAR(64)"),
    ],
    "memberships": [
        ("functional_role_id", "VARCHAR(64)"),
    ],
}


def ensure_runtime_schema_compatibility(engine: Engine) -> list[str]:
    """Apply non-destructive compatibility upgrades for existing databases."""
    applied: list[str] = []
    with engine.begin() as conn:
        inspector = inspect(conn)
        table_names = set(inspector.get_table_names())

        for table_name, columns in _LEGACY_COLUMNS.items():
            if table_name not in table_names:
                continue

            current_columns = {item["name"] for item in inspector.get_columns(table_name)}
            for column_name, column_type in columns:
                if column_name in current_columns:
                    continue
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                applied.append(f"{table_name}.{column_name}")
                current_columns.add(column_name)
    return applied


def backfill_default_functional_roles(db: Session) -> int:
    """Ensure each org has `unassigned` role and memberships have `functional_role_id`."""
    org_ids = list(db.execute(select(OrganizationModel.id)).scalars().all())
    updated_rows = 0

    for org_id in org_ids:
        default_role = db.execute(
            select(FunctionalRoleModel)
            .where(and_(FunctionalRoleModel.org_id == org_id, FunctionalRoleModel.code == "unassigned"))
            .limit(1)
        ).scalar_one_or_none()
        if default_role is None:
            default_role = FunctionalRoleModel(
                id=f"frl_{uuid4().hex[:12]}",
                org_id=org_id,
                code="unassigned",
                name="未分配",
                description="默认职能角色",
                is_active=True,
                sort_order=9999,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(default_role)
            db.flush()

        result = db.execute(
            update(MembershipModel)
            .where(and_(MembershipModel.org_id == org_id, MembershipModel.functional_role_id.is_(None)))
            .values(functional_role_id=default_role.id)
        )
        row_count = int(result.rowcount or 0)
        if row_count > 0:
            updated_rows += row_count

    return updated_rows
