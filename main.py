"""Blueprint Calculator — FastAPI router and API controllers (Phase 1)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from engines import numerology

BASE_DIR = Path(__file__).resolve().parent
INDEX_PAGE = BASE_DIR / "templates" / "index.html"

app = FastAPI(title="Blueprint Calculator", version="0.1.0")


class BirthProfile(BaseModel):
    name: str = Field(..., min_length=1, description="Full birth name")
    birth_date: date
    birth_time: str = Field("", description="HH:MM, used by later phases")
    birth_place: str = Field("", description="City/region, used by later phases")


@app.on_event("startup")
def run_self_verification() -> None:
    """Auto-verify the numerology engine against the reference profile."""
    report = numerology.verify_reference_profile()
    status = "PASSED" if report["all_passed"] else "FAILED"
    print(f"[numerology self-check] {status} — {report['profile']}")
    for key, check in report["checks"].items():
        mark = "✓" if check["passed"] else "✗"
        print(f"  {mark} {key}: expected {check['expected']}, got {check['actual']}")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(INDEX_PAGE)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "phase": 1, "engines": ["numerology"]}


@app.get("/api/verify")
def verify() -> dict:
    """Expose the hardcoded reference-profile verification."""
    return numerology.verify_reference_profile()


@app.post("/api/calculate")
def calculate(profile: BirthProfile) -> dict:
    if not any(char.isalpha() for char in profile.name):
        raise HTTPException(status_code=422, detail="Name must contain letters.")
    return {
        "profile": {
            "name": profile.name.strip(),
            "birth_date": profile.birth_date.isoformat(),
            "birth_time": profile.birth_time.strip(),
            "birth_place": profile.birth_place.strip(),
        },
        "numerology": numerology.calculate_chart(profile.name, profile.birth_date),
    }
