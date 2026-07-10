from pathlib import Path

import pandas as pd

from parser import read_fit_file
from metrics import (
    meters_to_miles,
    meters_to_feet,
    cadence_to_spm,
    seconds_to_hms,
    pace_from_time,
)
from excel_report import create_excel_report

# -----------------------
# Read all FIT files
# -----------------------

runs_folder = Path("Weekly Runs")
fit_files = sorted(runs_folder.glob("*.fit"))

rows = []

for fit_file in fit_files:
    w = read_fit_file(fit_file)

    miles = meters_to_miles(w["total_distance"])

    rows.append({
        "Date": str(w["start_time"].date()),
        "Miles": miles,
        "Time": seconds_to_hms(w["total_timer_time"]),
        "Pace (/mi)": pace_from_time(miles, w["total_timer_time"]),
        "Avg HR": w["avg_heart_rate"],
        "Max HR": w["max_heart_rate"],
        "Elevation (ft)": meters_to_feet(w["total_ascent"]),
        "Cadence (spm)": cadence_to_spm(w["avg_running_cadence"]),
        "Power (W)": w["avg_power"],
    })

df = pd.DataFrame(rows)
summary = {
    "athlete": "Brady Eagar",
    "team": "Utah Tech XC",
    "week": f"{df['Date'].min()} to {df['Date'].max()}",
}
output = create_excel_report(
    df,
    summary,
    "Reports/Week_Data.xlsx",
)
print("\n================================")
print(" Weekly Report Created!")
print("================================")
print(output)