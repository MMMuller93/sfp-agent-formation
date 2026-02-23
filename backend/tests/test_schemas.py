"""Tests for Pydantic schemas — validation, serialization, edge cases."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.entity_order import (
    ActionItem,
    AgentInput,
    CreateOrderRequest,
    MemberInput,
    OrderResponse,
    OrderSummary,
)
from app.schemas.common import ErrorResponse, HealthResponse, PaginationParams
from app.schemas.webhook import CreateWebhookRequest


# ---------------------------------------------------------------------------
# MemberInput
# ---------------------------------------------------------------------------


class TestMemberInput:
    def test_valid_member(self):
        m = MemberInput(legal_name="Jane Doe", email="jane@example.com", role="member")
        assert m.legal_name == "Jane Doe"
        assert m.role == "member"

    def test_invalid_role(self):
        with pytest.raises(ValidationError, match="role must be one of"):
            MemberInput(legal_name="Jane", role="ceo")

    def test_ownership_bounds(self):
        # Valid
        MemberInput(legal_name="Jane", ownership_percentage=0.0)
        MemberInput(legal_name="Jane", ownership_percentage=100.0)

        # Invalid
        with pytest.raises(ValidationError):
            MemberInput(legal_name="Jane", ownership_percentage=-1.0)
        with pytest.raises(ValidationError):
            MemberInput(legal_name="Jane", ownership_percentage=101.0)

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            MemberInput(legal_name="", role="member")


# ---------------------------------------------------------------------------
# AgentInput
# ---------------------------------------------------------------------------


class TestAgentInput:
    def test_valid_agent(self):
        a = AgentInput(
            display_name="Treasury Agent",
            authority_scope={"can_sign_checks": True},
        )
        assert a.display_name == "Treasury Agent"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            AgentInput(display_name="", authority_scope={})


# ---------------------------------------------------------------------------
# CreateOrderRequest
# ---------------------------------------------------------------------------


class TestCreateOrderRequest:
    def test_valid_request(self):
        r = CreateOrderRequest(
            jurisdiction="DE",
            vehicle_type="llc",
            requested_name="Test LLC",
            members=[MemberInput(legal_name="Jane Doe")],
        )
        assert r.jurisdiction == "DE"
        assert r.service_tier == "self_serve"  # default

    def test_no_members_rejected(self):
        with pytest.raises(ValidationError, match="at least"):
            CreateOrderRequest(
                jurisdiction="DE",
                vehicle_type="llc",
                requested_name="Test LLC",
                members=[],
            )

    def test_invalid_vehicle_type(self):
        with pytest.raises(ValidationError, match="vehicle_type"):
            CreateOrderRequest(
                jurisdiction="DE",
                vehicle_type="partnership",
                requested_name="Test",
                members=[MemberInput(legal_name="Jane")],
            )

    def test_invalid_service_tier(self):
        with pytest.raises(ValidationError, match="service_tier"):
            CreateOrderRequest(
                jurisdiction="DE",
                vehicle_type="llc",
                requested_name="Test",
                service_tier="premium",
                members=[MemberInput(legal_name="Jane")],
            )

    def test_with_agent(self):
        r = CreateOrderRequest(
            jurisdiction="WY",
            vehicle_type="dao_llc",
            requested_name="DAO Test",
            members=[MemberInput(legal_name="Jane")],
            agent=AgentInput(
                display_name="Agent",
                authority_scope={"level": "full"},
                transaction_limit_cents=100000,
            ),
        )
        assert r.agent is not None
        assert r.agent.transaction_limit_cents == 100000


# ---------------------------------------------------------------------------
# PaginationParams
# ---------------------------------------------------------------------------


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.per_page == 20
        assert p.offset == 0

    def test_offset_calculation(self):
        p = PaginationParams(page=3, per_page=10)
        assert p.offset == 20

    def test_page_must_be_positive(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_per_page_max(self):
        with pytest.raises(ValidationError):
            PaginationParams(per_page=101)


# ---------------------------------------------------------------------------
# ActionItem
# ---------------------------------------------------------------------------


class TestActionItem:
    def test_valid_action(self):
        a = ActionItem(
            action="complete_intake",
            endpoint="POST /v1/entity-orders/123/intake",
            description="Submit details",
            required=True,
        )
        assert a.required is True

    def test_nullable_endpoint(self):
        a = ActionItem(
            action="await_confirmation",
            endpoint=None,
            description="Waiting",
            required=False,
        )
        assert a.endpoint is None


# ---------------------------------------------------------------------------
# Webhook schemas
# ---------------------------------------------------------------------------


class TestWebhookSchemas:
    def test_valid_webhook(self):
        w = CreateWebhookRequest(
            url="https://example.com/hook",
            events=["order.state_changed"],
        )
        assert str(w.url) == "https://example.com/hook"

    def test_empty_events_rejected(self):
        with pytest.raises(ValidationError):
            CreateWebhookRequest(
                url="https://example.com/hook",
                events=[],
            )
