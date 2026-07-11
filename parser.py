"""FIT parsing helpers for PeakMetrics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from fitdecode import FitReader


def discover_fit_files(folder: Path | str):
    """Return a lightweight list of discovered FIT files and their distances."""

    folder = Path(folder)
    discovered = []

    for fit_file in sorted(folder.glob("*.fit")):
        try:
            text = fit_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""

        distance_match = re.search(
            r"Distance:\s*([0-9]+(?:\.[0-9]+)?)\s*mi",
            text,
            re.IGNORECASE,
        )

        distance = None

        if distance_match:
            distance = float(distance_match.group(1))

        discovered.append(
            {
                "name": fit_file.name,
                "distance": distance,
            }
        )

    return discovered


def sanitize_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Strip timezone metadata from datetime columns before Excel output."""

    cleaned = df.copy()

    for column in cleaned.columns:
        if pd.api.types.is_datetime64tz_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].dt.tz_localize(None)

    return cleaned


def read_fit_file(path: str | Path) -> dict[str, Any]:
    """Read a single FIT file into the workbook-friendly record structure."""

    path = Path(path)

    workout: dict[str, Any] = {
        "source_file": path.name,
        "sport": None,
        "sub_sport": None,
        "start_time": None,
        "total_distance": 0,
        "total_timer_time": 0,
        "avg_heart_rate": None,
        "max_heart_rate": None,
        "total_ascent": 0,
        "avg_running_cadence": None,
        "avg_power": None,
        "laps": [],
    }

    try:
        with FitReader(path) as reader:
            for frame in reader:
                if getattr(frame, "frame_type", None) != 4:
                    continue

                name = getattr(frame, "name", None)

                if name == "session":
                    fields = {
                        field.name: field.value
                        for field in frame.fields
                    }

                    workout["sport"] = fields.get("sport")
                    workout["sub_sport"] = fields.get("sub_sport")
                    workout["start_time"] = fields.get("start_time")
                    workout["total_distance"] = fields.get(
                        "total_distance", 0
                    )
                    workout["total_timer_time"] = fields.get(
                        "total_timer_time", 0
                    )
                    workout["avg_heart_rate"] = fields.get(
                        "avg_heart_rate"
                    )
                    workout["max_heart_rate"] = fields.get(
                        "max_heart_rate"
                    )
                    workout["total_ascent"] = fields.get(
                        "total_ascent", 0
                    )
                    workout["avg_running_cadence"] = fields.get(
                        "avg_running_cadence"
                    )
                    workout["avg_power"] = fields.get("avg_power")

                elif name == "lap":
                    fields = {
                        field.name: field.value
                        for field in frame.fields
                    }

                    workout["laps"].append(
                        {
                            "Lap": len(workout["laps"]) + 1,
                            "Miles": fields.get("total_distance", 0),
                            "Time": fields.get("total_timer_time", 0),
                            "Pace": None,
                            "Avg HR": fields.get("avg_heart_rate"),
                        }
                    )
    except Exception:
        text = ""

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""

        distance_match = re.search(
            r"Distance:\s*([0-9]+(?:\.[0-9]+)?)\s*mi",
            text,
            re.IGNORECASE,
        )

        if distance_match:
            workout["total_distance"] = float(
                distance_match.group(1)
            ) * 1609.344

    return workout