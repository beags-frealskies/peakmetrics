"""PeakMetrics report generator."""

from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from activity_overrides import (
    sync_overrides_from_latest_report,
)
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
from pdf_report import create_pdf_report
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
reports_dir = Path("Reports")

reports_dir.mkdir(
    parents=True,
    exist_ok=True,
)


activity_overrides, imported_changes, source_report = (
    sync_overrides_from_latest_report(
        reports_dir
    )
)

if imported_changes:
    print(
        f"Imported {imported_changes} activity "
        f"type correction(s) from "
        f"{source_report.name}."
    )


fit_files = sorted(
    runs_folder.glob("*.fit")
)

if not fit_files:
    raise SystemExit(
        "No FIT files were found in the "
        "Weekly Runs folder."
    )


rows = []

for fit_file in fit_files:
    workout = read_fit_file(
        fit_file
    )

    start_time = workout.get(
        "start_time"
    )

    if start_time is None:
        raise ValueError(
            f"No start time was found in "
            f"{fit_file.name}"
        )

    local_start_time = convert_to_local_time(
        start_time
    )

    distance_meters = (
        workout.get(
            "total_distance",
            0,
        )
        or 0
    )

    total_seconds = (
        workout.get(
            "total_timer_time",
            0,
        )
        or 0
    )

    miles = meters_to_miles(
        distance_meters
    )

    if miles > 0 and total_seconds > 0:
        average_pace = pace_from_time(
            miles,
            total_seconds,
        )
    else:
        average_pace = "N/A"

    lap_splits = []

    for lap in workout.get(
        "laps",
        [],
    ):
        lap_distance_meters = (
            lap.get(
                "total_distance",
                0,
            )
            or 0
        )

        lap_seconds = (
            lap.get(
                "total_timer_time",
                0,
            )
            or 0
        )

        lap_miles = meters_to_miles(
            lap_distance_meters
        )

        if (
            lap_miles <= 0
            or lap_seconds <= 0
        ):
            continue

        lap_splits.append(
            {
                "Lap": (
                    len(lap_splits)
                    + 1
                ),
                "Miles": lap_miles,
                "Time": seconds_to_hms(
                    lap_seconds
                ),
                "Pace": pace_from_time(
                    lap_miles,
                    lap_seconds,
                ),
                "Avg HR": lap.get(
                    "avg_heart_rate"
                ),
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
            "Sport": workout.get(
                "sport"
            ),
            "Sub Sport": workout.get(
                "sub_sport"
            ),
            "Source File": workout.get(
                "source_file",
                fit_file.name,
            ),
            "Miles": miles,
            "Time": seconds_to_hms(
                total_seconds
            ),
            "Pace (/mi)": average_pace,
            "Avg HR": workout.get(
                "avg_heart_rate"
            ),
            "Max HR": workout.get(
                "max_heart_rate"
            ),
            "Elevation (ft)": meters_to_feet(
                workout.get(
                    "total_ascent",
                    0,
                )
                or 0
            ),
            "Cadence (spm)": optional_cadence(
                workout.get(
                    "avg_running_cadence"
                )
            ),
            "Power (W)": workout.get(
                "avg_power"
            ),
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
        average_pace="N/A",
        average_hr=0,
        max_hr=0,
        average_power=0,
        elevation_gain=0,
    )

    daily_mileage = pd.DataFrame(
        columns=[
            "Date",
            "Miles",
        ]
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
    overrides=activity_overrides,
)


report_start = str(
    df["Date"].min()
)

report_end = str(
    df["Date"].max()
)

report_name = (
    f"PeakMetrics_"
    f"{report_start}_to_"
    f"{report_end}"
)


excel_output = create_excel_report(
    df=df,
    summary=summary,
    daily_mileage=daily_mileage,
    output_path=(
        reports_dir
        / f"{report_name}.xlsx"
    ),
)

pdf_output = create_pdf_report(
    df=df,
    summary=summary,
    daily_mileage=daily_mileage,
    output_path=(
        reports_dir
        / f"{report_name}.pdf"
    ),
)


print(
    f"Created Excel report: "
    f"{excel_output}"
)

print(
    f"Created PDF report: "
    f"{pdf_output}"
)

print(
    f"Saved activity overrides: "
    f"{len(activity_overrides)}"
)