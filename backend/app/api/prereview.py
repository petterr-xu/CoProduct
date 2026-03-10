from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import verify_api_token
from app.core.config import get_settings
from app.core.db import get_db
from app.repositories import PreReviewRepository
from app.services import PreReviewCreateInput, PreReviewService
from app.workflow import PreReviewWorkflow

router = APIRouter(prefix="/prereview", tags=["prereview"])
settings = get_settings()
workflow = PreReviewWorkflow(settings)


def build_prereview_service(db: Session) -> PreReviewService:
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


@router.post("", response_model=CreatePreReviewResponse, dependencies=[Depends(verify_api_token)])
def create_prereview(payload: CreatePreReviewRequest, db: Session = Depends(get_db)) -> CreatePreReviewResponse:
    service = build_prereview_service(db)
    try:
        result = service.create_prereview(
            PreReviewCreateInput(
                requirement_text=payload.requirementText,
                background_text=payload.backgroundText or None,
                business_domain=payload.businessDomain or None,
                module_hint=payload.moduleHint or None,
                attachments=[{"file_id": item.fileId} for item in payload.attachments],
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


@router.get("/{session_id}", dependencies=[Depends(verify_api_token)])
def get_prereview(session_id: str, db: Session = Depends(get_db)) -> dict:
    service = build_prereview_service(db)
    result = service.get_prereview(session_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "VALIDATION_ERROR", "message": "session not found"},
        )
    return result


@router.post("/{session_id}/regenerate", dependencies=[Depends(verify_api_token)])
def regenerate_prereview(session_id: str, _payload: RegeneratePreReviewRequest) -> dict:
    # M1 only reserves the route for M3 versioning implementation.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "WORKFLOW_ERROR",
            "message": f"regenerate not implemented in M1 for session {session_id}",
        },
    )
