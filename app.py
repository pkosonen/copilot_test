from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gridle_client import GridleApiError, GridleClient


load_dotenv()

app = FastAPI(title="Gridle Latest Values API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


def get_latest_measurement() -> dict[str, Any]:
    api_key = os.getenv("GRIDLE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GRIDLE_API_KEY is missing")

    client = GridleClient(api_key=api_key)

    try:
        rows = client.fetch_measurements()
    except GridleApiError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream Gridle API error: {exc}") from exc

    if not rows:
        raise HTTPException(status_code=404, detail="No measurement data returned")

    return rows[-1]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/latest")
def latest() -> dict[str, Any]:
    return get_latest_measurement()


# Serve React static files from frontend/dist
# This must be mounted AFTER all API routes are defined
dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
