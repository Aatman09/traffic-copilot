"""
models/incident.py — Data models for incidents, routes, and incident history.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_FILE = os.path.join(DATA_DIR, "incident_log.json")


@dataclass
class Route:
    """A single alternate route computed by the routing engine."""
    coords: List[Tuple[float, float]]
    nodes: List[int]
    distance_m: int
    street_summary: str
    rank: int
    eta_minutes: Optional[float] = None


@dataclass
class Incident:
    """A traffic incident with all associated metadata."""
    crash_lat: float
    crash_lng: float
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    blocked_street: str = "Unknown Road"
    vehicle_type: str = "Car"
    lanes_affected: str = "1"
    traffic_density: str = "Moderate"
    weather: str = "Clear"
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    severity_score: Optional[int] = None
    severity_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Incident":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class IncidentLog:
    """Persistent log of past incidents saved to JSON."""

    def __init__(self, filepath: str = LOG_FILE):
        self.filepath = filepath

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def load(self) -> List[dict]:
        """Load all past incidents from disk."""
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save(self, incident: Incident, analysis: Optional[dict] = None,
             routes: Optional[List[dict]] = None):
        """Append a new incident record to the log."""
        self._ensure_dir()
        records = self.load()
        record = {
            "incident": incident.to_dict(),
            "analysis_summary": (analysis or {}).get("incident_summary", ""),
            "route_count": len(routes) if routes else 0,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        records.append(record)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def clear(self):
        """Clear all incident history."""
        self._ensure_dir()
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([], f)

    def count(self) -> int:
        return len(self.load())
