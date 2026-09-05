"""aiosqlite plumbing for PatientLedger.

Local-first means the SQLite file IS the source of truth. Schema:

  events        — one row per health event after import + dedup
  sources       — one row per import-bundle (so a re-import is idempotent)
  raw_events    — events BEFORE dedup, kept so the user can re-dedup
                  with a different window without re-importing
  exports       — log of every export the user has produced, so the
                  portability story has an audit trail

A UUID is the canonical id (no integer auto-increment) so an export
from a downstream tracker can carry the same id forward.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id              TEXT PRIMARY KEY,
    source_format   TEXT NOT NULL,    -- flaredown_csv | bearable_json | ...
    original_name   TEXT NOT NULL,
    received_at     TEXT NOT NULL,
    event_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS raw_events (
    id              TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL,
    timestamp_utc   TEXT NOT NULL,
    kind            TEXT NOT NULL,
    severity        INTEGER,           -- 0-10, nullable (some sources don't)
    duration_min    INTEGER,
    body_system     TEXT,
    free_text       TEXT,
    trust           TEXT NOT NULL,
    raw             TEXT NOT NULL,     -- JSON blob of the source row
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_raw_events_source ON raw_events(source_id);
CREATE INDEX IF NOT EXISTS ix_raw_events_timestamp ON raw_events(timestamp_utc);

CREATE TABLE IF NOT EXISTS events (
    id              TEXT PRIMARY KEY,
    timestamp_utc   TEXT NOT NULL,
    kind            TEXT NOT NULL,
    severity        INTEGER,
    duration_min    INTEGER,
    body_system     TEXT,
    free_text       TEXT,
    trust           TEXT NOT NULL,
    sources         TEXT NOT NULL,     -- comma-separated source_ids
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_events_timestamp ON events(timestamp_utc);
CREATE INDEX IF NOT EXISTS ix_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS ix_events_body ON events(body_system);

CREATE TABLE IF NOT EXISTS exports (
    id              TEXT PRIMARY KEY,
    target_format   TEXT NOT NULL,    -- fhir_bundle | clinical_pdf | csv
    event_count     INTEGER NOT NULL,
    produced_at     TEXT NOT NULL,
    detail          TEXT
);
"""


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an aiosqlite connection. Caller owns the transaction."""
    db = await aiosqlite.connect(settings().database_url)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    async with get_db() as db:
        await db.executescript(SCHEMA)
        await db.commit()
