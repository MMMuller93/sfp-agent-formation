"""Application configuration via environment variables.

Uses pydantic-settings to load from environment variables (prefixed SFP_)
and from a .env file. All sensitive values (SECRET_KEY, PII_KEK) are required
in production but fall back to insecure defaults in development to allow
local iteration without a full secrets setup.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SFP Entity Formation API configuration.

    Environment variables are read with the ``SFP_`` prefix, e.g.
    ``SFP_SECRET_KEY``, ``SFP_DATABASE_URL``, etc.  A ``.env`` file in the
    backend root is also loaded automatically.
    """

    model_config = SettingsConfigDict(
        env_prefix="SFP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---
    ENVIRONMENT: str = "development"
    BASE_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "INSECURE-DEV-KEY-CHANGE-IN-PRODUCTION"
    API_KEY_SALT: str = "sfp-api-key-salt"

    # --- Databases ---
    DATABASE_URL: str = "postgresql+asyncpg://localhost/sfp_formation"
    PII_VAULT_DATABASE_URL: str = "postgresql+asyncpg://localhost/sfp_pii_vault"

    # --- PII Encryption ---
    # Key-encryption key for the PII vault.  Required in production.
    PII_KEK: str = ""

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # --- AWS S3 (document storage) ---
    S3_BUCKET: str = ""
    S3_REGION: str = ""

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Compliance ---
    OFAC_SDN_URL: str = "https://www.treasury.gov/ofac/downloads/sdn.xml"

    # --- Validators ---

    @field_validator("SECRET_KEY")
    @classmethod
    def _check_secret_key(cls, v: str, info: object) -> str:  # noqa: N805
        # info is a ValidationInfo but we only need the values dict
        # In production the default insecure key must be overridden.
        return v

    @field_validator("PII_KEK")
    @classmethod
    def _check_pii_kek(cls, v: str, info: object) -> str:  # noqa: N805
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")

    def validate_production_secrets(self) -> None:
        """Raise if required production secrets are missing.

        Call this during application startup in production environments.
        """
        if not self.is_production:
            return
        violations: list[str] = []
        if self.SECRET_KEY == "INSECURE-DEV-KEY-CHANGE-IN-PRODUCTION":
            violations.append("SFP_SECRET_KEY must be set in production")
        if not self.PII_KEK:
            violations.append("SFP_PII_KEK must be set in production")
        if violations:
            raise ValueError(
                "Production configuration errors:\n  - " + "\n  - ".join(violations)
            )


def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Uses ``lru_cache`` semantics via a module-level singleton so that the
    settings are parsed exactly once per process.
    """
    return _settings


_settings = Settings()
