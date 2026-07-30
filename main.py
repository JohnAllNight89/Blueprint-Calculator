"""
Blueprint Calculator — FastAPI web server.

Routes:
  GET  /              → serve the frontend (templates/index.html)
  GET  /api/health    → engine health check
  POST /api/calculate → run pipeline, return frontend JSON
"""
from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from blueprint_calculator.pipeline import run_pipeline
from api_adapter import adapt

app = FastAPI(title="Blueprint Calculator — Mapping the Human Condition")


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
async def calculate(req: CalculateRequest):
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


