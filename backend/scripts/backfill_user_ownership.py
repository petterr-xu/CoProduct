from __future__ import annotations

"""Backfill org_id/created_by_user_id for legacy business records.

Usage:
    cd backend
    python -m scripts.backfill_user_ownership
"""

from sqlalchemy import and_, select

from app.core.db import SessionLocal
from app.models import RequestModel, SessionModel, UploadedFileModel
from app.repositories import UserRepository


def run() -> None:
    with SessionLocal() as db:
        user_repo = UserRepository(db)
        owner = user_repo.get_user_by_email("owner@coproduct.local")
        if owner is None:
            raise RuntimeError("Bootstrap owner not found. Start application first to seed default owner.")

        membership = user_repo.get_first_active_membership(user_id=owner.id)
        if membership is None:
            raise RuntimeError("Bootstrap owner has no active membership.")

        default_org_id = membership.org_id
        default_user_id = owner.id

        requests = list(
            db.execute(
                select(RequestModel).where(
                    and_(RequestModel.org_id.is_(None), RequestModel.created_by_user_id.is_(None))
                )
            ).scalars()
        )
        sessions = list(
            db.execute(
                select(SessionModel).where(
                    and_(SessionModel.org_id.is_(None), SessionModel.created_by_user_id.is_(None))
                )
            ).scalars()
        )
        files = list(
            db.execute(
                select(UploadedFileModel).where(
                    and_(UploadedFileModel.org_id.is_(None), UploadedFileModel.created_by_user_id.is_(None))
                )
            ).scalars()
        )

        for item in requests:
            item.org_id = default_org_id
            item.created_by_user_id = default_user_id
            db.add(item)
        for item in sessions:
            item.org_id = default_org_id
            item.created_by_user_id = default_user_id
            db.add(item)
        for item in files:
            item.org_id = default_org_id
            item.created_by_user_id = default_user_id
            db.add(item)

        db.commit()
        print(  # noqa: T201
            "Backfill completed:",
            {
                "requests": len(requests),
                "sessions": len(sessions),
                "uploaded_files": len(files),
                "org_id": default_org_id,
                "created_by_user_id": default_user_id,
            },
        )


if __name__ == "__main__":
    run()
