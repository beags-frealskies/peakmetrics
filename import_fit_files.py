"""Select weekly FIT files, archive the old week, and run PeakMetrics."""

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import Tk, filedialog, messagebox


PROJECT_ROOT = Path(__file__).resolve().parent

WEEKLY_RUNS_FOLDER = PROJECT_ROOT / "Weekly Runs"
DATA_FOLDER = PROJECT_ROOT / "Data"
ARCHIVE_FOLDER = DATA_FOLDER / "FIT Archive"

IMPORT_SETTINGS_PATH = (
    DATA_FOLDER / "import_settings.json"
)

LAUNCHER_PATH = (
    PROJECT_ROOT / "launch_peakmetrics.py"
)


def create_required_folders():
    """Create folders used by the importer."""

    for folder in (
        WEEKLY_RUNS_FOLDER,
        DATA_FOLDER,
        ARCHIVE_FOLDER,
    ):
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


def load_last_import_folder():
    """Return the most recently used FIT-file folder."""

    if IMPORT_SETTINGS_PATH.exists():
        try:
            with IMPORT_SETTINGS_PATH.open(
                "r",
                encoding="utf-8-sig",
            ) as settings_file:
                settings = json.load(
                    settings_file
                )

            saved_folder = Path(
                settings.get(
                    "last_import_folder",
                    "",
                )
            )

            if saved_folder.exists():
                return saved_folder

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
        ):
            pass

    possible_folders = [
        Path.home() / "Downloads",
        Path.home() / "OneDrive" / "Downloads",
        Path.home() / "Desktop",
        PROJECT_ROOT,
    ]

    for folder in possible_folders:
        if folder.exists():
            return folder

    return PROJECT_ROOT


def save_last_import_folder(folder):
    """Remember where FIT files were last selected."""

    DATA_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings = {
        "last_import_folder": str(
            Path(folder).resolve()
        )
    }

    with IMPORT_SETTINGS_PATH.open(
        "w",
        encoding="utf-8",
    ) as settings_file:
        json.dump(
            settings,
            settings_file,
            indent=2,
        )


def choose_fit_files():
    """Open a Windows file picker for FIT files."""

    starting_folder = (
        load_last_import_folder()
    )

    window = Tk()
    window.withdraw()
    window.attributes(
        "-topmost",
        True,
    )

    selected_files = filedialog.askopenfilenames(
        parent=window,
        title="Select this week's FIT files",
        initialdir=str(starting_folder),
        filetypes=[
            (
                "FIT activity files",
                "*.fit",
            ),
            (
                "All files",
                "*.*",
            ),
        ],
    )

    window.destroy()

    fit_files = [
        Path(file_path)
        for file_path in selected_files
        if Path(file_path).suffix.lower()
        == ".fit"
    ]

    if fit_files:
        save_last_import_folder(
            fit_files[0].parent
        )

    return fit_files


def unique_destination(
    folder,
    filename,
):
    """Return a destination that will not overwrite a file."""

    destination = folder / filename

    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 2

    while True:
        candidate = folder / (
            f"{stem}_{counter}{suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def stage_selected_files(
    selected_files,
    staging_folder,
):
    """Copy selected files into temporary storage."""

    staged_files = []

    for source_file in selected_files:
        destination = unique_destination(
            staging_folder,
            source_file.name,
        )

        shutil.copy2(
            source_file,
            destination,
        )

        staged_files.append(
            destination
        )

    return staged_files


def archive_current_week():
    """Archive FIT files currently in Weekly Runs."""

    current_files = sorted(
        WEEKLY_RUNS_FOLDER.glob("*.fit")
    )

    if not current_files:
        return None, 0

    archive_name = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    week_archive = (
        ARCHIVE_FOLDER / archive_name
    )

    week_archive.mkdir(
        parents=True,
        exist_ok=False,
    )

    for current_file in current_files:
        destination = unique_destination(
            week_archive,
            current_file.name,
        )

        shutil.move(
            str(current_file),
            str(destination),
        )

    return week_archive, len(current_files)


def install_new_week(
    staged_files,
):
    """Copy the selected FIT files into Weekly Runs."""

    installed_files = []

    for staged_file in staged_files:
        destination = unique_destination(
            WEEKLY_RUNS_FOLDER,
            staged_file.name,
        )

        shutil.copy2(
            staged_file,
            destination,
        )

        installed_files.append(
            destination
        )

    return installed_files


def run_peakmetrics():
    """Run the normal PeakMetrics launcher."""

    if not LAUNCHER_PATH.exists():
        raise FileNotFoundError(
            "launch_peakmetrics.py was not found."
        )

    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER_PATH),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    return result.returncode


def show_message(
    title,
    message,
    error=False,
):
    """Show a Windows message box."""

    window = Tk()
    window.withdraw()
    window.attributes(
        "-topmost",
        True,
    )

    if error:
        messagebox.showerror(
            title,
            message,
            parent=window,
        )
    else:
        messagebox.showinfo(
            title,
            message,
            parent=window,
        )

    window.destroy()


def main():
    """Import a new week and generate its report."""

    create_required_folders()

    selected_files = choose_fit_files()

    if not selected_files:
        print(
            "No FIT files were selected."
        )
        return 0

    try:
        with tempfile.TemporaryDirectory() as temp_directory:
            staging_folder = Path(
                temp_directory
            )

            staged_files = stage_selected_files(
                selected_files,
                staging_folder,
            )

            archive_path, archived_count = (
                archive_current_week()
            )

            installed_files = install_new_week(
                staged_files
            )

        print()
        print(
            f"Imported {len(installed_files)} "
            "FIT file(s)."
        )

        if archive_path is not None:
            print(
                f"Archived {archived_count} "
                "old FIT file(s) to:"
            )
            print(
                archive_path
            )

        print()
        print(
            "Starting PeakMetrics..."
        )

        return run_peakmetrics()

    except Exception as error:
        show_message(
            "PeakMetrics Import Failed",
            str(error),
            error=True,
        )

        print(
            f"Import failed: {error}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )