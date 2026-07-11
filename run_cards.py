"""Strava-style run cards for PeakMetrics."""

from openpyxl.worksheet.datavalidation import DataValidation

from datetime import datetime
import math

from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter


CARD_FILL = PatternFill(
    fill_type="solid",
    fgColor="F8FAFC",
)

TITLE_FILL = PatternFill(
    fill_type="solid",
    fgColor="EAF2FF",
)

LAP_TITLE_FILL = PatternFill(
    fill_type="solid",
    fgColor="E8EEF5",
)

LAP_HEADER_FILL = PatternFill(
    fill_type="solid",
    fgColor="F0F4F8",
)

THIN_GRAY = Side(
    style="thin",
    color="D9E2EC",
)

CARD_BORDER = Border(
    left=THIN_GRAY,
    right=THIN_GRAY,
    top=THIN_GRAY,
    bottom=THIN_GRAY,
)


RUN_TYPE_STYLES = {
    "Easy Run": {
        "fill": "EAF4FC",
        "text": "1F4E78",
    },
    "Long Run": {
        "fill": "E2F0D9",
        "text": "375623",
    },
    "Workout": {
        "fill": "FCE4D6",
        "text": "9C0006",
    },
    "Strides": {
        "fill": "FFF2CC",
        "text": "7F6000",
    },
    "Cross Training": {
        "fill": "E4DFEC",
        "text": "5F497A",
    },
    "Core": {
        "fill": "DDEBF7",
        "text": "1F4E78",
    },
    "Lifting": {
        "fill": "D9EAD3",
        "text": "274E13",
    },
    "Other": {
        "fill": "E7E6E6",
        "text": "595959",
    },
}

ACTIVITY_TYPES = [
    "Easy Run",
    "Long Run",
    "Workout",
    "Strides",
    "Cross Training",
    "Core",
    "Lifting",
    "Other",
]

def get_run_type_style(run_type):
    """Return the header colors for an activity category."""

    style = RUN_TYPE_STYLES.get(
        run_type,
        RUN_TYPE_STYLES["Other"],
    )

    fill = PatternFill(
        fill_type="solid",
        fgColor=style["fill"],
    )

    return fill, style["text"]


def friendly_date(value):
    """Convert an ISO date into a readable date."""

    try:
        date = datetime.fromisoformat(str(value))
        return date.strftime("%A, %B %d")
    except ValueError:
        return str(value)


def is_missing(value):
    """Check whether a metric is missing."""

    if value is None:
        return True

    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def format_number(value, suffix="", decimals=0):
    """Format a numeric metric safely."""

    if is_missing(value):
        return "—"

    number = float(value)

    if decimals == 0:
        text = f"{number:.0f}"
    else:
        text = f"{number:.{decimals}f}"

    if suffix:
        return f"{text} {suffix}"

    return text


def format_text(value):
    """Format a text metric safely."""

    if value is None or str(value).strip() == "":
        return "—"

    return str(value)


def add_metric(
    ws,
    value_row,
    label_row,
    start_col,
    end_col,
    value,
    label,
):
    """Add one metric to the left side of a run card."""

    ws.merge_cells(
        start_row=value_row,
        start_column=start_col,
        end_row=value_row,
        end_column=end_col,
    )

    ws.merge_cells(
        start_row=label_row,
        start_column=start_col,
        end_row=label_row,
        end_column=end_col,
    )

    value_cell = ws.cell(value_row, start_col)
    value_cell.value = value
    value_cell.font = Font(
        size=14,
        bold=True,
        color="1F2937",
    )
    value_cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
    )

    label_cell = ws.cell(label_row, start_col)
    label_cell.value = label
    label_cell.font = Font(
        size=9,
        color="667085",
    )
    label_cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
    )


def merge_lap_cell(
    ws,
    row,
    start_col,
    end_col,
    value,
    bold=False,
):
    """Create one cell in the lap-splits table."""

    ws.merge_cells(
        start_row=row,
        start_column=start_col,
        end_row=row,
        end_column=end_col,
    )

    cell = ws.cell(row, start_col)
    cell.value = value
    cell.font = Font(
        size=9,
        bold=bold,
        color="344054",
    )
    cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
    )


