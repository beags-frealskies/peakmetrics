"""PeakMetrics report generator."""

from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from analytics import (
    WeeklySummary,
    build_daily_mileage,
    build_week_summary,
)
from excel_report import create_excel_report
from metrics import (
    cadence_to_spm,
    meters_to_feet,
    meters_to_miles,
    pace_from_time,
    seconds_to_hms,
)
from parser import read_fit_file
from run_classifier import (
    classify_runs,
    is_running_activity,
)


LOCAL_TIMEZONE = ZoneInfo(
    "America/Denver"
)


def convert_to_local_time(start_time):
    """Convert a FIT timestamp into Utah local time."""

    if start_time.tzinfo is None:
        start_time = start_time.replace(
            tzinfo=timezone.utc
        )

    return start_time.astimezone(
        LOCAL_TIMEZONE
    )


def optional_cadence(value):
    """Convert cadence safely when it exists."""

    if value is None:
        return None

    return cadence_to_spm(value)


runs_folder = Path("Weekly Runs")
fit_files = sorted(
    runs_folder.glob("*.fit")
)

if not fit_files:
    raise SystemExit(
        "No FIT files were found in the Weekly Runs folder."
    )


rows = []

for fit_file in fit_files:
    workout = read_fit_file(fit_file)

    start_time = workout["start_time"]

    if start_time is None:
        raise ValueError(
            f"No start time was found in {fit_file.name}"
        )

    local_start_time = convert_to_local_time(
        start_time
    )

    miles = meters_to_miles(
        workout["total_distance"] or 0
    )

    total_seconds = (
        workout["total_timer_time"] or 0
    )

    if miles > 0 and total_seconds > 0:
        average_pace = pace_from_time(
            miles,
            total_seconds,
        )
    else:
        average_pace = "—"

    lap_splits = []

    for lap in workout["laps"]:
        lap_miles_meters = lap.get("Miles") or 0
        lap_seconds = lap.get("Time") or 0

        lap_miles = meters_to_miles(
            lap_miles_meters
        )

        if (
            lap_miles <= 0
            or lap_seconds <= 0
        ):
            continue

        lap_splits.append(
            {
                "Lap": len(lap_splits) + 1,
                "Miles": lap_miles,
                "Time": seconds_to_hms(
                    lap_seconds
                ),
                "Pace": pace_from_time(
                    lap_miles,
                    lap_seconds,
                ),
                "Avg HR": lap.get("Avg HR"),
            }
        )

    rows.append(
        {
            "Start Time": local_start_time,
            "Date": (
                local_start_time
                .date()
                .isoformat()
            ),
            "Time of Day": (
                local_start_time
                .strftime("%I:%M %p")
                .lstrip("0")
            ),
            "Run Type": "Other",
            "Sport": workout.get("sport"),
            "Sub Sport": workout.get(
                "sub_sport"
            ),
            "Source File": workout[
                "source_file"
            ],
            "Miles": miles,
            "Time": seconds_to_hms(
                total_seconds
            ),
            "Pace (/mi)": average_pace,
            "Avg HR": workout[
                "avg_heart_rate"
            ],
            "Max HR": workout[
                "max_heart_rate"
            ],
            "Elevation (ft)": meters_to_feet(
                workout["total_ascent"] or 0
            ),
            "Cadence (spm)": optional_cadence(
                workout[
                    "avg_running_cadence"
                ]
            ),
            "Power (W)": workout[
                "avg_power"
            ],
            "Laps": lap_splits,
        }
    )


df = pd.DataFrame(rows)

df = (
    df.sort_values("Start Time")
    .reset_index(drop=True)
)

running_mask = df.apply(
    is_running_activity,
    axis=1,
)

running_df = (
    df[running_mask]
    .copy()
    .reset_index(drop=True)
)

if running_df.empty:
    summary = WeeklySummary(
        runs=0,
        mileage=0,
        total_seconds=0,
        average_pace="—",
        average_hr=0,
        max_hr=0,
        average_power=0,
        elevation_gain=0,
    )

    daily_mileage = pd.DataFrame(
        columns=["Date", "Miles"]
    )

else:
    summary = build_week_summary(
        running_df
    )

    daily_mileage = build_daily_mileage(
        running_df
    )

df = classify_runs(
    df,
    summary,
)

output = create_excel_report(
    df=df,
    summary=summary,
    daily_mileage=daily_mileage,
    output_path="Reports/Week_Data.xlsx",
)

print(f"Created report: {output}")