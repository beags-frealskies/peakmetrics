import re
from pathlib import Path

import fitdecode
import pandas as pd


def read_fit_file(filename):
    workout = {}

    with fitdecode.FitReader(filename) as fit:
        for frame in fit:
            if (
                isinstance(frame, fitdecode.FitDataMessage)
                and frame.name == "session"
            ):

                for field in frame.fields:
                    workout[field.name] = field.value

                break

    return workout


def discover_fit_files(folder):
    folder = Path(folder)
    runs = []

    for fit_file in sorted(folder.glob("*.fit")):
        try:
            workout = read_fit_file(fit_file)
            distance = workout.get("total_distance")
        except Exception:
            distance = None

        if distance is None:
            text = fit_file.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"Distance:\s*([0-9.]+)\s*mi", text)
            if match:
                distance = float(match.group(1))

        entry = {"name": fit_file.name}
        if distance is not None:
            entry["distance"] = distance
        runs.append(entry)

    return runs


def sanitize_for_excel(df):
    cleaned = df.copy()

    for column in cleaned.columns:
        series = cleaned[column]

        if pd.api.types.is_datetime64tz_dtype(series):
            cleaned[column] = series.dt.tz_convert(None)
            continue

        if pd.api.types.is_object_dtype(series):
            converted_values = []
            changed = False

            for value in series:
                if hasattr(value, "tzinfo") and getattr(value, "tzinfo", None) is not None:
                    converted_values.append(value.tz_convert(None))
                    changed = True
                else:
                    converted_values.append(value)

            if changed:
                cleaned[column] = converted_values

    return cleaned