def draw_run_card(
    ws,
    start_row,
    run,
    activity_type_validation,
):
    """Draw one activity card and return its ending row."""

    laps = run.get("Laps") or []

    # Seven rows are needed for the standard metrics.
    # Longer lap lists automatically make the card taller.
    end_row = max(
        start_row + 6,
        start_row + 3 + len(laps),
    )

    # Date and AM/PM on the left.
    ws.merge_cells(
        start_row=start_row,
        start_column=1,
        end_row=start_row,
        end_column=8,
    )

    # Run type on the right.
    ws.merge_cells(
        start_row=start_row,
        start_column=9,
        end_row=start_row,
        end_column=16,
    )

    # Left-side metric blocks.
    metric_columns = [
        (1, 2),
        (3, 4),
        (5, 6),
        (7, 8),
    ]

    for start_col, end_col in metric_columns:
        ws.merge_cells(
            start_row=start_row + 2,
            start_column=start_col,
            end_row=start_row + 2,
            end_column=end_col,
        )
        ws.merge_cells(
            start_row=start_row + 3,
            start_column=start_col,
            end_row=start_row + 3,
            end_column=end_col,
        )
        ws.merge_cells(
            start_row=start_row + 5,
            start_column=start_col,
            end_row=start_row + 5,
            end_column=end_col,
        )
        ws.merge_cells(
            start_row=start_row + 6,
            start_column=start_col,
            end_row=start_row + 6,
            end_column=end_col,
        )

    # Lap title.
    ws.merge_cells(
        start_row=start_row + 2,
        start_column=9,
        end_row=start_row + 2,
        end_column=16,
    )

    # Lap column headings.
    lap_columns = [
        (9, 10),
        (11, 12),
        (13, 14),
        (15, 16),
    ]

    for start_col, end_col in lap_columns:
        ws.merge_cells(
            start_row=start_row + 3,
            start_column=start_col,
            end_row=start_row + 3,
            end_column=end_col,
        )

    # Create the lap rows.
    if laps:
        for offset, lap in enumerate(laps, start=4):
            lap_row = start_row + offset

            for start_col, end_col in lap_columns:
                ws.merge_cells(
                    start_row=lap_row,
                    start_column=start_col,
                    end_row=lap_row,
                    end_column=end_col,
                )
    else:
        ws.merge_cells(
            start_row=start_row + 4,
            start_column=9,
            end_row=start_row + 4,
            end_column=16,
        )

    # Base styling for the complete card.
    for row in range(start_row, end_row + 1):
        for column in range(1, 17):
            cell = ws.cell(row, column)
            cell.fill = CARD_FILL
            cell.border = CARD_BORDER

    # Header styling based on activity type.
    run_type = str(
        run.get("Run Type") or "Other"
    )

    header_fill, header_text_color = (
        get_run_type_style(run_type)
    )

    for column in range(1, 17):
        ws.cell(
            start_row,
            column,
        ).fill = header_fill

    left_title = ws.cell(start_row, 1)
    left_title.value = (
        f"{friendly_date(run['Date'])}"
        f"  •  {run.get('Time of Day', '')}"
    )
    left_title.font = Font(
        size=13,
        bold=True,
        color="1F2937",
    )
    left_title.alignment = Alignment(
        horizontal="left",
        vertical="center",
        indent=1,
    )

    right_title = ws.cell(start_row, 9)
    right_title.value = run.get(
        "Run Type",
        "Run",
    )
    right_title.font = Font(
        size=13,
        bold=True,
        color="1F2937",
    )
    right_title.alignment = Alignment(
        horizontal="right",
        vertical="center",
        indent=1,
    )
    activity_type_validation.add(
    right_title
)

    # Main run metrics.
    add_metric(
        ws,
        start_row + 2,
        start_row + 3,
        1,
        2,
        format_number(
            run.get("Miles"),
            "mi",
            decimals=2,
        ),
        "Distance",
    )

    add_metric(
        ws,
        start_row + 2,
        start_row + 3,
        3,
        4,
        format_text(run.get("Time")),
        "Time",
    )

    add_metric(
        ws,
        start_row + 2,
        start_row + 3,
        5,
        6,
        format_text(run.get("Pace (/mi)")),
        "Average Pace",
    )

    add_metric(
        ws,
        start_row + 2,
        start_row + 3,
        7,
        8,
        format_number(
            run.get("Avg HR"),
            "bpm",
        ),
        "Average HR",
    )

    add_metric(
        ws,
        start_row + 5,
        start_row + 6,
        1,
        2,
        format_number(
            run.get("Elevation (ft)"),
            "ft",
        ),
        "Elevation",
    )

    add_metric(
        ws,
        start_row + 5,
        start_row + 6,
        3,
        4,
        format_number(
            run.get("Power (W)"),
            "W",
        ),
        "Average Power",
    )

    add_metric(
        ws,
        start_row + 5,
        start_row + 6,
        5,
        6,
        format_number(
            run.get("Max HR"),
            "bpm",
        ),
        "Maximum HR",
    )

    add_metric(
        ws,
        start_row + 5,
        start_row + 6,
        7,
        8,
        format_number(
            run.get("Cadence (spm)"),
            "spm",
        ),
        "Cadence",
    )

    # Lap-splits panel.
    lap_title = ws.cell(start_row + 2, 9)
    lap_title.value = "Lap Splits"
    lap_title.fill = LAP_TITLE_FILL
    lap_title.font = Font(
        size=11,
        bold=True,
        color="344054",
    )
    lap_title.alignment = Alignment(
        horizontal="center",
        vertical="center",
    )

    lap_headings = [
        ("Lap", 9, 10),
        ("Distance", 11, 12),
        ("Pace", 13, 14),
        ("Avg HR", 15, 16),
    ]

    for heading, start_col, end_col in lap_headings:
        cell = ws.cell(start_row + 3, start_col)
        cell.value = heading
        cell.fill = LAP_HEADER_FILL
        cell.font = Font(
            size=9,
            bold=True,
            color="475467",
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        for column in range(start_col, end_col + 1):
            ws.cell(
                start_row + 3,
                column,
            ).fill = LAP_HEADER_FILL

    if laps:
        for lap_index, lap in enumerate(laps):
            lap_row = start_row + 4 + lap_index

            merge_lap_cell(
                ws,
                lap_row,
                9,
                10,
                lap.get("Lap", lap_index + 1),
                bold=True,
            )

            merge_lap_cell(
                ws,
                lap_row,
                11,
                12,
                format_number(
                    lap.get("Miles"),
                    "mi",
                    decimals=2,
                ),
            )

            merge_lap_cell(
                ws,
                lap_row,
                13,
                14,
                format_text(lap.get("Pace")),
            )

            merge_lap_cell(
                ws,
                lap_row,
                15,
                16,
                format_number(
                    lap.get("Avg HR"),
                    "bpm",
                ),
            )

            ws.row_dimensions[lap_row].height = 20
    else:
        no_laps = ws.cell(start_row + 4, 9)
        no_laps.value = "No lap data found"
        no_laps.font = Font(
            size=9,
            italic=True,
            color="98A2B3",
        )
        no_laps.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    ws.row_dimensions[start_row].height = 28
    ws.row_dimensions[start_row + 1].height = 8
    ws.row_dimensions[start_row + 2].height = 25
    ws.row_dimensions[start_row + 3].height = 21
    ws.row_dimensions[start_row + 5].height = 25

    return end_row


def create_report_sheet(wb, df):
    """Create the chronological run-card report."""

    ws = wb.create_sheet("Report")
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 85

    activity_type_validation = DataValidation(
        type="list",
        formula1=(
            f'"{",".join(ACTIVITY_TYPES)}"'
        ),
        allow_blank=False,
    )

    activity_type_validation.promptTitle = (
        "Activity Type"
    )

    activity_type_validation.prompt = (
        "Choose the correct activity category."
    )

    activity_type_validation.errorTitle = (
        "Invalid Activity Type"
    )

    activity_type_validation.error = (
        "Choose an activity type from the dropdown."
    )

    activity_type_validation.showInputMessage = True
    activity_type_validation.showErrorMessage = True

    ws.add_data_validation(activity_type_validation)

    ws.merge_cells("A1:P1")
    ws["A1"] = "Weekly Runs"
    ws["A1"].font = Font(
        size=24,
        bold=True,
    )
    ws["A1"].alignment = Alignment(
        vertical="center",
    )
    ws.row_dimensions[1].height = 34

    ws.merge_cells("A2:P2")
    ws["A2"] = f"{len(df)} activities"
    ws["A2"].font = Font(
        size=11,
        color="667085",
    )

    # Main metrics area.
    for column in range(1, 9):
        ws.column_dimensions[get_column_letter(column)].width = 10

    # Lap-splits area.
    for column in range(9, 17):
        ws.column_dimensions[get_column_letter(column)].width = 8

    start_row = 4

    for run in df.to_dict("records"):
        end_row = draw_run_card(
            ws,
            start_row,
            run,
            activity_type_validation,
        )
        start_row = end_row + 3

    ws.freeze_panes = "A4"

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True