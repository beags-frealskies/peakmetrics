"""Excel report generation helpers."""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from dashboard import draw_metric_card
from run_cards import create_report_sheet


def build_output_path(output_path):
    """Return a writable path without overwriting an existing report."""

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


def create_summary_sheet(wb, df, summary):
    """Create the weekly dashboard."""

    ws = wb.active
    ws.title = "Summary"
    ws.sheet_view.showGridLines = False

    ws["A1"] = "PeakMetrics"
    ws["A1"].font = Font(size=26, bold=True)

    ws["A2"] = "Weekly Training Report"
    ws["A2"].font = Font(size=15, color="667085")

    ws["A4"] = "Athlete"
    ws["B4"] = "Brady Eagar"

    ws["A5"] = "Team"
    ws["B5"] = "Utah Tech XC"

    dates = sorted(df["Date"])

    ws["A6"] = "Week"
    ws["B6"] = f"{dates[0]} → {dates[-1]}"

    for cell in ("A4", "A5", "A6"):
        ws[cell].font = Font(bold=True)

    draw_metric_card(
        ws, 9, 1, "Weekly Mileage", f"{summary.mileage:.1f} mi"
    )
    draw_metric_card(
        ws, 9, 5, "Average HR", f"{summary.average_hr} bpm"
    )
    draw_metric_card(
        ws, 9, 9, "Average Power", f"{summary.average_power} W"
    )

    draw_metric_card(ws, 14, 1, "Runs", summary.runs)
    draw_metric_card(ws, 14, 5, "Max HR", f"{summary.max_hr} bpm")
    draw_metric_card(
        ws, 14, 9, "Elevation", f"{summary.elevation_gain:,} ft"
    )

    draw_metric_card(ws, 19, 1, "Weekly Time", summary.weekly_time)
    draw_metric_card(ws, 19, 5, "Average Pace", summary.average_pace)

    for column in range(1, 13):
        ws.column_dimensions[get_column_letter(column)].width = 11


def friendly_day(value) -> str:
    """Convert an ISO date into a short weekday label."""

    try:
        return datetime.fromisoformat(str(value)).strftime("%a")
    except ValueError:
        return str(value)


def add_mileage_chart(ws, daily_mileage):
    """Add daily mileage totals, combining double runs by date."""

    data_start_row = 26
    data_column = 14

    ws.cell(data_start_row, data_column).value = "Day"
    ws.cell(data_start_row, data_column + 1).value = "Miles"

    for index, row in enumerate(
        daily_mileage.itertuples(),
        start=data_start_row + 1,
    ):
        ws.cell(index, data_column).value = friendly_day(row.Date)
        ws.cell(index, data_column + 1).value = float(row.Miles)

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Daily Mileage"
    chart.y_axis.title = "Miles"
    chart.x_axis.title = None
    chart.legend = None

    data = Reference(
        ws,
        min_col=data_column + 1,
        min_row=data_start_row,
        max_row=data_start_row + len(daily_mileage),
    )

    categories = Reference(
        ws,
        min_col=data_column,
        min_row=data_start_row + 1,
        max_row=data_start_row + len(daily_mileage),
    )

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)

    chart.height = 7
    chart.width = 15

    chart.dLbls = DataLabelList()
    chart.dLbls.showVal = True

    ws.add_chart(chart, "A25")

    ws.column_dimensions["N"].hidden = True
    ws.column_dimensions["O"].hidden = True


def create_excel_report(df, summary, daily_mileage, output_path):
    """Create the complete PeakMetrics workbook."""

    output_path = build_output_path(output_path)

    wb = Workbook()

    create_summary_sheet(wb, df, summary)
    add_mileage_chart(wb["Summary"], daily_mileage)
    create_report_sheet(wb, df)

    wb.save(output_path)

    return output_path