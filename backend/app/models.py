"""SQLAlchemy 2.0 ORM models for the SFP Entity Formation service.

Uses DeclarativeBase with Mapped[] type annotations for full async
compatibility with asyncpg.  All UUIDs use PostgreSQL-native gen_random_uuid()
as server-side defaults.  JSONB columns use the PostgreSQL dialect type.
"""

from __future__ import annotations

import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all models."""

    type_annotation_map = {
        dict: JSONB,
        list: JSONB,
        UUID: PG_UUID(as_uuid=True),
    }


# ---------------------------------------------------------------------------
# EntityOrder
# ---------------------------------------------------------------------------

class EntityOrder(Base):
    __tablename__ = "entity_orders"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    jurisdiction: Mapped[str] = mapped_column(String(10), nullable=False, comment="e.g. DE, WY")
    vehicle_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="llc | dao_llc | corporation"
    )
    service_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="self_serve",
        comment="self_serve | managed | autonomous",
    )
    requested_name: Mapped[str] = mapped_column(String(255), nullable=False)
    formatted_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Set after name-formatting step"
    )

    state: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="draft", index=True,
    )
    state_history: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
        comment="Array of {state, timestamp, actor, details}",
    )

    pricing_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="unpaid",
    )
    payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Stripe PaymentIntent ID",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now(),
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, comment="Arbitrary order metadata",
    )

    # --- relationships ---
    persons: Mapped[list[NaturalPerson]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )
    agents: Mapped[list[AgentRecord]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )
    filing_events: Mapped[list[FilingEvent]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )
    human_kernel_sessions: Mapped[list[HumanKernelSession]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_entity_orders_jurisdiction_state", "jurisdiction", "state"),
        Index("ix_entity_orders_payment_status", "payment_status"),
        Index("ix_entity_orders_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EntityOrder id={self.id!s} name={self.requested_name!r} "
            f"state={self.state!r} jurisdiction={self.jurisdiction!r}>"
        )


# ---------------------------------------------------------------------------
# NaturalPerson
# ---------------------------------------------------------------------------

class NaturalPerson(Base):
    __tablename__ = "natural_persons"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("entity_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="member | manager | registered_agent | responsible_party",
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # PII vault references — opaque tokens, never raw PII in this database
    ssn_vault_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_vault_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dob_vault_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    kyc_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending",
    )
    ownership_percentage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    order: Mapped[EntityOrder] = relationship(back_populates="persons")

    __table_args__ = (
        Index("ix_natural_persons_order_role", "order_id", "role"),
    )

    def __repr__(self) -> str:
        return (
            f"<NaturalPerson id={self.id!s} role={self.role!r} "
            f"name={self.legal_name!r}>"
        )


# ---------------------------------------------------------------------------
# AgentRecord
# ---------------------------------------------------------------------------

class AgentRecord(Base):
    __tablename__ = "agent_records"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("entity_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    authority_scope: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Describes what the agent is authorized to do",
    )
    transaction_limit_cents: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
    )
    smart_contract_address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    order: Mapped[EntityOrder] = relationship(back_populates="agents")

    def __repr__(self) -> str:
        return f"<AgentRecord id={self.id!s} name={self.display_name!r}>"


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("entity_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    doc_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment=(
            "certificate_of_formation | operating_agreement | agent_authority_schedule | "
            "form_ss4 | form_8821 | banking_resolution | ciia | articles_of_organization | "
            "smart_contract_schedule | bank_pack_cover"
        ),
    )
    template_version: Mapped[str] = mapped_column(String(20), nullable=False)
    file_ref: Mapped[str] = mapped_column(
        Text, nullable=False, comment="S3 key or local path",
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 hex digest",
    )
    signing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="unsigned",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    order: Mapped[EntityOrder] = relationship(back_populates="documents")

    __table_args__ = (
        Index("ix_documents_order_type", "order_id", "doc_type"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id!s} type={self.doc_type!r}>"


# ---------------------------------------------------------------------------
# FilingEvent
# ---------------------------------------------------------------------------

class FilingEvent(Base):
    __tablename__ = "filing_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("entity_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    filing_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="state_formation | ein_application | boi_report",
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="manual | playwright | ra_api | mail",
    )
    receipt_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    state_confirmation_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    state_filing_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    expedite_level: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="standard",
    )
    filing_fee_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempt_number: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"),
    )
    automation_log: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    order: Mapped[EntityOrder] = relationship(back_populates="filing_events")

    __table_args__ = (
        Index("ix_filing_events_order_type", "order_id", "filing_type"),
        Index("ix_filing_events_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<FilingEvent id={self.id!s} type={self.filing_type!r} "
            f"status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# HumanKernelSession
# ---------------------------------------------------------------------------

class HumanKernelSession(Base):
    __tablename__ = "human_kernel_sessions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("entity_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending",
        comment="pending | in_progress | completed | expired",
    )
    completed_steps: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
    )

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # --- relationships ---
    order: Mapped[EntityOrder] = relationship(back_populates="human_kernel_sessions")

    __table_args__ = (
        Index("ix_human_kernel_sessions_status", "status"),
        Index("ix_human_kernel_sessions_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<HumanKernelSession id={self.id!s} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entity_orders.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="Nullable — some events are system-level",
    )
    actor: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="system | api_key:{prefix} | human_kernel:{token_prefix} | ops:{user}",
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    artifact_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    order: Mapped[Optional[EntityOrder]] = relationship(back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_events_actor", "actor"),
        Index("ix_audit_events_action", "action"),
        Index("ix_audit_events_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id!s} action={self.action!r} "
            f"actor={self.actor!r}>"
        )


# ---------------------------------------------------------------------------
# WebhookRegistration
# ---------------------------------------------------------------------------

class WebhookRegistration(Base):
    __tablename__ = "webhook_registrations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="HMAC signing secret",
    )
    events: Mapped[list] = mapped_column(
        JSONB, nullable=False, comment="Array of event types to subscribe to",
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    webhook_events: Mapped[list[WebhookEvent]] = relationship(
        back_populates="registration", cascade="all, delete-orphan", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_webhook_registrations_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<WebhookRegistration id={self.id!s} url={self.url!r}>"


# ---------------------------------------------------------------------------
# WebhookEvent
# ---------------------------------------------------------------------------

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    registration_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("webhook_registrations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"),
    )
    last_attempt_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    next_retry_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending",
        comment="pending | delivered | failed | dead_letter",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # --- relationships ---
    registration: Mapped[WebhookRegistration] = relationship(
        back_populates="webhook_events",
    )

    __table_args__ = (
        Index("ix_webhook_events_status", "status"),
        Index("ix_webhook_events_next_retry", "next_retry_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent id={self.id!s} type={self.event_type!r} "
            f"status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# ApiKey
# ---------------------------------------------------------------------------

class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    key_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="SHA-256 of the full key",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="First 8 chars for display",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("""'["*"]'::jsonb"""),
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
    )
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_api_keys_key_prefix", "key_prefix"),
        Index("ix_api_keys_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<ApiKey id={self.id!s} prefix={self.key_prefix!r} name={self.name!r}>"
