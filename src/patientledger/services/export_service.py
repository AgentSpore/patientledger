"""G3 stub of the export service.

The full implementation lands in G4. This stub records a zero-count
export so the route compiles and the audit-trail table is exercised
during G3; the G4 push overwrites this file with the real adapters
for FHIR Bundle, clinical PDF, and generic CSV export.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


async def export_timeline(
    db,
    export_id: str,
    target: str,
    body_system: Optional[str],
    kind: Optional[str],
    start,
    end,
    patient_name: Optional[str],
    produced_at: str,
) -> Dict[str, Any]:
    await db.execute(
        "INSERT INTO exports (id, target_format, event_count, produced_at, "
        "detail) VALUES (?, ?, 0, ?, ?)",
        (export_id, target, produced_at, "stub"),
    )
    return {"event_count": 0, "bundle": ""}
