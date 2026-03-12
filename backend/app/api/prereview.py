from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.permissions import require_write_permission
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.services import PreReviewCreateInput, PreReviewRegenerateInput, PreReviewService
from app.workflow import PreReviewWorkflow

router = APIRouter(prefix="/prereview", tags=["prereview"])
settings = get_settings()
workflow = PreReviewWorkflow(settings)


def build_prereview_service(db: Session) -> PreReviewService:
    """Build service with request-scoped DB session and shared workflow instance."""
    repo = PreReviewRepository(db)
    return PreReviewService(settings=settings, repo=repo, workflow=workflow)


class AttachmentInput(BaseModel):
    fileId: str


class CreatePreReviewRequest(BaseModel):
    requirementText: str = Field(min_length=1)
    backgroundText: str = ""
    businessDomain: str = ""
    moduleHint: str = ""
    attachments: list[AttachmentInput] = Field(default_factory=list)


class CreatePreReviewResponse(BaseModel):
    sessionId: str
    status: str


class RegeneratePreReviewRequest(BaseModel):
    additionalContext: str = ""
    attachments: list[AttachmentInput] = Field(default_factory=list)


@router.post("", response_model=CreatePreReviewResponse)
def create_prereview(
    payload: CreatePreReviewRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatePreReviewResponse:
    """Create a new pre-review session and trigger workflow execution."""
    require_write_permission(current_user)
    service = build_prereview_service(db)
    try:
        result = service.create_prereview(
            PreReviewCreateInput(
                requirement_text=payload.requirementText,
                background_text=payload.backgroundText or None,
                business_domain=payload.businessDomain or None,
                module_hint=payload.moduleHint or None,
                attachments=[{"file_id": item.fileId} for item in payload.attachments],
                current_user=current_user,
            )
        )
        db.commit()
        return CreatePreReviewResponse(**result)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "WORKFLOW_ERROR", "message": "workflow execution failed"},
        ) from exc


@router.get("/{session_id}")
def get_prereview(
    session_id: str,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Query session status and normalized report view for frontend rendering."""
    service = build_prereview_service(db)
    result = service.get_prereview(session_id, current_user=current_user)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "VALIDATION_ERROR", "message": "session not found", "status": "NOT_FOUND"},
        )
    return result


@router.post("/{session_id}/regenerate")
def regenerate_prereview(
    session_id: str,
    payload: RegeneratePreReviewRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Regenerate from an existing session and create a new versioned session."""
    require_write_permission(current_user)
    service = build_prereview_service(db)
    try:
        result = service.regenerate_prereview(
            PreReviewRegenerateInput(
                parent_session_id=session_id,
                additional_context=payload.additionalContext,
                attachments=[{"file_id": item.fileId} for item in payload.attachments],
                current_user=current_user,
            )
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "VALIDATION_ERROR", "message": str(exc), "status": "NOT_FOUND"},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "WORKFLOW_ERROR", "message": "workflow execution failed"},
        ) from exc
