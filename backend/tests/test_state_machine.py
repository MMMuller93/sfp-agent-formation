"""Tests for the entity order state machine.

Verifies transition table integrity, valid/invalid transitions,
terminal states, and next-action guidance.
"""

from __future__ import annotations

import pytest

from app.services.state_machine import (
    VALID_TRANSITIONS,
    OrderState,
    can_transition,
    get_next_required_actions,
    is_terminal,
)


# ---------------------------------------------------------------------------
# Transition table integrity
# ---------------------------------------------------------------------------


class TestTransitionTable:
    """Verify the transition table is internally consistent."""

    def test_all_states_have_entries(self):
        """Every OrderState must appear as a key in VALID_TRANSITIONS."""
        for state in OrderState:
            assert state.value in VALID_TRANSITIONS, (
                f"State {state.value!r} missing from VALID_TRANSITIONS"
            )

    def test_all_targets_are_valid_states(self):
        """Every target in the transition table must be a valid OrderState."""
        valid_values = {s.value for s in OrderState}
        for source, targets in VALID_TRANSITIONS.items():
            for target in targets:
                assert target in valid_values, (
                    f"Transition {source!r} -> {target!r}: "
                    f"target is not a valid OrderState"
                )

    def test_no_self_transitions(self):
        """No state should transition to itself."""
        for source, targets in VALID_TRANSITIONS.items():
            assert source not in targets, (
                f"State {source!r} has a self-transition"
            )

    def test_terminal_states_have_no_targets(self):
        """Terminal states (active, failed) must have empty target lists."""
        assert VALID_TRANSITIONS[OrderState.ACTIVE] == []
        assert VALID_TRANSITIONS[OrderState.FAILED] == []

    def test_every_non_terminal_can_reach_failed(self):
        """Every non-terminal state must have 'failed' as a possible target."""
        for state, targets in VALID_TRANSITIONS.items():
            if targets:  # non-terminal
                assert OrderState.FAILED in targets, (
                    f"State {state!r} cannot transition to 'failed'"
                )

    def test_happy_path_is_reachable(self):
        """The full happy path from draft to active must be traversable."""
        happy_path = [
            OrderState.DRAFT,
            OrderState.INTAKE_COMPLETE,
            OrderState.NAME_CHECK_PASSED,
            OrderState.PAYMENT_PENDING,
            OrderState.PAYMENT_COMPLETE,
            OrderState.HUMAN_KERNEL_REQUIRED,
            OrderState.HUMAN_KERNEL_COMPLETED,
            OrderState.DOCS_GENERATED,
            OrderState.STATE_FILING_SUBMITTED,
            OrderState.STATE_CONFIRMED,
            OrderState.EIN_PENDING,
            OrderState.EIN_ISSUED,
            OrderState.BANK_PACK_READY,
            OrderState.ACTIVE,
        ]
        for i in range(len(happy_path) - 1):
            current = happy_path[i]
            next_state = happy_path[i + 1]
            assert can_transition(current, next_state), (
                f"Happy path broken: {current!r} -> {next_state!r} not allowed"
            )


# ---------------------------------------------------------------------------
# can_transition
# ---------------------------------------------------------------------------


class TestCanTransition:
    def test_valid_transition(self):
        assert can_transition("draft", "intake_complete") is True

    def test_invalid_transition(self):
        assert can_transition("draft", "active") is False

    def test_unknown_source_state(self):
        assert can_transition("nonexistent", "active") is False

    def test_terminal_state_cannot_transition(self):
        assert can_transition("active", "draft") is False
        assert can_transition("failed", "draft") is False

    def test_sanctions_blocked_only_to_failed(self):
        assert can_transition("sanctions_blocked", "failed") is True
        assert can_transition("sanctions_blocked", "draft") is False
        assert can_transition("sanctions_blocked", "human_kernel_required") is False


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


class TestIsTerminal:
    def test_active_is_terminal(self):
        assert is_terminal("active") is True

    def test_failed_is_terminal(self):
        assert is_terminal("failed") is True

    def test_draft_is_not_terminal(self):
        assert is_terminal("draft") is False

    def test_unknown_state_is_terminal(self):
        # Unknown states have no transitions → treated as terminal
        assert is_terminal("nonexistent") is True


# ---------------------------------------------------------------------------
# Retry/recovery paths
# ---------------------------------------------------------------------------


class TestRetryPaths:
    def test_name_check_failure_allows_retry(self):
        """Name check failure should allow going back to intake_complete."""
        assert can_transition("name_check_failed", "intake_complete") is True

    def test_payment_failure_allows_retry(self):
        """Payment failure should allow retrying payment."""
        assert can_transition("payment_failed", "payment_pending") is True

    def test_kernel_expired_allows_restart(self):
        """Expired kernel should allow creating a new session."""
        assert can_transition("kernel_expired", "human_kernel_required") is True

    def test_filing_rejected_allows_regen(self):
        """Filing rejection should allow regenerating docs."""
        assert can_transition("filing_rejected", "docs_generated") is True

    def test_ein_manual_review_allows_issuance(self):
        """EIN manual review should allow issuing EIN."""
        assert can_transition("ein_manual_review", "ein_issued") is True


# ---------------------------------------------------------------------------
# OrderState enum
# ---------------------------------------------------------------------------


class TestOrderStateEnum:
    def test_str_serialization(self):
        """OrderState values should serialize to plain strings."""
        assert str(OrderState.DRAFT) == "draft"
        assert str(OrderState.ACTIVE) == "active"

    def test_state_count(self):
        """Should have exactly 21 states."""
        assert len(OrderState) == 21

    def test_comparison_with_strings(self):
        """StrEnum values should compare equal to their string values."""
        assert OrderState.DRAFT == "draft"
        assert OrderState.ACTIVE == "active"
