from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.permissions import require_write_permission
from app.core.user_context import CurrentUserContext
from app.repositories import PreReviewRepository
from app.services import (
    PreReviewCreateInput,
    PreReviewRegenerateInput,
    PreReviewService,
    SubmissionRejectedError,
    WorkflowRunner,
)

router = APIRouter(prefix="/prereview", tags=["prereview"])
settings = get_settings()


def build_prereview_service(db: Session) -> PreReviewService:
    """Build service with request-scoped DB session."""
    repo = PreReviewRepository(db)
    return PreReviewService(settings=settings, repo=repo)


def get_workflow_runner(request: Request) -> WorkflowRunner:
    runner = getattr(request.app.state, "workflow_runner", None)
    if runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "SUBMISSION_TIMEOUT", "message": "workflow runner unavailable"},
        )
    return runner


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


@router.post("", response_model=CreatePreReviewResponse, status_code=status.HTTP_202_ACCEPTED)
def create_prereview(
    request: Request,
    payload: CreatePreReviewRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatePreReviewResponse:
    """Create a pre-review session and enqueue async workflow execution."""
    require_write_permission(current_user)
    service = build_prereview_service(db)
    runner = get_workflow_runner(request)
    try:
        submission = service.create_prereview(
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
            detail={"error_code": "WORKFLOW_ERROR", "message": "workflow submission failed"},
        ) from exc

    try:
        runner.enqueue_blocking(submission.task)
    except SubmissionRejectedError as exc:
        runner.mark_submission_failed(session_id=submission.session_id, error_code=exc.error_code, message=exc.message)
        raise HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message}) from exc
    except Exception as exc:  # noqa: BLE001
        runner.mark_submission_failed(
            session_id=submission.session_id,
            error_code="SUBMISSION_TIMEOUT",
            message="workflow submission failed unexpectedly",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SUBMISSION_TIMEOUT", "message": "workflow submission failed unexpectedly"},
        ) from exc

    return CreatePreReviewResponse(**submission.to_response())


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


@router.post("/{session_id}/regenerate", response_model=CreatePreReviewResponse, status_code=status.HTTP_202_ACCEPTED)
def regenerate_prereview(
    request: Request,
    session_id: str,
    payload: RegeneratePreReviewRequest,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatePreReviewResponse:
    """Regenerate a session and enqueue async workflow execution."""
    require_write_permission(current_user)
    service = build_prereview_service(db)
    runner = get_workflow_runner(request)
    try:
        submission = service.regenerate_prereview(
            PreReviewRegenerateInput(
                parent_session_id=session_id,
                additional_context=payload.additionalContext,
                attachments=[{"file_id": item.fileId} for item in payload.attachments],
                current_user=current_user,
            )
        )
        db.commit()
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
            detail={"error_code": "WORKFLOW_ERROR", "message": "workflow submission failed"},
        ) from exc

    try:
        runner.enqueue_blocking(submission.task)
    except SubmissionRejectedError as exc:
        runner.mark_submission_failed(session_id=submission.session_id, error_code=exc.error_code, message=exc.message)
        raise HTTPException(status_code=exc.http_status, detail={"error_code": exc.error_code, "message": exc.message}) from exc
    except Exception as exc:  # noqa: BLE001
        runner.mark_submission_failed(
            session_id=submission.session_id,
            error_code="SUBMISSION_TIMEOUT",
            message="workflow submission failed unexpectedly",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SUBMISSION_TIMEOUT", "message": "workflow submission failed unexpectedly"},
        ) from exc

    return CreatePreReviewResponse(**submission.to_response())
