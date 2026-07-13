"""Excel report generation helpers."""

from pathlib import Path

from openpyxl import Workbook

from history_sheet import create_history_sheet
from run_cards import create_report_sheet
from summary_sheet import create_summary_sheet


def build_output_path(output_path):
    """Return a path without overwriting a report."""

    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not path.exists():
        return path

    counter = 1

    while True:
        candidate = path.parent / (
            f"{path.stem}_"
            f"{counter}"
            f"{path.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def create_activity_data_sheet(
    wb,
    df,
):
    """Store hidden dropdown-tracking information."""

    ws = wb.create_sheet(
        "_ActivityData"
    )

    ws.append(
        [
            "Source File",
            "Type Cell",
            "Generated Type",
            "Start Time",
        ]
    )

    start_row = 4

    for run in df.to_dict(
        "records"
    ):
        laps = run.get(
            "Laps"
        ) or []

        source_file = str(
            run.get(
                "Source File",
                "",
            )
        )

        generated_type = str(
            run.get(
                "Run Type",
                "Other",
            )
        )

        start_time = str(
            run.get(
                "Start Time",
                "",
            )
        )

        type_cell = (
            f"I{start_row}"
        )

        ws.append(
            [
                source_file,
                type_cell,
                generated_type,
                start_time,
            ]
        )

        end_row = max(
            start_row + 6,
            start_row + 3 + len(laps),
        )

        start_row = (
            end_row + 3
        )

    ws.sheet_state = "veryHidden"


def create_excel_report(
    df,
    summary,
    daily_mileage,
    weekly_history,
    output_path,
):
    """Create the complete PeakMetrics workbook."""

    output_path = build_output_path(
        output_path
    )

    wb = Workbook()

    create_summary_sheet(
        wb,
        df,
        summary,
        daily_mileage,
    )

    create_report_sheet(
        wb,
        df,
    )

    create_history_sheet(
        wb,
        weekly_history,
    )

    create_activity_data_sheet(
        wb,
        df,
    )

    wb.active = 0

    wb.save(
        output_path
    )

    return output_path