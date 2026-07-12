"""Weekly trend calculations from the PeakMetrics database."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from run_classifier import is_running_activity
from training_history import DEFAULT_DATABASE_PATH


HISTORY_COLUMNS = [
    "Week Start",
    "Week End",
    "Week",
    "Miles",
    "Runs",
    "Workouts",
    "Long Runs",
    "Strides",
    "Time",
    "Average Pace",
    "Average HR",
]


def default_history_summary():
    """Return blank historical summary metrics."""

    current_year = date.today().year

    return {
        "Current Year": current_year,
        "Total Weeks": 0,
        "Total Mileage": 0.0,
        "Average Week": 0.0,
        "YTD Mileage": 0.0,
        "YTD Average Pace": "N/A",
        "Historical Average Pace": "N/A",
    }


def empty_history():
    """Return an empty weekly-history table."""

    history = pd.DataFrame(
        columns=HISTORY_COLUMNS
    )

    history.attrs["summary"] = (
        default_history_summary()
    )

    return history


def format_duration(total_seconds):
    """Convert seconds into a readable weekly duration."""

    total_seconds = int(
        round(total_seconds)
    )

    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    return f"{hours}h {minutes}m"


def format_pace(
    total_seconds,
    total_miles,
):
    """Calculate weighted average pace."""

    if (
        total_miles is None
        or total_miles <= 0
    ):
        return "N/A"

    pace_seconds = int(
        round(
            total_seconds
            / total_miles
        )
    )

    minutes = pace_seconds // 60
    seconds = pace_seconds % 60

    return (
        f"{minutes}:"
        f"{seconds:02d}/mi"
    )


def build_week_label(
    week_start,
    week_end,
):
    """Create a short label such as 6/29-7/5."""

    return (
        f"{week_start.month}/"
        f"{week_start.day}-"
        f"{week_end.month}/"
        f"{week_end.day}"
    )


def weighted_average_hr(group):
    """Calculate duration-weighted average heart rate."""

    heart_rate_rows = group[
        group["Avg HR"].notna()
    ].copy()

    if heart_rate_rows.empty:
        return 0

    weights = heart_rate_rows[
        "Duration Seconds"
    ].clip(lower=0)

    if weights.sum() > 0:
        weighted_total = (
            heart_rate_rows["Avg HR"]
            * weights
        ).sum()

        return int(
            round(
                weighted_total
                / weights.sum()
            )
        )

    return int(
        round(
            heart_rate_rows[
                "Avg HR"
            ].mean()
        )
    )


def build_history_summary(activities):
    """Calculate year-to-date and all-time metrics."""

    current_year = date.today().year

    total_miles = float(
        activities["Miles"].sum()
    )

    total_seconds = float(
        activities[
            "Duration Seconds"
        ].sum()
    )

    ytd_activities = activities[
        activities["Date"].dt.year
        == current_year
    ].copy()

    ytd_miles = float(
        ytd_activities["Miles"].sum()
    )

    ytd_seconds = float(
        ytd_activities[
            "Duration Seconds"
        ].sum()
    )

    return {
        "Current Year": current_year,
        "Total Mileage": total_miles,
        "YTD Mileage": ytd_miles,
        "YTD Average Pace": format_pace(
            ytd_seconds,
            ytd_miles,
        ),
        "Historical Average Pace": format_pace(
            total_seconds,
            total_miles,
        ),
    }


def load_weekly_history(
    database_path=DEFAULT_DATABASE_PATH,
):
    """Load running history grouped into Monday-Sunday weeks."""

    database_path = Path(
        database_path
    )

    if not database_path.exists():
        return empty_history()

    connection = sqlite3.connect(
        database_path
    )

    try:
        activities = pd.read_sql_query(
            """
            SELECT
                activity_date,
                start_time,
                run_type,
                sport,
                sub_sport,
                miles,
                duration_seconds,
                avg_hr
            FROM activities
            ORDER BY start_time
            """,
            connection,
        )

    finally:
        connection.close()

    if activities.empty:
        return empty_history()

    activities["Is Running"] = (
        activities.apply(
            lambda row: is_running_activity(
                {
                    "Sport": row["sport"],
                    "Sub Sport": row[
                        "sub_sport"
                    ],
                }
            ),
            axis=1,
        )
    )

    activities = activities[
        activities["Is Running"]
    ].copy()

    if activities.empty:
        return empty_history()

    activities["Date"] = pd.to_datetime(
        activities["activity_date"],
        errors="coerce",
    )

    activities = activities[
        activities["Date"].notna()
    ].copy()

    if activities.empty:
        return empty_history()

    activities["Miles"] = pd.to_numeric(
        activities["miles"],
        errors="coerce",
    ).fillna(0.0)

    activities[
        "Duration Seconds"
    ] = pd.to_numeric(
        activities["duration_seconds"],
        errors="coerce",
    ).fillna(0)

    activities["Avg HR"] = pd.to_numeric(
        activities["avg_hr"],
        errors="coerce",
    )

    history_summary = build_history_summary(
        activities
    )

    activities["Week Start"] = (
        activities["Date"]
        - pd.to_timedelta(
            activities[
                "Date"
            ].dt.weekday,
            unit="D",
        )
    )

    records = []

    for week_start, group in activities.groupby(
        "Week Start",
        sort=True,
    ):
        week_start_date = (
            week_start.date()
        )

        week_end_date = (
            week_start_date
            + timedelta(days=6)
        )

        total_miles = float(
            group["Miles"].sum()
        )

        total_seconds = int(
            group[
                "Duration Seconds"
            ].sum()
        )

        run_types = group[
            "run_type"
        ].fillna("Other")

        records.append(
            {
                "Week Start": (
                    week_start_date
                    .isoformat()
                ),
                "Week End": (
                    week_end_date
                    .isoformat()
                ),
                "Week": build_week_label(
                    week_start_date,
                    week_end_date,
                ),
                "Miles": round(
                    total_miles,
                    2,
                ),
                "Runs": int(
                    len(group)
                ),
                "Workouts": int(
                    (
                        run_types
                        == "Workout"
                    ).sum()
                ),
                "Long Runs": int(
                    (
                        run_types
                        == "Long Run"
                    ).sum()
                ),
                "Strides": int(
                    (
                        run_types
                        == "Strides"
                    ).sum()
                ),
                "Time": format_duration(
                    total_seconds
                ),
                "Average Pace": format_pace(
                    total_seconds,
                    total_miles,
                ),
                "Average HR": (
                    weighted_average_hr(
                        group
                    )
                ),
            }
        )

    history = pd.DataFrame(
        records,
        columns=HISTORY_COLUMNS,
    )

    total_weeks = len(history)

    average_week = (
        float(history["Miles"].mean())
        if total_weeks > 0
        else 0.0
    )

    history_summary[
        "Total Weeks"
    ] = total_weeks

    history_summary[
        "Average Week"
    ] = average_week

    history.attrs["summary"] = (
        history_summary
    )

    return history