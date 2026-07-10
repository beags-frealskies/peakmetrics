from metrics import pace_from_time


def build_week_summary(df):
    """Calculate weekly summary statistics."""

    total_runs = len(df)

    total_miles = df["Miles"].sum()

    total_seconds = 0

    for t in df["Time"]:
        h, m, s = map(int, t.split(":"))
        total_seconds += h * 3600 + m * 60 + s

    average_hr = round(df["Avg HR"].mean())

    max_hr = int(df["Max HR"].max())

    average_power = round(df["Power (W)"].mean())

    elevation_gain = round(df["Elevation (ft)"].sum())

    average_pace = pace_from_time(total_miles, total_seconds)

    return {
        "Runs": total_runs,
        "Mileage": round(total_miles, 2),
        "Time": total_seconds,
        "Average Pace": average_pace,
        "Average HR": average_hr,
        "Maximum HR": max_hr,
        "Average Power": average_power,
        "Elevation Gain": elevation_gain,
    }