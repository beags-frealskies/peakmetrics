"""Manage the PeakMetrics weekly Excel archive."""

import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path


REPORT_FILENAME_PATTERN = re.compile(
    r"^PeakMetrics_"
    r"(\d{4}-\d{2}-\d{2})"
    r"_to_"
    r"(\d{4}-\d{2}-\d{2})"
    r"(?:_\d+)?"
    r"\.xlsx$",
    re.IGNORECASE,
)


def parse_date_value(value):
    """Convert a stored value into a date."""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.fromisoformat(
        str(value)
    ).date()


def get_week_bounds(value):
    """Return the Monday and Sunday surrounding a date."""

    activity_date = parse_date_value(
        value
    )

    week_start = (
        activity_date
        - timedelta(
            days=activity_date.weekday()
        )
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

    return week_start, week_end


def canonical_week_path(
    archive_folder,
    week_start,
    week_end,
):
    """Build the permanent workbook path for one week."""

    archive_folder = Path(
        archive_folder
    )

    week_start = parse_date_value(
        week_start
    )

    week_end = parse_date_value(
        week_end
    )

    filename = (
        f"PeakMetrics_"
        f"{week_start.isoformat()}"
        f"_to_"
        f"{week_end.isoformat()}"
        f".xlsx"
    )

    return archive_folder / filename


def build_current_archive_path(
    df,
    archive_folder,
):
    """Build the canonical archive path for the current report."""

    if df.empty:
        raise ValueError(
            "The current report has no activities."
        )

    activity_dates = [
        parse_date_value(value)
        for value in df["Date"]
    ]

    first_date = min(
        activity_dates
    )

    week_start, week_end = get_week_bounds(
        first_date
    )

    return canonical_week_path(
        archive_folder,
        week_start,
        week_end,
    )


def parse_report_filename(
    report_path,
):
    """Read the date range from a PeakMetrics filename."""

    match = REPORT_FILENAME_PATTERN.match(
        Path(report_path).name
    )

    if match is None:
        return None

    report_start = parse_date_value(
        match.group(1)
    )

    report_end = parse_date_value(
        match.group(2)
    )

    return report_start, report_end


def report_belongs_to_week(
    report_path,
    week_start,
    week_end,
):
    """Return True when a report's dates belong to a week."""

    report_dates = parse_report_filename(
        report_path
    )

    if report_dates is None:
        return False

    report_start, report_end = (
        report_dates
    )

    return (
        week_start
        <= report_start
        <= week_end
        and week_start
        <= report_end
        <= week_end
    )


def archive_existing_reports(
    reports_folder,
    archive_folder,
    weekly_history,
    current_archive_path,
):
    """Migrate existing weekly workbooks into the archive."""

    reports_folder = Path(
        reports_folder
    )

    archive_folder = Path(
        archive_folder
    )

    current_archive_path = Path(
        current_archive_path
    )

    archive_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    current_resolved = (
        current_archive_path.resolve()
    )

    root_reports = [
        report_path
        for report_path
        in reports_folder.glob(
            "PeakMetrics_*.xlsx"
        )
        if (
            report_path.is_file()
            and not report_path.name.startswith(
                "~$"
            )
        )
    ]

    copied_count = 0

    for record in weekly_history.to_dict(
        "records"
    ):
        week_start = parse_date_value(
            record["Week Start"]
        )

        week_end = parse_date_value(
            record["Week End"]
        )

        archive_path = canonical_week_path(
            archive_folder,
            week_start,
            week_end,
        )

        # The current week will be created from the
        # newly generated workbook, not an old copy.
        if (
            archive_path.resolve()
            == current_resolved
        ):
            continue

        candidates = [
            report_path
            for report_path in root_reports
            if report_belongs_to_week(
                report_path,
                week_start,
                week_end,
            )
        ]

        if not candidates:
            continue

        newest_candidate = max(
            candidates,
            key=lambda path: (
                path.stat().st_mtime_ns
            ),
        )

        should_copy = (
            not archive_path.exists()
        )

        if archive_path.exists():
            should_copy = (
                newest_candidate
                .stat()
                .st_mtime_ns
                > archive_path
                .stat()
                .st_mtime_ns
            )

        if not should_copy:
            continue

        shutil.copy2(
            newest_candidate,
            archive_path,
        )

        copied_count += 1

    return copied_count