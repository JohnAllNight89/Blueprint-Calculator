"""Blueprint Calculator — FastAPI router and API controllers (Phase 2)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from engines import (
    gene_keys,
    geolocation,
    human_design,
    numerology,
    synthesis,
    vedic_astrology,
    western_astrology,
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_PAGE = BASE_DIR / "templates" / "index.html"


import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "change-this-password-locally")

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: The Unified Spirit Secure Node",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app = FastAPI(title="Blueprint Calculator", version="0.2.0", dependencies=[Depends(authenticate_user)])


class BirthProfile(BaseModel):
    name: str = Field(..., min_length=1, description="Full birth name")
    birth_date: date
    birth_time: str = Field("", description="HH:MM local birth time")
    birth_place: str = Field("", description="Birth city or 'lat, lon'")


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
    return {
        "status": "ok",
        "phase": 3,
        "engines": [
            "numerology", "western_astrology", "vedic_astrology",
            "human_design", "gene_keys", "synthesis",
        ],
    }


@app.get("/api/verify")
def verify() -> dict:
    """Expose the hardcoded reference-profile verification."""
    return numerology.verify_reference_profile()


def _calculate_astrology(profile: BirthProfile) -> dict | None:
    """Run both astrology engines when birth time and place are supplied."""
    has_time = bool(profile.birth_time.strip())
    has_place = bool(profile.birth_place.strip())
    if not (has_time and has_place):
        missing = []
        if not has_time:
            missing.append("birth time")
        if not has_place:
            missing.append("birth place")
        return {"available": False, "reason": f"Add {' and '.join(missing)} to unlock the astrology engines."}

    try:
        location = geolocation.resolve_location(profile.birth_place)
    except LookupError as error:
        raise HTTPException(status_code=422, detail=str(error))

    try:
        moment = geolocation.local_to_utc(
            profile.birth_date, profile.birth_time, location["timezone"]
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    latitude, longitude = location["latitude"], location["longitude"]
    western = western_astrology.calculate_chart(moment["utc"], latitude, longitude)
    bodygraph = human_design.calculate_chart(moment["utc"])
    genekeys = gene_keys.calculate_profile(bodygraph)
    return {
        "available": True,
        "location": {
            "query": profile.birth_place.strip(),
            "resolved": location["display"],
            "latitude": latitude,
            "longitude": longitude,
            "timezone": location["timezone"],
        },
        "time": {
            "local": moment["local"].strftime("%Y-%m-%d %H:%M"),
            "utc": moment["utc"].strftime("%Y-%m-%d %H:%M"),
            "utc_offset": moment["utc_offset_label"],
        },
        "western": western,
        "vedic": vedic_astrology.calculate_chart(moment["utc"], latitude, longitude),
        "human_design": bodygraph,
        "gene_keys": genekeys,
    }


@app.post("/api/calculate")
def calculate(profile: BirthProfile) -> dict:
    if not any(char.isalpha() for char in profile.name):
        raise HTTPException(status_code=422, detail="Name must contain letters.")
    numerology_chart = numerology.calculate_chart(profile.name, profile.birth_date)
    astrology = _calculate_astrology(profile)

    blueprint = None
    if astrology and astrology["available"]:
        blueprint = synthesis.compose(
            numerology_chart,
            astrology["western"],
            astrology["human_design"],
            astrology["gene_keys"],
        )

    return {
        "profile": {
            "name": profile.name.strip(),
            "birth_date": profile.birth_date.isoformat(),
            "birth_time": profile.birth_time.strip(),
            "birth_place": profile.birth_place.strip(),
        },
        "numerology": numerology_chart,
        "astrology": astrology,
        "synthesis": blueprint,
    }
