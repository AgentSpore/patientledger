"""PatientLedger — thin FastAPI entrypoint (G1).

Routers land in G3; the entrypoint is intentionally minimal so a smoke
test (`GET /health`) confirms the package is importable and the app
boots before any domain logic is wired in.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PatientLedger",
    version="0.1.0",
    description=(
        "Local-first, patient-owned health event store and portability "
        "layer. Import from any past tracker, normalize into a single "
        "timeline, export to any future tracker or to a clinician-readable "
        "PDF. The data lives on the patient's machine, not in our cloud."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
