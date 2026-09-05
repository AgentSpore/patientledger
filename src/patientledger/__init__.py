"""PatientLedger — local-first, patient-owned health event store and
portability layer.

This package ships a small FastAPI app that imports from any past
tracker (CSV, JSON, FHIR), normalizes into a single timeline, then
exports to any future tracker or to a clinician-readable PDF. The data
lives on the patient's machine, not in our cloud.
"""
__version__ = "0.1.0"
