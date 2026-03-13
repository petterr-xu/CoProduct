from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.db import Base
from app.repositories import PreReviewRepository
from app.services.prereview_service import PreReviewCreateInput, PreReviewService
from app.services.workflow_runner import WorkflowRunner


class _StubWorkflow:
    def invoke(self, state: dict) -> dict:
        return {
            **state,
            "status": "DONE",
            "capability_judgement": {"status": "SUPPORTED"},
            "report": {"summary": "done"},
            "evidence_pack": [],
        }


def _build_session_local(tmp_path: Path):
    db_path = tmp_path / "phase15.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _build_settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=str(tmp_path / "uploads"),
        workflow_queue_maxsize=8,
        workflow_worker_count=1,
        workflow_enqueue_timeout_seconds=0.5,
        workflow_task_timeout_seconds=10,
        workflow_max_retries=0,
        workflow_recover_limit=50,
    )


def test_create_prereview_persists_queued_workflow_job(tmp_path: Path) -> None:
    SessionLocal = _build_session_local(tmp_path)
    settings = _build_settings(tmp_path)

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        service = PreReviewService(settings=settings, repo=repo)

        submission = service.create_prereview(PreReviewCreateInput(requirement_text="需要支持导出能力"))
        db.commit()

        session = repo.get_session(submission.session_id)
        job = repo.get_workflow_job_by_session(submission.session_id)
        assert session is not None
        assert session.status == "PROCESSING"
        assert job is not None
        assert job.status == "QUEUED"

        payload = json.loads(job.payload_json)
        assert payload["session_id"] == submission.session_id
        assert payload["task_type"] == "CREATE"


def test_workflow_runner_executes_enqueued_submission(tmp_path: Path) -> None:
    SessionLocal = _build_session_local(tmp_path)
    settings = _build_settings(tmp_path)

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        service = PreReviewService(settings=settings, repo=repo)
        submission = service.create_prereview(PreReviewCreateInput(requirement_text="测试异步执行"))
        db.commit()

    runner = WorkflowRunner(settings=settings, session_factory=SessionLocal, workflow=_StubWorkflow())

    async def _run() -> None:
        await runner.start()
        await runner.enqueue(submission.task)
        assert runner.queue_depth >= 0
        if runner._queue is not None:
            await runner._queue.join()
        await runner.stop()

    asyncio.run(_run())

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        session = repo.get_session(submission.session_id)
        job = repo.get_workflow_job_by_session(submission.session_id)
        report = repo.get_report(submission.session_id)
        assert session is not None
        assert session.status == "DONE"
        assert job is not None
        assert job.status == "DONE"
        assert report is not None


def test_workflow_runner_recovers_unfinished_jobs_on_startup(tmp_path: Path) -> None:
    SessionLocal = _build_session_local(tmp_path)
    settings = _build_settings(tmp_path)

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        service = PreReviewService(settings=settings, repo=repo)
        submission = service.create_prereview(PreReviewCreateInput(requirement_text="恢复任务测试"))
        db.commit()

    runner = WorkflowRunner(settings=settings, session_factory=SessionLocal, workflow=_StubWorkflow())

    async def _run() -> None:
        await runner.start()
        if runner._queue is not None:
            await runner._queue.join()
        await runner.stop()

    asyncio.run(_run())

    with SessionLocal() as db:
        repo = PreReviewRepository(db)
        session = repo.get_session(submission.session_id)
        job = repo.get_workflow_job_by_session(submission.session_id)
        assert session is not None
        assert session.status == "DONE"
        assert job is not None
        assert job.status == "DONE"
