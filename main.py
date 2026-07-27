"""
Blueprint Calculator — FastAPI web server.

Routes:
  GET  /              → serve the frontend (templates/index.html)
  GET  /api/health    → engine health check
  POST /api/calculate → run pipeline, return frontend JSON
  GET  /api/audit     → re-run pipeline, return full ledger as downloadable JSON

All routes except GET / require HTTP Basic Auth (env: ADMIN_USER / ADMIN_PASS,
defaults: admin / blueprint). The browser caches credentials on the first
challenge so the frontend's subsequent XHR calls work seamlessly.
"""
from __future__ import annotations

import os
import secrets
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from blueprint_calculator.pipeline import run_pipeline
from api_adapter import adapt

_ADMIN_USER = os.environ.get("ADMIN_USER", "admin").encode()
_ADMIN_PASS = os.environ.get("ADMIN_PASS", "blueprint").encode()

app = FastAPI(title="Blueprint Calculator — Mapping the Human Condition")
_security = HTTPBasic()


def _require_auth(creds: HTTPBasicCredentials = Depends(_security)) -> str:
    ok = secrets.compare_digest(creds.username.encode(), _ADMIN_USER) and \
         secrets.compare_digest(creds.password.encode(), _ADMIN_PASS)
    if not ok:
        raise HTTPException(
            status_code=401, detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Blueprint Calculator"'},
        )
    return creds.username


class CalculateRequest(BaseModel):
    name: str
    birth_date: str
    birth_time: str = ""
    birth_place: str = ""


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(
        "templates/index.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "engine": "Mapping the Human Condition — Blueprint Pipeline v1",
    }


@app.post("/api/calculate")
async def calculate(req: CalculateRequest, _: str = Depends(_require_auth)):
    try:
        report = run_pipeline(
            name=req.name,
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            birth_place=req.birth_place,
            today=date.today(),
        )
        return adapt(report)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


