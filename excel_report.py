"""Excel report generation helpers."""

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)


def build_output_path(output_path):
    """Return a writable Excel output path, avoiding collisions."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def style_daily_runs_sheet(ws):
    """Apply formatting to the Daily Runs worksheet."""

    blue = PatternFill(fill_type="solid", fgColor="2F75B5")
    white = Font(color="FFFFFF", bold=True)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    for cell in ws[1]:
        cell.fill = blue
        cell.font = white
        cell.alignment = Alignment(horizontal="center")

    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal="center")

    for column in ws.columns:
        width = max(
            len(str(cell.value)) if cell.value is not None else 0
            for cell in column
        )

        ws.column_dimensions[column[0].column_letter].width = width + 3


def create_summary_sheet(wb, df):
    """Create the Summary worksheet."""

    ws = wb.create_sheet("Summary", 0)

    # ----------------------------
    # Report Header
    # ----------------------------

    ws["A1"] = "PeakMetrics"
    ws["A1"].font = Font(size=26, bold=True)

    ws["A2"] = "Weekly Training Report"
    ws["A2"].font = Font(size=15)

    ws["A4"] = "Athlete"
    ws["B4"] = "Brady Eagar"

    ws["A5"] = "Team"
    ws["B5"] = "Utah Tech XC"

    ws["A6"] = "Week"

    dates = sorted(df["Date"])
    ws["B6"] = f"{dates[0]}  →  {dates[-1]}"

    # Statistics
    total_runs = len(df)
    total_miles = df["Miles"].sum()
    total_time_seconds = 0

    for t in df["Time"]:
        h, m, s = map(int, t.split(":"))
        total_time_seconds += h * 3600 + m * 60 + s

    hours = total_time_seconds // 3600
    mins = (total_time_seconds % 3600) // 60

    weekly_time = f"{hours}h {mins}m"

    avg_hr = round(df["Avg HR"].mean())
    max_hr = df["Max HR"].max()

    avg_seconds = total_time_seconds / total_miles if total_miles else 0

    pace_minutes = int(avg_seconds // 60)
    pace_seconds = int(avg_seconds % 60)

    average_pace = f"{pace_minutes}:{pace_seconds:02d} /mi"

    total_elevation = round(df["Elevation (ft)"].sum())

    avg_power = round(df["Power (W)"].mean())

    stats = [
        ("Runs", total_runs),
        ("Total Mileage", f"{total_miles:.2f} mi"),
        ("Average HR", f"{avg_hr} bpm"),
        ("Maximum HR", f"{max_hr} bpm"),
        ("Elevation Gain", f"{total_elevation:,} ft"),
        ("Average Power", f"{avg_power} W"),
    ]

    def draw_metric_card(ws, row, col, title, value, color):
        """Draw one dashboard metric card."""

        fill = PatternFill(fill_type="solid", fgColor=color)

        border = Border(
            left=Side(style="medium"),
            right=Side(style="medium"),
            top=Side(style="medium"),
            bottom=Side(style="medium"),
        )

        ws.merge_cells(
            start_row=row,
            start_column=col,
            end_row=row + 3,
            end_column=col + 2,
        )

        cell = ws.cell(row=row, column=col)

        cell.value = f"{value}\n\n{title}"

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        cell.fill = fill

        cell.font = Font(
            size=22,
            bold=True,
            color="FFFFFF",
        )

        for r in range(row, row + 4):
            for c in range(col, col + 2 + 1):
                ws.cell(r, c).fill = fill
                ws.cell(r, c).border = border

def create_excel_report(df, summary, output_path):
    """Create the complete Excel workbook."""

    output_path = build_output_path(output_path)

    # Write Daily Runs sheet
    df.to_excel(output_path, sheet_name="Daily Runs", index=False)

    wb = load_workbook(output_path)

    # Create Summary sheet
    create_summary_sheet(wb, df)

    # Format Daily Runs
    style_daily_runs_sheet(wb["Daily Runs"])

    wb.save(output_path)

    return output_path