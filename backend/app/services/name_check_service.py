"""Entity name availability checking service.

MVP: Returns random availability for development.
Phase A: Integrates with DE/WY Playwright automation for real checks.
Phase B: Integrates with registered agent APIs for instant checks.
"""

from __future__ import annotations

import random
from typing import Any


async def check_name_availability(
    jurisdiction: str,
    entity_name: str,
    entity_type: str = "llc",
) -> dict[str, Any]:
    """Check if an entity name is available in the given jurisdiction.
    
    Returns:
        dict with keys:
            - available: bool
            - jurisdiction: str
            - entity_name: str
            - message: str
            - method: str (how the check was performed)
    """
    # MVP: Random result for development
    # TODO: Wire to filing-automation/scripts/delaware/name_check.py
    available = random.random() > 0.3  # 70% chance available
    
    if available:
        message = f"'{entity_name}' appears to be available in {jurisdiction}"
    else:
        message = f"'{entity_name}' is not available in {jurisdiction}. A similar entity may already exist."
    
    return {
        "available": available,
        "jurisdiction": jurisdiction.upper(),
        "entity_name": entity_name,
        "entity_type": entity_type,
        "message": message,
        "method": "dev_stub",
        "suggestions": [] if available else [
            f"{entity_name} Holdings",
            f"{entity_name} Group",
            f"{entity_name} Capital",
        ],
    }
