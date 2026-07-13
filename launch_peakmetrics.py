"""Friendly one-click launcher for PeakMetrics."""

import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PROJECT_ROOT = Path(__file__).resolve().parent

APP_PATH = PROJECT_ROOT / "app.py"
CONFIG_PATH = PROJECT_ROOT / "config.json"

RUNS_FOLDER = PROJECT_ROOT / "Weekly Runs"
REPORTS_FOLDER = PROJECT_ROOT / "Reports"
DATA_FOLDER = PROJECT_ROOT / "Data"


def print_heading(message):
    """Print a visible launcher heading."""

    print()
    print("=" * 62)
    print(message)
    print("=" * 62)


def create_required_folders():
    """Create all folders required by PeakMetrics."""

    for folder in (
        RUNS_FOLDER,
        REPORTS_FOLDER,
        DATA_FOLDER,
    ):
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def validate_config():
    """Load and validate config.json."""

    if not CONFIG_PATH.exists():
        raise ValueError(
            "config.json was not found.\n\n"
            "Create config.json in the main "
            "PeakMetrics project folder."
        )

    try:
        with CONFIG_PATH.open(
            "r",
            encoding="utf-8",
        ) as config_file:
            config = json.load(
                config_file
            )

    except json.JSONDecodeError as error:
        raise ValueError(
            "config.json contains invalid JSON.\n"
            f"Check line {error.lineno}, "
            f"column {error.colno}."
        ) from error

    required_settings = (
        "athlete_name",
        "team",
        "timezone",
    )

    missing_settings = []

    for setting in required_settings:
        value = str(
            config.get(
                setting,
                "",
            )
        ).strip()

        if not value:
            missing_settings.append(
                setting
            )

    if missing_settings:
        raise ValueError(
            "config.json is missing these settings: "
            + ", ".join(missing_settings)
        )

    timezone_name = str(
        config["timezone"]
    ).strip()

    try:
        ZoneInfo(
            timezone_name
        )

    except ZoneInfoNotFoundError as error:
        raise ValueError(
            "The timezone in config.json is invalid: "
            f"{timezone_name}"
        ) from error

    return config


def find_fit_files():
    """Return FIT files currently ready to process."""

    return sorted(
        file_path
        for file_path in RUNS_FOLDER.iterdir()
        if (
            file_path.is_file()
            and file_path.suffix.lower() == ".fit"
        )
    )


def snapshot_excel_reports():
    """Record the existing Excel reports and timestamps."""

    snapshot = {}

    for report_path in REPORTS_FOLDER.glob(
        "*.xlsx"
    ):
        try:
            snapshot[
                report_path.resolve()
            ] = report_path.stat().st_mtime_ns

        except OSError:
            continue

    return snapshot


def find_newest_generated_report(
    previous_snapshot,
):
    """Find an Excel report created or updated by this run."""

    changed_reports = []

    for report_path in REPORTS_FOLDER.glob(
        "*.xlsx"
    ):
        try:
            resolved_path = report_path.resolve()
            modified_time = (
                report_path.stat().st_mtime_ns
            )

        except OSError:
            continue

        previous_time = previous_snapshot.get(
            resolved_path
        )

        if (
            previous_time is None
            or modified_time > previous_time
        ):
            changed_reports.append(
                report_path
            )

    if not changed_reports:
        return None

    return max(
        changed_reports,
        key=lambda path: path.stat().st_mtime_ns,
    )


def print_error_details(
    stdout_text,
    stderr_text,
):
    """Show useful error output without overwhelming the user."""

    combined_lines = []

    for text in (
        stdout_text,
        stderr_text,
    ):
        combined_lines.extend(
            line
            for line in text.splitlines()
            if line.strip()
        )

    if not combined_lines:
        return

    print()
    print("Technical details:")
    print("-" * 62)

    for line in combined_lines[-22:]:
        print(line)


def run_report_generator():
    """Run app.py using the current Python interpreter."""

    return subprocess.run(
        [
            sys.executable,
            str(APP_PATH),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def open_excel_report(
    report_path,
):
    """Open the generated Excel report in Windows."""

    try:
        os.startfile(
            str(
                report_path.resolve()
            )
        )

    except OSError as error:
        raise ValueError(
            "The report was created, but Windows "
            "could not open it automatically.\n\n"
            f"Open it manually here:\n{report_path}\n\n"
            f"Windows error: {error}"
        ) from error


def run_peakmetrics():
    """Validate the project, generate reports, and open Excel."""

    os.chdir(
        PROJECT_ROOT
    )

    print_heading(
        "PEAKMETRICS"
    )

    create_required_folders()

    if not APP_PATH.exists():
        raise ValueError(
            "app.py was not found in the main "
            "PeakMetrics project folder."
        )

    config = validate_config()
    fit_files = find_fit_files()

    if not fit_files:
        raise ValueError(
            "No FIT files were found.\n\n"
            "Place the current reporting week's "
            "FIT files inside the Weekly Runs folder."
        )

    print(
        f"Athlete:   {config['athlete_name']}"
    )
    print(
        f"Team:      {config['team']}"
    )
    print(
        f"Timezone:  {config['timezone']}"
    )
    print(
        f"FIT files: {len(fit_files)}"
    )

    print()
    print(
        "Generating the Excel and PDF reports..."
    )

    previous_reports = (
        snapshot_excel_reports()
    )

    result = run_report_generator()

    if result.returncode != 0:
        print_heading(
            "REPORT CREATION FAILED"
        )

        print(
            "PeakMetrics could not finish the report."
        )

        print_error_details(
            result.stdout,
            result.stderr,
        )

        return 1

    if result.stdout.strip():
        print()
        print(
            result.stdout.strip()
        )

    report_path = find_newest_generated_report(
        previous_reports
    )

    if report_path is None:
        print_heading(
            "REPORT NOT FOUND"
        )

        print(
            "PeakMetrics finished without reporting "
            "an error, but a new Excel file was not found."
        )

        return 1

    print_heading(
        "REPORT COMPLETE"
    )

    print(
        f"Opening: {report_path.name}"
    )

    open_excel_report(
        report_path
    )

    return 0


def main():
    """Run PeakMetrics with friendly error handling."""

    try:
        return run_peakmetrics()

    except Exception as error:
        print_heading(
            "STARTUP CHECK FAILED"
        )

        print(error)

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )