"""Initial schema — create all application tables.

Revision ID: 001
Revises:
Create Date: 2026-02-22

Tables created:
    entity_orders
    natural_persons
    agent_records
    documents
    filing_events
    human_kernel_sessions
    audit_events
    webhook_registrations
    webhook_events
    api_keys

PostgreSQL-only migration: uses gen_random_uuid(), JSONB, and
TIMESTAMPTZ (DateTime with timezone=True).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers — used by Alembic
# ---------------------------------------------------------------------------

revision: str = "001"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jsonb() -> sa.types.TypeEngine:
    """Return the PostgreSQL JSONB type."""
    return postgresql.JSONB(astext_type=sa.Text())


def _uuid_pk() -> sa.Column:
    """Primary-key column: UUID, server-side default via gen_random_uuid()."""
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=False),  # stored as text in migration DDL
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # entity_orders                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "entity_orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("jurisdiction", sa.String(10), nullable=False,
                  comment="e.g. DE, WY"),
        sa.Column("vehicle_type", sa.String(30), nullable=False,
                  comment="llc | dao_llc | corporation"),
        sa.Column("service_tier", sa.String(20), nullable=False,
                  server_default="self_serve",
                  comment="self_serve | managed | autonomous"),
        sa.Column("requested_name", sa.String(255), nullable=False),
        sa.Column("formatted_name", sa.String(255), nullable=True,
                  comment="Set after name-formatting step"),
        sa.Column("state", sa.String(40), nullable=False,
                  server_default="draft"),
        sa.Column(
            "state_history",
            _jsonb(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="Array of {state, timestamp, actor, details}",
        ),
        sa.Column("pricing_cents", sa.Integer, nullable=False),
        sa.Column("payment_status", sa.String(20), nullable=False,
                  server_default="unpaid"),
        sa.Column("payment_intent_id", sa.String(255), nullable=True,
                  comment="Stripe PaymentIntent ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", _jsonb(), nullable=True,
                  comment="Arbitrary order metadata"),
    )

    # Indexes on entity_orders
    op.create_index(
        "ix_entity_orders_state",
        "entity_orders",
        ["state"],
    )
    op.create_index(
        "ix_entity_orders_jurisdiction_state",
        "entity_orders",
        ["jurisdiction", "state"],
    )
    op.create_index(
        "ix_entity_orders_payment_status",
        "entity_orders",
        ["payment_status"],
    )
    op.create_index(
        "ix_entity_orders_created_at",
        "entity_orders",
        ["created_at"],
    )

    # ------------------------------------------------------------------ #
    # natural_persons                                                      #
    # ------------------------------------------------------------------ #
    op.create_table(
        "natural_persons",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(30),
            nullable=False,
            comment="member | manager | registered_agent | responsible_party",
        ),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("ssn_vault_ref", sa.String(255), nullable=True),
        sa.Column("address_vault_ref", sa.String(255), nullable=True),
        sa.Column("dob_vault_ref", sa.String(255), nullable=True),
        sa.Column("kyc_status", sa.String(20), nullable=False,
                  server_default="pending"),
        sa.Column("ownership_percentage", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_natural_persons_order_id",
        "natural_persons",
        ["order_id"],
    )
    op.create_index(
        "ix_natural_persons_order_role",
        "natural_persons",
        ["order_id", "role"],
    )

    # ------------------------------------------------------------------ #
    # agent_records                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "agent_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("version_hash", sa.String(64), nullable=True),
        sa.Column(
            "authority_scope",
            _jsonb(),
            nullable=False,
            comment="Describes what the agent is authorized to do",
        ),
        sa.Column("transaction_limit_cents", sa.Integer, nullable=True),
        sa.Column("smart_contract_address", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_agent_records_order_id",
        "agent_records",
        ["order_id"],
    )

    # ------------------------------------------------------------------ #
    # documents                                                            #
    # ------------------------------------------------------------------ #
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doc_type",
            sa.String(50),
            nullable=False,
            comment=(
                "certificate_of_formation | operating_agreement | "
                "agent_authority_schedule | form_ss4 | form_8821 | "
                "banking_resolution | ciia | articles_of_organization | "
                "smart_contract_schedule | bank_pack_cover"
            ),
        ),
        sa.Column("template_version", sa.String(20), nullable=False),
        sa.Column("file_ref", sa.Text, nullable=False,
                  comment="S3 key or local path"),
        sa.Column("file_hash", sa.String(64), nullable=False,
                  comment="SHA-256 hex digest"),
        sa.Column("signing_status", sa.String(20), nullable=False,
                  server_default="unsigned"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_documents_order_id",
        "documents",
        ["order_id"],
    )
    op.create_index(
        "ix_documents_order_type",
        "documents",
        ["order_id", "doc_type"],
    )

    # ------------------------------------------------------------------ #
    # filing_events                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "filing_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filing_type", sa.String(30), nullable=False,
                  comment="state_formation | ein_application | boi_report"),
        sa.Column("channel", sa.String(20), nullable=False,
                  comment="manual | playwright | ra_api | mail"),
        sa.Column("receipt_ref", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("state_confirmation_number", sa.String(100), nullable=True),
        sa.Column("state_filing_date", sa.DateTime(timezone=True),
                  nullable=True),
        sa.Column("expedite_level", sa.String(20), nullable=False,
                  server_default="standard"),
        sa.Column("filing_fee_cents", sa.Integer, nullable=True),
        sa.Column(
            "attempt_number",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("automation_log", _jsonb(), nullable=True),
        sa.Column("metadata", _jsonb(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_filing_events_order_id",
        "filing_events",
        ["order_id"],
    )
    op.create_index(
        "ix_filing_events_order_type",
        "filing_events",
        ["order_id", "filing_type"],
    )
    op.create_index(
        "ix_filing_events_status",
        "filing_events",
        ["status"],
    )

    # ------------------------------------------------------------------ #
    # human_kernel_sessions                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "human_kernel_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending | in_progress | completed | expired",
        ),
        sa.Column(
            "completed_steps",
            _jsonb(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token", name="uq_human_kernel_sessions_token"),
    )

    op.create_index(
        "ix_human_kernel_sessions_order_id",
        "human_kernel_sessions",
        ["order_id"],
    )
    op.create_index(
        "ix_human_kernel_sessions_token",
        "human_kernel_sessions",
        ["token"],
        unique=True,
    )
    op.create_index(
        "ix_human_kernel_sessions_status",
        "human_kernel_sessions",
        ["status"],
    )
    op.create_index(
        "ix_human_kernel_sessions_expires_at",
        "human_kernel_sessions",
        ["expires_at"],
    )

    # ------------------------------------------------------------------ #
    # audit_events                                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("entity_orders.id", ondelete="SET NULL"),
            nullable=True,
            comment="Nullable — some events are system-level",
        ),
        sa.Column(
            "actor",
            sa.String(255),
            nullable=False,
            comment=(
                "system | api_key:{prefix} | "
                "human_kernel:{token_prefix} | ops:{user}"
            ),
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", _jsonb(), nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_audit_events_order_id",
        "audit_events",
        ["order_id"],
    )
    op.create_index(
        "ix_audit_events_actor",
        "audit_events",
        ["actor"],
    )
    op.create_index(
        "ix_audit_events_action",
        "audit_events",
        ["action"],
    )
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
    )

    # ------------------------------------------------------------------ #
    # webhook_registrations                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "webhook_registrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("secret", sa.String(255), nullable=False,
                  comment="HMAC signing secret"),
        sa.Column(
            "events",
            _jsonb(),
            nullable=False,
            comment="Array of event types to subscribe to",
        ),
        sa.Column(
            "active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_webhook_registrations_active",
        "webhook_registrations",
        ["active"],
    )

    # ------------------------------------------------------------------ #
    # webhook_events                                                       #
    # ------------------------------------------------------------------ #
    op.create_table(
        "webhook_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "registration_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("webhook_registrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "attempts",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending | delivered | failed | dead_letter",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_webhook_events_idempotency_key",
        ),
    )

    op.create_index(
        "ix_webhook_events_registration_id",
        "webhook_events",
        ["registration_id"],
    )
    op.create_index(
        "ix_webhook_events_status",
        "webhook_events",
        ["status"],
    )
    op.create_index(
        "ix_webhook_events_next_retry",
        "webhook_events",
        ["next_retry_at"],
    )

    # ------------------------------------------------------------------ #
    # api_keys                                                             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("key_hash", sa.String(64), nullable=False,
                  comment="SHA-256 of the full key"),
        sa.Column("key_prefix", sa.String(8), nullable=False,
                  comment="First 8 chars for display"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "scopes",
            _jsonb(),
            nullable=False,
            server_default=sa.text("""'["*"]'::jsonb"""),
        ),
        sa.Column(
            "active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
    )

    op.create_index(
        "ix_api_keys_key_prefix",
        "api_keys",
        ["key_prefix"],
    )
    op.create_index(
        "ix_api_keys_active",
        "api_keys",
        ["active"],
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # Drop in reverse dependency order (children before parents).

    # No FK dependencies
    op.drop_table("api_keys")

    # webhook_events -> webhook_registrations
    op.drop_table("webhook_events")
    op.drop_table("webhook_registrations")

    # All tables below depend on entity_orders
    op.drop_table("audit_events")
    op.drop_table("human_kernel_sessions")
    op.drop_table("filing_events")
    op.drop_table("documents")
    op.drop_table("agent_records")
    op.drop_table("natural_persons")

    # Parent table last
    op.drop_table("entity_orders")
