from __future__ import annotations

from app.workflow.state import PreReviewState


class PersistenceNode:
    """Workflow terminal node.

    M1 keeps this node lightweight. Actual DB persistence is handled by PersistenceService
    after graph invocation.
    """

    def __call__(self, state: PreReviewState) -> dict:
        return {"status": "SUCCESS"}

