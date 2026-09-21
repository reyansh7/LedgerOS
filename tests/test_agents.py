"""Test LangGraph agent investigation workflow and audit logging."""

import pytest
from agents.graph import investigation_graph
from core.database import SyncSessionLocal
from core.models.reconciliation import ExceptionCase
from sqlalchemy import select


def test_agent_investigation_flow():
    with SyncSessionLocal() as session:
        exc = session.execute(select(ExceptionCase).limit(1)).scalar_one_or_none()
        assert exc is not None

        initial_state = {
            "case_id": exc.case_id,
            "failure_type": exc.failure_type,
            "primary_entity_type": exc.primary_entity_type,
            "primary_entity_id": exc.primary_entity_id,
            "amount_at_risk": float(exc.amount_at_risk),
            "observed_symptom": exc.observed_symptom,
            "activity_log": [],
        }

    final_state = investigation_graph.invoke(initial_state)
    assert final_state["case_id"] == exc.case_id
    assert final_state.get("root_cause") is not None
    assert final_state.get("confidence_score") > 0.0
    assert len(final_state.get("activity_log", [])) >= 5
