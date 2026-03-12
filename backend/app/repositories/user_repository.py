from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import ApiKeyModel, AuditLogModel, AuthSessionModel, MembershipModel, OrganizationModel, UserModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRepository:
    """Persistence operations for user/auth domain."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_organization(self, org_id: str) -> OrganizationModel | None:
        return self.db.get(OrganizationModel, org_id)

    def count_users(self) -> int:
        stmt = select(func.count(UserModel.id))
        return int(self.db.execute(stmt).scalar_one() or 0)

    def get_or_create_organization(self, *, org_id: str, name: str) -> OrganizationModel:
        org = self.db.get(OrganizationModel, org_id)
        if org is None:
            org = OrganizationModel(id=org_id, name=name, status="ACTIVE")
            self.db.add(org)
            self.db.flush()
        return org

    def get_user_by_email(self, email: str) -> UserModel | None:
        stmt: Select[tuple[UserModel]] = select(UserModel).where(UserModel.email == email).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user(self, user_id: str) -> UserModel | None:
        return self.db.get(UserModel, user_id)

    def create_user(self, *, email: str, display_name: str, status: str = "ACTIVE") -> UserModel:
        user = UserModel(email=email, display_name=display_name, status=status)
        self.db.add(user)
        self.db.flush()
        return user

    def update_user_status(self, *, user_id: str, status: str) -> UserModel | None:
        user = self.db.get(UserModel, user_id)
        if user is None:
            return None
        user.status = status
        user.disabled_at = utc_now() if status == "DISABLED" else None
        self.db.add(user)
        self.db.flush()
        return user

    def touch_last_login(self, user_id: str) -> None:
        user = self.db.get(UserModel, user_id)
        if user is None:
            return
        user.last_login_at = utc_now()
        self.db.add(user)

    def get_membership(self, *, user_id: str, org_id: str) -> MembershipModel | None:
        stmt: Select[tuple[MembershipModel]] = (
            select(MembershipModel)
            .where(and_(MembershipModel.user_id == user_id, MembershipModel.org_id == org_id))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_membership_role(self, *, user_id: str, org_id: str, role: str) -> MembershipModel | None:
        membership = self.get_membership(user_id=user_id, org_id=org_id)
        if membership is None:
            return None
        membership.role = role
        self.db.add(membership)
        self.db.flush()
        return membership

    def list_users(
        self,
        *,
        org_id: str,
        query: str | None,
        role: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict]]:
        filters = [MembershipModel.org_id == org_id]
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(
                or_(
                    UserModel.email.ilike(pattern),
                    UserModel.display_name.ilike(pattern),
                )
            )
        if role:
            filters.append(MembershipModel.role == role)
        if status:
            filters.append(UserModel.status == status)

        total_stmt = (
            select(func.count(UserModel.id))
            .select_from(UserModel)
            .join(MembershipModel, MembershipModel.user_id == UserModel.id)
            .where(and_(*filters))
        )
        total = int(self.db.execute(total_stmt).scalar_one() or 0)

        rows = self.db.execute(
            select(UserModel, MembershipModel)
            .select_from(UserModel)
            .join(MembershipModel, MembershipModel.user_id == UserModel.id)
            .where(and_(*filters))
            .order_by(desc(UserModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        items = [
            {
                "id": user.id,
                "email": user.email,
                "displayName": user.display_name,
                "role": membership.role,
                "status": user.status,
                "orgId": membership.org_id,
                "createdAt": user.created_at.isoformat() if user.created_at else "",
                "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
            }
            for user, membership in rows
        ]
        return total, items

    def get_active_membership(self, *, user_id: str, org_id: str) -> MembershipModel | None:
        stmt: Select[tuple[MembershipModel]] = (
            select(MembershipModel)
            .where(
                and_(
                    MembershipModel.user_id == user_id,
                    MembershipModel.org_id == org_id,
                    MembershipModel.status == "ACTIVE",
                )
            )
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_first_active_membership(self, *, user_id: str) -> MembershipModel | None:
        stmt: Select[tuple[MembershipModel]] = (
            select(MembershipModel)
            .where(and_(MembershipModel.user_id == user_id, MembershipModel.status == "ACTIVE"))
            .order_by(MembershipModel.created_at.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_membership(self, *, user_id: str, org_id: str, role: str, status: str = "ACTIVE") -> MembershipModel:
        membership = MembershipModel(user_id=user_id, org_id=org_id, role=role, status=status)
        self.db.add(membership)
        self.db.flush()
        return membership

    def find_api_keys_by_prefix(self, key_prefix: str) -> list[ApiKeyModel]:
        stmt: Select[tuple[ApiKeyModel]] = (
            select(ApiKeyModel).where(ApiKeyModel.key_prefix == key_prefix).order_by(ApiKeyModel.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_api_key(self, key_id: str) -> ApiKeyModel | None:
        return self.db.get(ApiKeyModel, key_id)

    def create_api_key(
        self,
        *,
        user_id: str,
        org_id: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        key_salt: str,
        expires_at: datetime | None,
    ) -> ApiKeyModel:
        api_key = ApiKeyModel(
            user_id=user_id,
            org_id=org_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            key_salt=key_salt,
            expires_at=expires_at,
            status="ACTIVE",
        )
        self.db.add(api_key)
        self.db.flush()
        return api_key

    def mark_api_key_used(self, key_id: str) -> None:
        api_key = self.db.get(ApiKeyModel, key_id)
        if api_key is None:
            return
        api_key.last_used_at = utc_now()
        self.db.add(api_key)

    def list_api_keys(
        self,
        *,
        org_id: str,
        user_id: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict]]:
        filters = [ApiKeyModel.org_id == org_id]
        if user_id:
            filters.append(ApiKeyModel.user_id == user_id)
        if status:
            filters.append(ApiKeyModel.status == status)

        total_stmt = select(func.count(ApiKeyModel.id)).where(and_(*filters))
        total = int(self.db.execute(total_stmt).scalar_one() or 0)

        rows = self.db.execute(
            select(ApiKeyModel)
            .where(and_(*filters))
            .order_by(desc(ApiKeyModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()

        items = [
            {
                "keyId": item.id,
                "userId": item.user_id,
                "keyPrefix": item.key_prefix,
                "status": item.status,
                "name": item.name,
                "expiresAt": item.expires_at.isoformat() if item.expires_at else None,
                "lastUsedAt": item.last_used_at.isoformat() if item.last_used_at else None,
                "createdAt": item.created_at.isoformat() if item.created_at else "",
            }
            for item in rows
        ]
        return total, items

    def revoke_api_key_and_sessions(self, *, key_id: str, org_id: str) -> tuple[ApiKeyModel | None, int]:
        api_key = self.get_api_key(key_id)
        if api_key is None or api_key.org_id != org_id:
            return None, 0

        if api_key.status != "REVOKED":
            api_key.status = "REVOKED"
            api_key.revoked_at = utc_now()
            self.db.add(api_key)

        sessions = list(
            self.db.execute(
                select(AuthSessionModel).where(
                    and_(
                        AuthSessionModel.api_key_id == key_id,
                        AuthSessionModel.status == "ACTIVE",
                    )
                )
            ).scalars()
        )
        for session in sessions:
            session.status = "REVOKED"
            session.revoked_at = utc_now()
            self.db.add(session)

        self.db.flush()
        return api_key, len(sessions)

    def create_auth_session(
        self,
        *,
        session_id: str | None,
        user_id: str,
        org_id: str,
        api_key_id: str | None,
        refresh_token_hash: str,
        expires_at: datetime,
        device_info: str | None,
        ip: str | None,
        user_agent: str | None,
    ) -> AuthSessionModel:
        payload: dict = {}
        if session_id:
            payload["id"] = session_id
        session = AuthSessionModel(
            user_id=user_id,
            org_id=org_id,
            api_key_id=api_key_id,
            refresh_token_hash=refresh_token_hash,
            status="ACTIVE",
            issued_at=utc_now(),
            expires_at=expires_at,
            device_info=device_info,
            ip=ip,
            user_agent=user_agent,
            version=1,
            **payload,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_auth_session(self, session_id: str) -> AuthSessionModel | None:
        return self.db.get(AuthSessionModel, session_id)

    def rotate_auth_session(
        self,
        *,
        session_id: str,
        expected_refresh_hash: str,
        new_refresh_hash: str,
        new_expires_at: datetime,
    ) -> AuthSessionModel | None:
        session = self.db.get(AuthSessionModel, session_id)
        if session is None:
            return None
        if session.status != "ACTIVE":
            return None
        if session.refresh_token_hash != expected_refresh_hash:
            return None

        session.refresh_token_hash = new_refresh_hash
        session.expires_at = new_expires_at
        session.rotated_at = utc_now()
        session.last_seen_at = utc_now()
        session.version += 1
        self.db.add(session)
        self.db.flush()
        return session

    def revoke_auth_session(self, session_id: str) -> bool:
        session = self.db.get(AuthSessionModel, session_id)
        if session is None:
            return False
        session.status = "REVOKED"
        session.revoked_at = utc_now()
        self.db.add(session)
        return True

    def revoke_all_user_sessions(self, *, user_id: str, org_id: str) -> int:
        stmt: Select[tuple[AuthSessionModel]] = select(AuthSessionModel).where(
            and_(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.org_id == org_id,
                AuthSessionModel.status == "ACTIVE",
            )
        )
        sessions = list(self.db.execute(stmt).scalars().all())
        for session in sessions:
            session.status = "REVOKED"
            session.revoked_at = utc_now()
            self.db.add(session)
        return len(sessions)

    def create_audit_log(
        self,
        *,
        org_id: str | None,
        actor_user_id: str | None,
        target_type: str,
        target_id: str | None,
        action: str,
        result: str,
        metadata: dict | None = None,
    ) -> AuditLogModel:
        item = AuditLogModel(
            org_id=org_id,
            actor_user_id=actor_user_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            result=result,
            meta_json=json.dumps(metadata or {}, ensure_ascii=False),
        )
        self.db.add(item)
        self.db.flush()
        return item

    def list_audit_logs(
        self,
        *,
        org_id: str,
        actor_user_id: str | None,
        action: str | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict]]:
        filters = [AuditLogModel.org_id == org_id]
        if actor_user_id:
            filters.append(AuditLogModel.actor_user_id == actor_user_id)
        if action:
            filters.append(AuditLogModel.action == action)

        total_stmt = select(func.count(AuditLogModel.id)).where(and_(*filters))
        total = int(self.db.execute(total_stmt).scalar_one() or 0)

        rows = self.db.execute(
            select(AuditLogModel)
            .where(and_(*filters))
            .order_by(desc(AuditLogModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()

        items = [
            {
                "id": item.id,
                "orgId": item.org_id,
                "actorUserId": item.actor_user_id,
                "targetType": item.target_type,
                "targetId": item.target_id,
                "action": item.action,
                "result": item.result,
                "meta": json.loads(item.meta_json or "{}"),
                "createdAt": item.created_at.isoformat() if item.created_at else "",
            }
            for item in rows
        ]
        return total, items
