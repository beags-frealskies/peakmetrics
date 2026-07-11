"""Analytics functions for PeakMetrics."""

from dataclasses import dataclass

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
    """Build weekly summary from Daily Runs dataframe."""

    total_seconds = 0

    for t in df["Time"]:
        h, m, s = map(int, t.split(":"))
        total_seconds += h * 3600 + m * 60 + s

    return WeeklySummary(
        runs=len(df),
        mileage=round(df["Miles"].sum(), 2),
        total_seconds=total_seconds,
        average_pace=pace_from_time(df["Miles"].sum(), total_seconds),
        average_hr=round(df["Avg HR"].mean()),
        max_hr=int(df["Max HR"].max()),
        average_power=round(df["Power (W)"].mean()),
        elevation_gain=round(df["Elevation (ft)"].sum()),
    )
def build_daily_mileage(df):
    """Return mileage totals grouped by date."""

    daily = (
        df.groupby("Date")["Miles"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    return daily