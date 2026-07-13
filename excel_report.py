"""Excel report generation helpers."""

import shutil
from pathlib import Path

from openpyxl import Workbook

from history_sheet import create_history_sheet
from report_archive import (
    archive_existing_reports,
    build_current_archive_path,
)
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

    reports_folder = (
        output_path.parent
    )

    archive_folder = (
        reports_folder
        / "Weekly Archive"
    )

    archive_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    current_archive_path = (
        build_current_archive_path(
            df,
            archive_folder,
        )
    )

    archive_existing_reports(
        reports_folder=reports_folder,
        archive_folder=archive_folder,
        weekly_history=weekly_history,
        current_archive_path=(
            current_archive_path
        ),
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
        archive_folder=archive_folder,
        current_archive_path=(
            current_archive_path
        ),
    )

    create_activity_data_sheet(
        wb,
        df,
    )

    wb.active = 0

    try:
        # Save the permanent canonical workbook first.
        # Saving only once also keeps embedded charts safe.
        wb.save(
            current_archive_path
        )

    except PermissionError as error:
        raise PermissionError(
            "PeakMetrics could not update the "
            "weekly archive workbook.\n\n"
            f"Close this file if it is open:\n"
            f"{current_archive_path}"
        ) from error

    # Create the normal numbered report as an exact
    # copy of the canonical weekly workbook.
    shutil.copy2(
        current_archive_path,
        output_path,
    )

    return output_path