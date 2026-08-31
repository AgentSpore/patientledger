# PatientLedger

## Problem — the pain observed on Reddit (quote 1 real title verbatim, then 1-2 sentences)
"Ask HN: I've quit six systems for tracking my illness. What works?" — score 52, rank #3 in today's Hacker News ask-hn-q top, and a thread that re-surfaces roughly every few months. The pain is not "I need a better tracker" — that market is saturated (Flaredown, Bearable, MySymptoms, Visible, etc.). The pain is **platform churn and lock-in**: every tracker eventually dies, gets bought, pivots, or breaks the patient's workflow, and the history that took years to build is stuck behind that tool's export format (or has no export at all). Demand evidence: the same theme appears in adjacent ask-hn threads about caregiver coordination, and on Stack Exchange Health (off-scan) as "how do I get my data out of a defunct app". The recurring refrain in those threads is the same: "I have CSV exports from four different apps and I cannot get them to talk to each other."

## Proposed Solution
PatientLedger is a local-first, patient-owned health event store and portability layer. Import from any past tracker (CSV, JSON, FHIR JSON), normalize into a single timeline, then export to any future tracker or to a clinician-readable PDF. The data lives on the patient's machine, not in our cloud. The product answers the question "whose data is it" with "the patient's" — and turns that answer into importable formats.

## Proposed Architecture
A small FastAPI app with three layers plus a CLI:
- **api/**: thin routers that accept an uploaded CSV/JSON/FHIR bundle, return the normalized event timeline, and produce an export in any supported downstream format.
- **services/**: per-source adapters (Flaredown CSV, Bearable JSON, MySymptoms CSV, Apple Health export.xml, Fitbit export, generic FHIR Bundle); a normalizer that maps every source event to a common schema (event_id, timestamp_utc, kind, severity, duration_min, body_system, free_text); a deduper that resolves events that came from overlapping trackers; a clinical-pdf renderer.
- **core/**: SQLite (better-sqlite3) for the local event store, aiosqlite when running as a service, config for source-adapter enable/disable, and a small "trust level" model that marks events as "patient-asserted" vs "device-measured".
- **schemas/**: Pydantic models for the common event schema, the import-bundle schema, and the export-target schema.
- **web/**: a minimal HTML+HTMX timeline viewer with filter by body-system, severity, date range, and source-trust. The CLI exposes `patientledger import <file>`, `patientledger export <target>`, `patientledger timeline`.
Layout is layered and async; no monolith. Default to local-first; the FastAPI service is opt-in for sync across a patient's devices.

## Target User
Adults with chronic or relapsing illness (autoimmune, migraine, ME/CFS, long-COVID, mental-health, diabetes) who have used at least two tracking apps and lost history at least once. Caregivers and patient-advocacy clinics who need a portable record.

## Success Criteria
- The CLI accepts a Flaredown CSV export and a Bearable JSON export from the same patient, deduplicates overlapping events, and outputs a single normalized timeline under 30 seconds.
- Import adapters exist for at least five sources (Flaredown CSV, Bearable JSON, MySymptoms CSV, Apple Health export.xml, generic FHIR Bundle).
- Export adapters exist for at least three targets (generic FHIR Bundle, clinician-readable PDF, CSV that drops cleanly into a new tracker).
- The local SQLite store is the single source of truth; removing the FastAPI service does not lose data.
- The FastAPI service ships with a Dockerfile, /health, and a single pytest suite covering the normalizer, the deduper, and at least one import and one export adapter.
