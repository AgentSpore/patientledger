"""Settings for PatientLedger.

Local-first means a single settings object: where the SQLite file lives,
which import adapters are enabled, and which export targets exist. The
defaults match the README "Success Criteria" — five import adapters,
three export targets — so the service ships usable.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Persistence — local SQLite file is the source of truth (README
    # success criterion: removing the FastAPI service must not lose data).
    database_url: str = "patientledger.db"

    # HTTP
    cors_origins: str = "*"
    log_level: str = "INFO"

    # Import adapters (CSV / JSON / FHIR / Apple Health XML / Fitbit).
    # Set via env to disable a flaky upstream format. The README lists
    # five canonical sources; the defaults are them.
    enable_flaredown_csv: bool = True
    enable_bearable_json: bool = True
    enable_mysymptoms_csv: bool = True
    enable_apple_health_xml: bool = True
    enable_fhir_bundle: bool = True
    enable_fitbit_csv: bool = True

    # Export targets.
    enable_export_fhir_bundle: bool = True
    enable_export_clinical_pdf: bool = True
    enable_export_generic_csv: bool = True

    # Dedup window — two events are "the same" if their kind, body
    # system, and severity match within this many minutes. Generous
    # enough to merge a manually-logged entry with a watch-recorded
    # one, tight enough to keep distinct events distinct.
    dedup_window_minutes: int = 30

    # Trust levels. patient-asserted = typed by the patient. device-
    # measured = arrived from Apple Health / Fitbit / a wearable.
    default_trust_patient: str = "patient-asserted"
    default_trust_device: str = "device-measured"


@lru_cache
def settings() -> Settings:
    return Settings()
