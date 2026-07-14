"""Analytics functions for PeakMetrics."""

from dataclasses import dataclass

import pandas as pd

from metrics import pace_from_time


@dataclass
class WeeklySummary:
    runs: int
    mileage: float
    total_seconds: int
    average_pace: str
    average_hr: int
    max_hr: int
    average_power: int
    elevation_gain: int

    @property
    def weekly_time(self):
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def build_week_summary(df) -> WeeklySummary:
    """Build weekly summary from the activity dataframe."""

    total_seconds = 0

    for time_value in df["Time"]:
        hours, minutes, seconds = map(
            int,
            str(time_value).split(":"),
        )

        total_seconds += (
            hours * 3600
            + minutes * 60
            + seconds
        )

    total_mileage = float(
        df["Miles"].sum()
    )

    return WeeklySummary(
        runs=len(df),
        mileage=round(total_mileage, 2),
        total_seconds=total_seconds,
        average_pace=pace_from_time(
            total_mileage,
            total_seconds,
        ),
        average_hr=round(
            df["Avg HR"].mean()
        ),
        max_hr=int(
            df["Max HR"].max()
        ),
        average_power=round(
            df["Power (W)"].mean()
        ),
        elevation_gain=round(
            df["Elevation (ft)"].sum()
        ),
    )


def clean_mileage(value):
    """Convert a mileage value into a usable float."""

    try:
        mileage = float(value)
    except (TypeError, ValueError):
        return 0.0

    if pd.isna(mileage):
        return 0.0

    return max(mileage, 0.0)


def build_daily_mileage(df):
    """Return daily totals while preserving each activity segment."""

    columns = [
        "Date",
        "Miles",
        "Segments",
    ]

    if df.empty:
        return pd.DataFrame(
            columns=columns
        )

    working_df = df.copy()

    sort_columns = ["Date"]

    if "Start Time" in working_df.columns:
        sort_columns.append(
            "Start Time"
        )

    working_df = working_df.sort_values(
        sort_columns
    )

    records = []

    for activity_date, day_group in working_df.groupby(
        "Date",
        sort=True,
    ):
        segments = []

        for _, activity in day_group.iterrows():
            miles = clean_mileage(
                activity.get("Miles")
            )

            if miles <= 0:
                continue

            segments.append(
                {
                    "Miles": round(miles, 2),
                    "Time of Day": str(
                        activity.get(
                            "Time of Day",
                            "",
                        )
                    ),
                    "Run Type": str(
                        activity.get(
                            "Run Type",
                            "",
                        )
                    ),
                }
            )

        if not segments:
            continue

        daily_total = sum(
            segment["Miles"]
            for segment in segments
        )

        records.append(
            {
                "Date": activity_date,
                "Miles": round(
                    daily_total,
                    2,
                ),
                "Segments": segments,
            }
        )

    return pd.DataFrame(
        records,
        columns=columns,
    )
