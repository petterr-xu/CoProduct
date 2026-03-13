from __future__ import annotations

"""Background workflow runner for async prereview submission."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import log_event
from app.repositories import PreReviewRepository
from app.services.persistence_service import PersistenceService
from app.workflow import PreReviewState, PreReviewWorkflow


@dataclass
class WorkflowTaskEnvelope:
    """Serializable task payload queued for async workflow execution."""

    task_type: str
    session_id: str
    request_id: str
    parent_session_id: str | None
    version: int
    org_id: str | None
    actor_user_id: str | None
    trace_id: str | None
    initial_state: PreReviewState

    def to_payload(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "parent_session_id": self.parent_session_id,
            "version": self.version,
            "org_id": self.org_id,
            "actor_user_id": self.actor_user_id,
            "trace_id": self.trace_id,
            "initial_state": self.initial_state,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> WorkflowTaskEnvelope:
        return cls(
            task_type=str(payload.get("task_type", "CREATE")),
            session_id=str(payload["session_id"]),
            request_id=str(payload["request_id"]),
            parent_session_id=payload.get("parent_session_id"),
            version=int(payload.get("version", 1)),
            org_id=payload.get("org_id"),
            actor_user_id=payload.get("actor_user_id"),
            trace_id=payload.get("trace_id"),
            initial_state=payload["initial_state"],
        )


class SubmissionRejectedError(RuntimeError):
    """Base error for submission acceptance failures."""

    def __init__(self, *, error_code: str, message: str, http_status: int) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.http_status = http_status


class SubmissionQueueFullError(SubmissionRejectedError):
    def __init__(self, message: str = "workflow queue is full") -> None:
        super().__init__(error_code="SUBMISSION_QUEUE_FULL", message=message, http_status=429)


class SubmissionTimeoutError(SubmissionRejectedError):
    def __init__(self, message: str = "workflow submission timed out") -> None:
        super().__init__(error_code="SUBMISSION_TIMEOUT", message=message, http_status=504)


class RunnerNotReadyError(SubmissionRejectedError):
    def __init__(self, message: str = "workflow runner is not ready") -> None:
        super().__init__(error_code="SUBMISSION_TIMEOUT", message=message, http_status=503)


class WorkflowRunner:
    """In-process queue + worker runner.

    Accepts workflow tasks quickly in API request path, then executes workflow in
    background workers and persists final state updates.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: Callable[[], Session],
        workflow: PreReviewWorkflow | None = None,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.workflow = workflow or PreReviewWorkflow(settings)

        self._queue: asyncio.Queue[WorkflowTaskEnvelope | None] | None = None
        self._workers: list[asyncio.Task[None]] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._started = False
        self._stopping = False

        self._accepted_count = 0
        self._enqueue_failed_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._total_execute_ms = 0.0

    @property
    def queue_depth(self) -> int:
        if self._queue is None:
            return 0
        return int(self._queue.qsize())

    @property
    def worker_busy(self) -> int:
        return sum(1 for task in self._workers if not task.done())

    @property
    def avg_execute_ms(self) -> float:
        if self._completed_count == 0:
            return 0.0
        return self._total_execute_ms / self._completed_count

    async def start(self) -> None:
        if self._started:
            return
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue(maxsize=max(1, self.settings.workflow_queue_maxsize))
        self._stopping = False
        worker_count = max(1, self.settings.workflow_worker_count)
        self._workers = [
            asyncio.create_task(self._worker_loop(index), name=f"workflow-runner-{index}")
            for index in range(worker_count)
        ]
        self._started = True
        await self.recover_unfinished_jobs()
        log_event("workflow_runner_started", worker_count=worker_count, queue_maxsize=self.settings.workflow_queue_maxsize)

    async def stop(self) -> None:
        if not self._started or self._queue is None:
            return
        self._stopping = True
        for _ in self._workers:
            await self._queue.put(None)
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._started = False
        log_event(
            "workflow_runner_stopped",
            queue_depth=self.queue_depth,
            accepted_count=self._accepted_count,
            enqueue_failed_count=self._enqueue_failed_count,
            completed_count=self._completed_count,
            failed_count=self._failed_count,
            avg_execute_ms=round(self.avg_execute_ms, 2),
        )

    def enqueue_blocking(self, task: WorkflowTaskEnvelope) -> None:
        if self._loop is None or not self._started:
            raise RunnerNotReadyError()
        timeout = max(0.1, float(self.settings.workflow_enqueue_timeout_seconds) + 1.0)
        future = asyncio.run_coroutine_threadsafe(self.enqueue(task), self._loop)
        try:
            future.result(timeout=timeout)
        except TimeoutError as exc:
            self._enqueue_failed_count += 1
            raise SubmissionTimeoutError() from exc

    async def enqueue(self, task: WorkflowTaskEnvelope, *, source: str = "api") -> None:
        if self._queue is None or not self._started or self._stopping:
            self._enqueue_failed_count += 1
            raise RunnerNotReadyError()

        if self._queue.full():
            self._enqueue_failed_count += 1
            raise SubmissionQueueFullError()

        try:
            await asyncio.wait_for(
                self._queue.put(task),
                timeout=max(0.1, float(self.settings.workflow_enqueue_timeout_seconds)),
            )
        except asyncio.TimeoutError as exc:
            self._enqueue_failed_count += 1
            raise SubmissionTimeoutError() from exc

        self._accepted_count += 1
        log_event(
            "workflow_submission_enqueued",
            source=source,
            session_id=task.session_id,
            request_id=task.request_id,
            queue_depth=self.queue_depth,
            accepted_count=self._accepted_count,
        )

    async def recover_unfinished_jobs(self) -> None:
        if self._queue is None:
            return

        with self.session_factory() as db:
            repo = PreReviewRepository(db)
            jobs = repo.list_recoverable_workflow_jobs(limit=max(1, self.settings.workflow_recover_limit))
            recovered_tasks: list[WorkflowTaskEnvelope] = []
            for job in jobs:
                try:
                    payload = json.loads(job.payload_json)
                    task = WorkflowTaskEnvelope.from_payload(payload)
                except Exception as exc:  # noqa: BLE001
                    repo.mark_workflow_job_failed(job.session_id, error_message=f"recover_payload_error: {exc}")
                    repo.update_session_status(
                        session_id=job.session_id,
                        status="FAILED",
                        error_message=f"recover payload decode failed: {exc}",
                    )
                    continue
                repo.mark_workflow_job_queued(job.session_id, error_message="recovered_on_startup")
                recovered_tasks.append(task)
            db.commit()

        for task in recovered_tasks:
            try:
                await self.enqueue(task, source="recover")
            except SubmissionRejectedError as exc:
                self.mark_submission_failed(
                    session_id=task.session_id,
                    error_code=exc.error_code,
                    message=exc.message,
                )
                log_event(
                    "workflow_recover_enqueue_failed",
                    session_id=task.session_id,
                    error_code=exc.error_code,
                    error_message=exc.message,
                )
        if recovered_tasks:
            log_event("workflow_recovered", count=len(recovered_tasks))

    def mark_submission_failed(self, *, session_id: str, error_code: str, message: str) -> None:
        full_message = f"{error_code}: {message}"
        with self.session_factory() as db:
            repo = PreReviewRepository(db)
            repo.mark_workflow_job_failed(session_id, error_message=full_message)
            repo.update_session_status(session_id=session_id, status="FAILED", error_message=full_message)
            db.commit()
        log_event("workflow_submission_rejected", session_id=session_id, error_code=error_code, error_message=message)

    async def _worker_loop(self, worker_index: int) -> None:
        if self._queue is None:
            return
        while True:
            task = await self._queue.get()
            if task is None:
                self._queue.task_done()
                return

            started = monotonic()
            try:
                await asyncio.to_thread(self._execute_task_with_retry, task)
            except Exception as exc:  # noqa: BLE001
                self._failed_count += 1
                log_event(
                    "workflow_runner_worker_error",
                    worker_index=worker_index,
                    session_id=task.session_id,
                    error_message=str(exc),
                )
            finally:
                elapsed_ms = (monotonic() - started) * 1000
                self._total_execute_ms += elapsed_ms
                self._completed_count += 1
                self._queue.task_done()

    def _execute_task_with_retry(self, task: WorkflowTaskEnvelope) -> None:
        max_retries = max(0, self.settings.workflow_max_retries)
        for _ in range(max_retries + 1):
            try:
                self._execute_task(task)
                return
            except Exception as exc:  # noqa: BLE001
                if self._is_retryable(exc):
                    with self.session_factory() as db:
                        repo = PreReviewRepository(db)
                        repo.mark_workflow_job_queued(task.session_id, error_message=str(exc))
                        db.commit()
                    continue

                self._failed_count += 1
                self._mark_execution_failed(task=task, error_message=str(exc))
                return
        self._failed_count += 1
        self._mark_execution_failed(task=task, error_message="retry budget exhausted")

    def _execute_task(self, task: WorkflowTaskEnvelope) -> None:
        with self.session_factory() as db:
            repo = PreReviewRepository(db)
            persistence = PersistenceService(repo)
            repo.mark_workflow_job_running(task.session_id)
            db.commit()

            final_state = self._invoke_with_timeout(task.initial_state)
            persistence.persist_workflow_result(final_state)
            repo.mark_workflow_job_done(task.session_id)
            db.commit()

        log_event(
            "workflow_completed",
            request_id=task.request_id,
            session_id=task.session_id,
            status=final_state.get("status", "DONE"),
        )

    def _mark_execution_failed(self, *, task: WorkflowTaskEnvelope, error_message: str) -> None:
        error_code, persisted_message = self._extract_error_code(error_message)
        with self.session_factory() as db:
            repo = PreReviewRepository(db)
            persistence = PersistenceService(repo)
            persistence.persist_workflow_failure(task.session_id, persisted_message)
            repo.mark_workflow_job_failed(task.session_id, error_message=persisted_message)
            db.commit()

        log_event(
            "workflow_failed",
            request_id=task.request_id,
            session_id=task.session_id,
            status="FAILED",
            error_code=error_code,
            error_message=persisted_message,
        )

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        return isinstance(exc, (TimeoutError, ConnectionError))

    def _invoke_with_timeout(self, state: PreReviewState) -> PreReviewState:
        timeout_seconds = max(1.0, float(self.settings.workflow_task_timeout_seconds))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.workflow.invoke, state)
            try:
                return future.result(timeout=timeout_seconds)
            except FuturesTimeoutError as exc:
                raise TimeoutError(f"workflow task timed out after {timeout_seconds}s") from exc

    @staticmethod
    def _extract_error_code(error_message: str) -> tuple[str, str]:
        known_codes = {
            "MODEL_SCHEMA_ERROR",
            "MODEL_PROVIDER_ERROR",
            "MODEL_TIMEOUT",
            "MODEL_LANGUAGE_ERROR",
            "WORKFLOW_ERROR",
        }
        prefix, sep, rest = error_message.partition(":")
        if sep and prefix in known_codes:
            normalized = rest.strip() or error_message
            return prefix, f"{prefix}: {normalized}"
        return "WORKFLOW_ERROR", error_message
