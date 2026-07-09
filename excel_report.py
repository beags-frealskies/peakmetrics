"""Excel report generation helpers."""

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment


def build_output_path(output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        return path

    i = 1
    while True:
        candidate = path.parent / f"{path.stem}_{i}{path.suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def style_sheet(ws):
    """Apply formatting to a worksheet."""

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
            len(str(c.value)) if c.value is not None else 0
            for c in column
        )
        ws.column_dimensions[column[0].column_letter].width = width + 3


def create_summary_sheet(wb, df):
    ws = wb.create_sheet("Summary", 0)

    ws["A1"] = "Weekly Training Summary"
    ws["A1"].font = Font(size=18, bold=True)

    ws["A3"] = "Runs"
    ws["B3"] = len(df)

    ws["A4"] = "Mileage"
    ws["B4"] = round(df["Miles"].sum(), 2)

    ws["A5"] = "Average HR"
    ws["B5"] = round(df["Avg HR"].mean())

    ws["A6"] = "Max HR"
    ws["B6"] = df["Max HR"].max()

    ws["A7"] = "Elevation Gain (ft)"
    ws["B7"] = df["Elevation (ft)"].sum()

    ws["A8"] = "Average Power"
    ws["B8"] = round(df["Power (W)"].mean())

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 15


def create_excel_report(df, output_path):

    output_path = build_output_path(output_path)

    df.to_excel(output_path, sheet_name="Daily Runs", index=False)

    wb = load_workbook(output_path)

    create_summary_sheet(wb, df)

    style_sheet(wb["Daily Runs"])

    wb.save(output_path)

    return output_path