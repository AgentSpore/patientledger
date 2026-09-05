"""G3 stub of the import service.

The full implementation lands in G4. This stub returns no-op counters
so the route compiles and the test surface can be brought up; the G4
push overwrites this file with real adapters for Flaredown CSV,
Bearable JSON, MySymptoms CSV, Apple Health XML, FHIR Bundle, and
Fitbit CSV, plus a dedup pass that merges events whose kind +
body_system + severity match within `dedup_window_minutes`.
"""
from __future__ import annotations

from typing import Any, Dict


async def import_bundle(
    db,
    source_id: str,
    source_format: str,
    original_name: str,
    payload: str,
    received_at: str,
) -> Dict[str, int]:
    await db.execute(
        "INSERT INTO sources (id, source_format, original_name, "
        "received_at, event_count) VALUES (?, ?, ?, ?, 0)",
        (source_id, source_format, original_name, received_at),
    )
    return {
        "raw_count": 0,
        "accepted_count": 0,
        "merged_count": 0,
        "skipped_count": 0,
    }
