"""Update PeakMetrics PDF charts to use stacked daily mileage bars."""

import re
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PDF_REPORT_PATH = PROJECT_ROOT / "pdf_report.py"
BACKUP_PATH = PROJECT_ROOT / "pdf_report_before_stacked_mileage.py"

SHARED_IMPORT = (
    "from mileage_chart import "
    "create_daily_mileage_chart as "
    "create_stacked_daily_mileage_chart"
)

WRAPPER_FUNCTION = '''def create_daily_mileage_chart(
    daily_mileage,
    weekly_total,
):
    """Create the PDF version of the stacked mileage chart."""

    return create_stacked_daily_mileage_chart(
        daily_mileage,
        weekly_total,
        figsize=(11.2, 3.5),
        dpi=150,
        title_font_size=17,
        subtitle_font_size=9,
        total_font_size=10,
        axis_font_size=8,
        segment_font_size=9,
        total_label_font_size=9,
        pad_inches=0.08,
    )


'''


def add_shared_import(source):
    """Add the shared chart import once."""

    if SHARED_IMPORT in source:
        return source

    anchor = "from config import CONFIG\n"

    if anchor not in source:
        raise RuntimeError(
            "Could not find the config import in pdf_report.py."
        )

    return source.replace(
        anchor,
        f"{anchor}{SHARED_IMPORT}\n",
        1,
    )


def remove_old_chart_imports(source):
    """Remove imports used only by the old PDF chart function."""

    source = source.replace(
        "from io import BytesIO\n",
        "",
        1,
    )

    source = source.replace(
        "import matplotlib\n\n"
        "matplotlib.use(\"Agg\")\n\n"
        "import matplotlib.pyplot as plt\n"
        "import pandas as pd\n"
        "from matplotlib.ticker import MaxNLocator\n",
        "import pandas as pd\n",
        1,
    )

    return source


def replace_chart_function(source):
    """Replace the old PDF chart renderer with the shared renderer."""

    pattern = re.compile(
        r"^def create_daily_mileage_chart\([\s\S]*?"
        r"(?=^def build_summary_page\()",
        flags=re.MULTILINE,
    )

    updated_source, replacement_count = pattern.subn(
        WRAPPER_FUNCTION,
        source,
        count=1,
    )

    if replacement_count != 1:
        raise RuntimeError(
            "Could not locate the daily mileage chart function "
            "inside pdf_report.py."
        )

    return updated_source


def main():
    """Back up and update pdf_report.py."""

    if not PDF_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {PDF_REPORT_PATH.name}."
        )

    if not BACKUP_PATH.exists():
        shutil.copy2(
            PDF_REPORT_PATH,
            BACKUP_PATH,
        )

    source = PDF_REPORT_PATH.read_text(
        encoding="utf-8"
    )

    source = remove_old_chart_imports(
        source
    )

    source = add_shared_import(
        source
    )

    source = replace_chart_function(
        source
    )

    PDF_REPORT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print("Updated pdf_report.py successfully.")
    print(
        "Backup: "
        f"{BACKUP_PATH.name}"
    )


if __name__ == "__main__":
    main()
