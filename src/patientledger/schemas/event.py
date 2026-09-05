"""Pydantic v2 models for PatientLedger's health event timeline.

Three shapes:

  Event              — one row in the normalized timeline
  ImportRequest      — a raw import bundle with a format hint
  ExportRequest      — a query for the timeline, plus a target format
  TimelineResponse   — what /timeline returns: events + source provenance

The same Event shape is used as input, as a row in /timeline, and as a
member of the FHIR-export payload. The trust field is on every Event
because the README's portability story depends on the patient being
able to show a clinician which events were manually logged and which
were recorded by a device.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


SourceFormat = Literal[
    "flaredown_csv",
    "bearable_json",
    "mysymptoms_csv",
    "apple_health_xml",
    "fhir_bundle",
    "fitbit_csv",
]

ExportFormat = Literal["fhir_bundle", "clinical_pdf", "csv"]

Trust = Literal["patient-asserted", "device-measured"]


class Event(BaseModel):
    id: str
    timestamp_utc: datetime
    kind: str = Field(..., min_length=1, max_length=100,
                      description="symptom, mood, medication, sleep, activity, ...")
    severity: Optional[int] = Field(default=None, ge=0, le=10)
    duration_min: Optional[int] = Field(default=None, ge=0)
    body_system: Optional[str] = Field(default=None, max_length=100)
    free_text: Optional[str] = None
    trust: Trust
    sources: List[str] = Field(default_factory=list,
                               description="source_ids that contributed to this event")


class ImportRequest(BaseModel):
    source_format: SourceFormat
    original_name: str = Field(..., min_length=1, max_length=400)
    payload: str = Field(..., description="raw import contents (CSV/JSON/XML/FHIR text)")


class ImportResponse(BaseModel):
    source_id: str
    source_format: SourceFormat
    raw_event_count: int
    accepted_event_count: int
    merged_count: int = Field(..., description="events merged into an existing one")
    skipped_count: int


class TimelineFilter(BaseModel):
    body_system: Optional[str] = None
    kind: Optional[str] = None
    trust: Optional[Trust] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=500, ge=1, le=5000)


class TimelineResponse(BaseModel):
    count: int
    events: List[Event]


class ExportRequest(BaseModel):
    target: ExportFormat
    body_system: Optional[str] = None
    kind: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    patient_name: Optional[str] = Field(default=None,
        description="used in the clinical PDF header; not stored")


class ExportRead(BaseModel):
    id: str
    target: ExportFormat
    event_count: int
    produced_at: datetime
