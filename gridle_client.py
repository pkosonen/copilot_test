from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


BASE_URL = "https://residential.gridle.com/api/public/measurements"


class GridleApiError(RuntimeError):
    pass


@dataclass(slots=True)
class MeasurementQuery:
    start_time: datetime | None = None
    end_time: datetime | None = None

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.start_time is not None:
            params["start_time"] = self.start_time.isoformat()
        if self.end_time is not None:
            params["end_time"] = self.end_time.isoformat()
        return params


class GridleClient:
    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "accept": "application/json",
                "x-api-key": api_key,
            }
        )
        self._timeout = timeout

    def fetch_measurements(self, query: MeasurementQuery | None = None) -> list[dict[str, Any]]:
        response = self._session.get(
            BASE_URL,
            params=(query or MeasurementQuery()).to_params(),
            timeout=self._timeout,
        )

        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise GridleApiError(f"{response.status_code}: {message}")

        payload = response.json()
        if not isinstance(payload, list):
            raise GridleApiError("Unexpected response payload; expected a list of measurements.")

        return payload

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("message") or payload
            return str(detail)

        return str(payload)
