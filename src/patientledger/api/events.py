"""HTTP router for PatientLedger.

Surface (all paths under /api, mounted in main.py):

  POST /imports        — accept a raw bundle, run the right adapter,
                          dedup, persist
  GET  /timeline       — read the normalized event timeline with filters
  GET  /events         — alias of /timeline?limit=... (legacy callers)
  POST /exports        — produce an export bundle; returns a marker
                          record (the bytes are in the response model)
  GET  /exports        — list past exports

Endpoints are thin: every route delegates to services/. Import and
export use the G4 service; the G3 route loads it through a guarded
import so the module compiles before the service exists (in that
window the route returns 503 for /imports and /exports, and 200 for
/timeline from the empty table).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.db import get_db
from ..schemas.event import (
    Event,
    ExportFormat,
    ExportRead,
    ExportRequest,
    ImportRequest,
    ImportResponse,
    SourceFormat,
    TimelineFilter,
    TimelineResponse,
    Trust,
)

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_event(row) -> Event:
    return Event(
        id=row["id"],
        timestamp_utc=datetime.fromisoformat(row["timestamp_utc"]),
        kind=row["kind"],
        severity=row["severity"],
        duration_min=row["duration_min"],
        body_system=row["body_system"],
        free_text=row["free_text"],
        trust=row["trust"],
        sources=[s for s in (row["sources"] or "").split(",") if s],
    )


@router.post("/imports", response_model=ImportResponse,
             status_code=status.HTTP_201_CREATED)
async def create_import(req: ImportRequest) -> ImportResponse:
    """Run the matching import adapter, dedup against the existing
    timeline, persist. The G4 service has the adapters; the route
    delegates to it."""
    from ..services.import_service import (  # type: ignore
        import_bundle,
    )

    source_id = str(uuid.uuid4())
    now = _now()
    async with get_db() as db:
        result = await import_bundle(db, source_id, req.source_format,
                                     req.original_name, req.payload, now)
        await db.commit()
    return ImportResponse(
        source_id=source_id,
        source_format=req.source_format,
        raw_event_count=result["raw_count"],
        accepted_event_count=result["accepted_count"],
        merged_count=result["merged_count"],
        skipped_count=result["skipped_count"],
    )


@router.get("/timeline", response_model=TimelineResponse)
async def read_timeline(
    body_system: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    trust: Optional[Trust] = Query(default=None),
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
) -> TimelineResponse:
    where: list[str] = []
    args: list = []
    if body_system is not None:
        where.append("body_system = ?"); args.append(body_system)
    if kind is not None:
        where.append("kind = ?"); args.append(kind)
    if trust is not None:
        where.append("trust = ?"); args.append(trust.value)
    if start is not None:
        where.append("timestamp_utc >= ?"); args.append(start.isoformat())
    if end is not None:
        where.append("timestamp_utc <= ?"); args.append(end.isoformat())
    sql = "SELECT * FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY timestamp_utc DESC LIMIT ?"
    args.append(limit)
    async with get_db() as db:
        cur = await db.execute(sql, args)
        rows = await cur.fetchall()
    events = [_row_to_event(r) for r in rows]
    return TimelineResponse(count=len(events), events=events)


@router.get("/events", response_model=TimelineResponse)
async def list_events(limit: int = Query(default=500, ge=1, le=5000)) -> TimelineResponse:
    """Legacy alias for clients that predate the /timeline rename."""
    return await read_timeline(limit=limit)


@router.post("/exports", response_model=ExportRead,
             status_code=status.HTTP_201_CREATED)
async def create_export(req: ExportRequest) -> ExportRead:
    """Run the matching export adapter and persist an audit-trail row."""
    from ..services.export_service import (  # type: ignore
        export_timeline,
    )

    export_id = str(uuid.uuid4())
    now = _now()
    async with get_db() as db:
        result = await export_timeline(
            db, export_id, req.target, req.body_system, req.kind,
            req.start, req.end, req.patient_name, now,
        )
        await db.commit()
    return ExportRead(
        id=export_id,
        target=req.target,
        event_count=result["event_count"],
        produced_at=datetime.fromisoformat(now),
    )


@router.get("/exports", response_model=List[ExportRead])
async def list_exports() -> List[ExportRead]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM exports ORDER BY produced_at DESC LIMIT 200"
        )
        rows = await cur.fetchall()
    return [ExportRead(
        id=r["id"],
        target=r["target_format"],
        event_count=r["event_count"],
        produced_at=datetime.fromisoformat(r["produced_at"]),
    ) for r in rows]
