"""Permanent SQLite training history for PeakMetrics."""

import hashlib
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("Data") / "peakmetrics.db"


def safe_float(value, default=None):
    """Convert a value to a float without crashing."""

    if value is None:
        return default

    try:
        number = float(value)

        if math.isnan(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def text_or_none(value):
    """Convert a value to text while preserving missing values."""

    if value is None:
        return None

    text = str(value).strip()

    if text.lower() in {
        "",
        "none",
        "nan",
        "<na>",
        "n/a",
    }:
        return None

    return text


def time_to_seconds(value):
    """Convert H:MM:SS or MM:SS into seconds."""

    if value is None:
        return 0

    parts = str(value).split(":")

    try:
        numbers = [
            int(float(part))
            for part in parts
        ]
    except ValueError:
        return 0

    if len(numbers) == 3:
        hours, minutes, seconds = numbers

        return (
            hours * 3600
            + minutes * 60
            + seconds
        )

    if len(numbers) == 2:
        minutes, seconds = numbers

        return minutes * 60 + seconds

    return 0


def pace_to_seconds(value):
    """Convert a pace such as 6:42 into seconds per mile."""

    if value is None:
        return None

    pace_text = (
        str(value)
        .replace("/mi", "")
        .strip()
    )

    parts = pace_text.split(":")

    if len(parts) != 2:
        return None

    try:
        minutes = int(parts[0])
        seconds = int(float(parts[1]))
    except ValueError:
        return None

    return minutes * 60 + seconds


def datetime_text(value):
    """Convert a datetime-like value into stable text."""

    if value is None:
        return ""

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def build_activity_key(run):
    """
    Create a stable identifier for an activity.

    The FIT filename and activity start time together
    uniquely identify the activity.
    """

    source_file = str(
        run.get("Source File") or ""
    )

    start_time = datetime_text(
        run.get("Start Time")
    )

    key_text = (
        f"{source_file}|{start_time}"
    )

    return hashlib.sha256(
        key_text.encode("utf-8")
    ).hexdigest()


def initialize_database(connection):
    """Create the PeakMetrics database tables."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            activity_key TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            start_time TEXT NOT NULL,
            activity_date TEXT NOT NULL,
            time_of_day TEXT,
            run_type TEXT NOT NULL,
            sport TEXT,
            sub_sport TEXT,
            miles REAL NOT NULL DEFAULT 0,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            pace_seconds_per_mile INTEGER,
            avg_hr REAL,
            max_hr REAL,
            elevation_ft REAL,
            cadence_spm REAL,
            power_w REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS laps (
            activity_key TEXT NOT NULL,
            lap_number INTEGER NOT NULL,
            miles REAL NOT NULL DEFAULT 0,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            pace_seconds_per_mile INTEGER,
            avg_hr REAL,

            PRIMARY KEY (
                activity_key,
                lap_number
            ),

            FOREIGN KEY (
                activity_key
            )
            REFERENCES activities (
                activity_key
            )
            ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_activities_date
        ON activities (
            activity_date
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_activities_type
        ON activities (
            run_type
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_activities_start_time
        ON activities (
            start_time
        )
        """
    )


