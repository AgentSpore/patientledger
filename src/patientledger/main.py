"""PatientLedger — FastAPI entrypoint (G3: routers wired in)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.events import router as events_router
from .core.db import init_db

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

app.include_router(events_router, prefix="/api")


@app.on_event("startup")
async def _startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
