"""Deterministic document template engine.

Wraps docxtpl to render legal documents from Jinja2-templated DOCX files.
Uses StrictUndefined to prevent silent variable omission.

IMPORTANT: After editing templates in Word, always validate with
get_undeclared_template_variables() — Word can silently split
{{variable}} across XML runs, making them invisible to the variable checker.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate
from jinja2 import StrictUndefined

logger = logging.getLogger("sfp.templates")

# Base directory for templates (relative to backend/)
TEMPLATE_BASE = Path(__file__).resolve().parents[3] / "templates"


def get_template_path(jurisdiction: str, template_name: str) -> Path:
    """Resolve a template file path.

    Args:
        jurisdiction: e.g., "de_llc", "wy_dao_llc", "common"
        template_name: e.g., "operating_agreement.docx"

    Returns:
        Absolute path to the template file.

    Raises:
        FileNotFoundError: If the template doesn't exist.
    """
    path = TEMPLATE_BASE / jurisdiction / template_name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path


def list_templates(jurisdiction: str | None = None) -> list[dict[str, str]]:
    """List available templates, optionally filtered by jurisdiction."""
    results = []
    search_dirs = (
        [TEMPLATE_BASE / jurisdiction] if jurisdiction else TEMPLATE_BASE.iterdir()
    )

    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.docx")):
            results.append({
                "jurisdiction": d.name,
                "template": f.name,
                "path": str(f),
            })
    return results


def get_template_variables(jurisdiction: str, template_name: str) -> set[str]:
    """Get the undeclared variables in a template.

    Useful for validation before rendering. Note: variables split across
    XML runs by Word may not appear here — always validate rendered output.
    """
    path = get_template_path(jurisdiction, template_name)
    doc = DocxTemplate(str(path))
    return doc.get_undeclared_template_variables()


def render_document(
    jurisdiction: str,
    template_name: str,
    context: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    """Render a DOCX template with the given context.

    Args:
        jurisdiction: Template jurisdiction directory (e.g., "de_llc")
        template_name: Template filename (e.g., "operating_agreement.docx")
        context: Template variables to merge
        output_path: Where to save the rendered document

    Returns:
        dict with:
            - output_path: str — path to rendered file
            - file_hash: str — SHA-256 hex digest
            - template_name: str
            - template_version: str — hash of template file
            - variables_used: list[str]
    """
    template_path = get_template_path(jurisdiction, template_name)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Hash the template for version tracking
    template_hash = hashlib.sha256(template_path.read_bytes()).hexdigest()[:16]

    # Render with StrictUndefined
    doc = DocxTemplate(str(template_path))

    # Get declared variables for logging
    declared_vars = doc.get_undeclared_template_variables()

    # Check for missing variables
    missing = declared_vars - set(context.keys())
    if missing:
        logger.warning(
            "Template %s/%s has undeclared variables not in context: %s",
            jurisdiction, template_name, missing,
        )

    doc.render(context, jinja_env=doc.get_jinja_env(undefined=StrictUndefined))
    doc.save(str(output_path))

    # Hash the output
    file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()

    logger.info(
        "Rendered %s/%s -> %s (hash=%s)",
        jurisdiction, template_name, output_path, file_hash[:16],
    )

    return {
        "output_path": str(output_path),
        "file_hash": file_hash,
        "template_name": template_name,
        "template_version": template_hash,
        "variables_used": sorted(declared_vars),
    }


def validate_template(jurisdiction: str, template_name: str) -> dict[str, Any]:
    """Validate a template file without rendering.

    Returns info about the template including variables and any issues.
    """
    path = get_template_path(jurisdiction, template_name)

    try:
        doc = DocxTemplate(str(path))
        variables = doc.get_undeclared_template_variables()
        template_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

        return {
            "valid": True,
            "path": str(path),
            "template_hash": template_hash,
            "variables": sorted(variables),
            "variable_count": len(variables),
            "issues": [],
        }
    except Exception as e:
        return {
            "valid": False,
            "path": str(path),
            "template_hash": None,
            "variables": [],
            "variable_count": 0,
            "issues": [str(e)],
        }