def save_training_history(
    df,
    database_path=DEFAULT_DATABASE_PATH,
):
    """
    Save activities and laps into the history database.

    Existing activities are updated instead of duplicated.
    """

    database_path = Path(
        database_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        database_path
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    initialize_database(
        connection
    )

    added = 0
    updated = 0
    laps_saved = 0

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    try:
        for run in df.to_dict("records"):
            activity_key = build_activity_key(
                run
            )

            already_exists = (
                connection.execute(
                    """
                    SELECT 1
                    FROM activities
                    WHERE activity_key = ?
                    """,
                    (activity_key,),
                ).fetchone()
                is not None
            )

            if already_exists:
                updated += 1
            else:
                added += 1

            source_file = str(
                run.get("Source File")
                or "unknown.fit"
            )

            start_time = datetime_text(
                run.get("Start Time")
            )

            activity_date = str(
                run.get("Date") or ""
            )

            run_type = str(
                run.get("Run Type")
                or "Other"
            )

            connection.execute(
                """
                INSERT INTO activities (
                    activity_key,
                    source_file,
                    start_time,
                    activity_date,
                    time_of_day,
                    run_type,
                    sport,
                    sub_sport,
                    miles,
                    duration_seconds,
                    pace_seconds_per_mile,
                    avg_hr,
                    max_hr,
                    elevation_ft,
                    cadence_spm,
                    power_w,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(activity_key)
                DO UPDATE SET
                    source_file =
                        excluded.source_file,
                    start_time =
                        excluded.start_time,
                    activity_date =
                        excluded.activity_date,
                    time_of_day =
                        excluded.time_of_day,
                    run_type =
                        excluded.run_type,
                    sport =
                        excluded.sport,
                    sub_sport =
                        excluded.sub_sport,
                    miles =
                        excluded.miles,
                    duration_seconds =
                        excluded.duration_seconds,
                    pace_seconds_per_mile =
                        excluded.pace_seconds_per_mile,
                    avg_hr =
                        excluded.avg_hr,
                    max_hr =
                        excluded.max_hr,
                    elevation_ft =
                        excluded.elevation_ft,
                    cadence_spm =
                        excluded.cadence_spm,
                    power_w =
                        excluded.power_w,
                    updated_at =
                        excluded.updated_at
                """,
                (
                    activity_key,
                    source_file,
                    start_time,
                    activity_date,
                    text_or_none(
                        run.get("Time of Day")
                    ),
                    run_type,
                    text_or_none(
                        run.get("Sport")
                    ),
                    text_or_none(
                        run.get("Sub Sport")
                    ),
                    safe_float(
                        run.get("Miles"),
                        0,
                    ),
                    time_to_seconds(
                        run.get("Time")
                    ),
                    pace_to_seconds(
                        run.get("Pace (/mi)")
                    ),
                    safe_float(
                        run.get("Avg HR")
                    ),
                    safe_float(
                        run.get("Max HR")
                    ),
                    safe_float(
                        run.get(
                            "Elevation (ft)"
                        )
                    ),
                    safe_float(
                        run.get(
                            "Cadence (spm)"
                        )
                    ),
                    safe_float(
                        run.get("Power (W)")
                    ),
                    timestamp,
                    timestamp,
                ),
            )

            # Replace the old lap records so that
            # rerunning an activity cannot duplicate laps.
            connection.execute(
                """
                DELETE FROM laps
                WHERE activity_key = ?
                """,
                (activity_key,),
            )

            for lap_index, lap in enumerate(
                run.get("Laps") or [],
                start=1,
            ):
                lap_number = (
                    lap.get("Lap")
                    or lap_index
                )

                connection.execute(
                    """
                    INSERT INTO laps (
                        activity_key,
                        lap_number,
                        miles,
                        duration_seconds,
                        pace_seconds_per_mile,
                        avg_hr
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity_key,
                        int(lap_number),
                        safe_float(
                            lap.get("Miles"),
                            0,
                        ),
                        time_to_seconds(
                            lap.get("Time")
                        ),
                        pace_to_seconds(
                            lap.get("Pace")
                        ),
                        safe_float(
                            lap.get("Avg HR")
                        ),
                    ),
                )

                laps_saved += 1

        connection.commit()

        total_activities = connection.execute(
            """
            SELECT COUNT(*)
            FROM activities
            """
        ).fetchone()[0]

        total_laps = connection.execute(
            """
            SELECT COUNT(*)
            FROM laps
            """
        ).fetchone()[0]

    finally:
        connection.close()

    return {
        "database_path": database_path,
        "added": added,
        "updated": updated,
        "laps_saved": laps_saved,
        "total_activities": total_activities,
        "total_laps": total_laps,
    }