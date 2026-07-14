"""Branded PeakMetrics PDF report generator."""

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator
from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
    TA_RIGHT,
)
from reportlab.lib.pagesizes import (
    landscape,
    letter,
)
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import CONFIG


# PeakMetrics brand palette.
PEAK_NAVY = "#12304A"
PEAK_TEAL = "#169C9C"
PEAK_AQUA = "#63D6D0"
PEAK_FILL = "#D9F3F1"

DARK_TEXT = "#102A43"
SECONDARY_TEXT = "#486581"
LIGHT_TEXT = "#829AB1"
GRID_COLOR = "#D9E2EC"

WHITE = "#FFFFFF"
CARD_BACKGROUND = "#F8FAFC"
ALTERNATE_ROW = "#F5FAFA"
WORKOUT_GOLD = "#D58B17"


RUN_TYPE_COLORS = {
    "Easy Run": "#169C9C",
    "Long Run": "#12304A",
    "Workout": "#D58B17",
    "Strides": "#7257A8",
    "Cross Training": "#2878B5",
    "Core": "#4B7F52",
    "Lifting": "#5B667A",
    "Other": "#6B7280",
}


PAGE_WIDTH, PAGE_HEIGHT = landscape(
    letter
)

LEFT_MARGIN = 0.45 * inch
RIGHT_MARGIN = 0.45 * inch
TOP_MARGIN = 0.42 * inch
BOTTOM_MARGIN = 0.42 * inch

USABLE_WIDTH = (
    PAGE_WIDTH
    - LEFT_MARGIN
    - RIGHT_MARGIN
)


def register_pdf_fonts():
    """Use Arial on Windows, with Helvetica as a fallback."""

    regular_name = "PeakMetricsArial"
    bold_name = "PeakMetricsArialBold"

    registered_fonts = set(
        pdfmetrics.getRegisteredFontNames()
    )

    if (
        regular_name in registered_fonts
        and bold_name in registered_fonts
    ):
        return regular_name, bold_name

    regular_path = Path(
        "C:/Windows/Fonts/arial.ttf"
    )

    bold_path = Path(
        "C:/Windows/Fonts/arialbd.ttf"
    )

    try:
        if (
            regular_path.exists()
            and bold_path.exists()
        ):
            pdfmetrics.registerFont(
                TTFont(
                    regular_name,
                    str(regular_path),
                )
            )

            pdfmetrics.registerFont(
                TTFont(
                    bold_name,
                    str(bold_path),
                )
            )

            return regular_name, bold_name

    except Exception:
        pass

    return (
        "Helvetica",
        "Helvetica-Bold",
    )


FONT_REGULAR, FONT_BOLD = (
    register_pdf_fonts()
)


def pdf_color(value):
    """Convert a hex color into a ReportLab color."""

    return colors.HexColor(
        value
    )


def build_output_path(output_path):
    """Return a unique output path without overwriting a PDF."""

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
            f"{path.stem}_{counter}"
            f"{path.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def safe_text(value):
    """Escape text before placing it in a Paragraph."""

    if value is None:
        return ""

    return escape(
        str(value)
    )


def is_missing(value):
    """Return True when a value is blank, None, or NaN."""

    if value is None:
        return True

    if isinstance(
        value,
        (
            list,
            tuple,
            dict,
        ),
    ):
        return False

    try:
        return bool(
            pd.isna(value)
        )

    except (
        TypeError,
        ValueError,
    ):
        return False


def text_value(value):
    """Return readable text for an optional value."""

    if is_missing(value):
        return "N/A"

    text = str(
        value
    ).strip()

    if not text:
        return "N/A"

    return text


def numeric_text(
    value,
    suffix="",
    decimals=0,
):
    """Format an optional numeric value."""

    if is_missing(value):
        return "N/A"

    try:
        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return text_value(
            value
        )

    if decimals == 0:
        number_text = (
            f"{number:,.0f}"
        )

    else:
        number_text = (
            f"{number:,.{decimals}f}"
        )

    if suffix:
        return (
            f"{number_text} "
            f"{suffix}"
        )

    return number_text


def pace_display(value):
    """Ensure a pace value displays its unit."""

    pace = text_value(
        value
    )

    if pace == "N/A":
        return pace

    if "/mi" in pace:
        return pace

    return f"{pace}/mi"


def format_week_range(
    start_value,
    end_value,
):
    """Create a polished reporting-week label."""

    try:
        start_date = datetime.fromisoformat(
            str(start_value)
        )

        end_date = datetime.fromisoformat(
            str(end_value)
        )

    except ValueError:
        return (
            f"{start_value} - "
            f"{end_value}"
        )

    if start_date.year != end_date.year:
        return (
            f"{start_date.strftime('%b')} "
            f"{start_date.day}, "
            f"{start_date.year} - "
            f"{end_date.strftime('%b')} "
            f"{end_date.day}, "
            f"{end_date.year}"
        )

    if start_date.month != end_date.month:
        return (
            f"{start_date.strftime('%b')} "
            f"{start_date.day} - "
            f"{end_date.strftime('%b')} "
            f"{end_date.day}, "
            f"{end_date.year}"
        )

    return (
        f"{start_date.strftime('%b')} "
        f"{start_date.day}-"
        f"{end_date.day}, "
        f"{end_date.year}"
    )


def activity_heading(run):
    """Create the activity date and time heading."""

    start_time = run.get(
        "Start Time"
    )

    if (
        start_time is not None
        and hasattr(
            start_time,
            "strftime",
        )
    ):
        date_text = (
            start_time.strftime(
                "%A, %B"
            )
        )

        time_text = (
            start_time.strftime(
                "%I:%M %p"
            )
            .lstrip("0")
        )

        return (
            f"{date_text} "
            f"{start_time.day} | "
            f"{time_text}"
        )

    date_value = run.get(
        "Date",
        ""
    )

    time_value = run.get(
        "Time of Day",
        ""
    )

    try:
        parsed_date = datetime.fromisoformat(
            str(date_value)
        )

        date_text = (
            f"{parsed_date.strftime('%A, %B')} "
            f"{parsed_date.day}"
        )

    except ValueError:
        date_text = str(
            date_value
        )

    if time_value:
        return (
            f"{date_text} | "
            f"{time_value}"
        )

    return date_text


def build_styles():
    """Create the PDF paragraph styles."""

    base_styles = (
        getSampleStyleSheet()
    )

    return {
        "title": ParagraphStyle(
            "PeakMetricsTitle",
            parent=base_styles["Title"],
            fontName=FONT_BOLD,
            fontSize=24,
            leading=27,
            textColor=pdf_color(
                PEAK_NAVY
            ),
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "PeakMetricsSubtitle",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=13,
            textColor=pdf_color(
                SECONDARY_TEXT
            ),
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "PeakMetricsSectionTitle",
            parent=base_styles["Heading2"],
            fontName=FONT_BOLD,
            fontSize=17,
            leading=20,
            textColor=pdf_color(
                PEAK_NAVY
            ),
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "info_label": ParagraphStyle(
            "PeakMetricsInfoLabel",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=7,
            leading=9,
            textColor=pdf_color(
                SECONDARY_TEXT
            ),
            alignment=TA_LEFT,
        ),
        "info_value": ParagraphStyle(
            "PeakMetricsInfoValue",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            leading=12,
            textColor=pdf_color(
                PEAK_NAVY
            ),
            alignment=TA_LEFT,
        ),
        "metric": ParagraphStyle(
            "PeakMetricsMetric",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=pdf_color(
                DARK_TEXT
            ),
            alignment=TA_CENTER,
        ),
        "activity_heading": ParagraphStyle(
            "PeakMetricsActivityHeading",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            leading=12,
            textColor=pdf_color(
                WHITE
            ),
            alignment=TA_LEFT,
        ),
        "activity_type": ParagraphStyle(
            "PeakMetricsActivityType",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=11,
            textColor=pdf_color(
                WHITE
            ),
            alignment=TA_RIGHT,
        ),
        "lap_title": ParagraphStyle(
            "PeakMetricsLapTitle",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            leading=12,
            textColor=pdf_color(
                PEAK_NAVY
            ),
            alignment=TA_LEFT,
        ),
        "lap_header": ParagraphStyle(
            "PeakMetricsLapHeader",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=pdf_color(
                SECONDARY_TEXT
            ),
            alignment=TA_CENTER,
        ),
        "lap_cell": ParagraphStyle(
            "PeakMetricsLapCell",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=10,
            textColor=pdf_color(
                DARK_TEXT
            ),
            alignment=TA_CENTER,
        ),
        "lap_cell_bold": ParagraphStyle(
            "PeakMetricsLapCellBold",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=pdf_color(
                DARK_TEXT
            ),
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "PeakMetricsNote",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=11,
            textColor=pdf_color(
                SECONDARY_TEXT
            ),
            alignment=TA_LEFT,
        ),
        "center_note": ParagraphStyle(
            "PeakMetricsCenterNote",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=11,
            textColor=pdf_color(
                SECONDARY_TEXT
            ),
            alignment=TA_CENTER,
        ),
    }


def build_info_card(
    label,
    value,
    width,
    styles,
):
    """Create an athlete/team/week information card."""

    table = Table(
        [
            [
                Paragraph(
                    safe_text(
                        label.upper()
                    ),
                    styles["info_label"],
                )
            ],
            [
                Paragraph(
                    safe_text(
                        value
                    ),
                    styles["info_value"],
                )
            ],
        ],
        colWidths=[
            width
        ],
        rowHeights=[
            0.18 * inch,
            0.34 * inch,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    pdf_color(
                        ALTERNATE_ROW
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    pdf_color(
                        GRID_COLOR
                    ),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    return table


def metric_cell(
    value,
    label,
    styles,
):
    """Create one value-and-label metric cell."""

    content = (
        f"<font name='{FONT_BOLD}' "
        f"size='12' color='{PEAK_NAVY}'>"
        f"{safe_text(value)}"
        f"</font>"
        f"<br/>"
        f"<font name='{FONT_REGULAR}' "
        f"size='7' color='{SECONDARY_TEXT}'>"
        f"{safe_text(label.upper())}"
        f"</font>"
    )

    return Paragraph(
        content,
        styles["metric"],
    )


def build_metric_grid(
    summary,
    styles,
):
    """Create the eight-card weekly summary grid."""

    metrics = [
        (
            f"{summary.mileage:.1f} mi",
            "Weekly Mileage",
        ),
        (
            summary.weekly_time,
            "Weekly Time",
        ),
        (
            pace_display(
                summary.average_pace
            ),
            "Average Pace",
        ),
        (
            str(
                summary.runs
            ),
            "Runs",
        ),
        (
            f"{summary.average_hr} bpm",
            "Average Heart Rate",
        ),
        (
            f"{summary.max_hr} bpm",
            "Maximum Heart Rate",
        ),
        (
            f"{summary.average_power} W",
            "Average Power",
        ),
        (
            f"{summary.elevation_gain:,} ft",
            "Elevation Gain",
        ),
    ]

    rows = []

    for start_index in (
        0,
        4,
    ):
        rows.append(
            [
                metric_cell(
                    value,
                    label,
                    styles,
                )
                for value, label
                in metrics[
                    start_index:
                    start_index + 4
                ]
            ]
        )

    table = Table(
        rows,
        colWidths=[
            USABLE_WIDTH / 4
        ]
        * 4,
        rowHeights=[
            0.66 * inch,
            0.66 * inch,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    pdf_color(
                        CARD_BACKGROUND
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    pdf_color(
                        GRID_COLOR
                    ),
                ),
                (
                    "LINEABOVE",
                    (0, 0),
                    (-1, 0),
                    2,
                    pdf_color(
                        PEAK_TEAL
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def format_day_label(value):
    """Create a weekday and date label for the chart."""

    try:
        activity_date = datetime.fromisoformat(
            str(value)
        )

        return (
            f"{activity_date.strftime('%a')}\n"
            f"{activity_date.month}/"
            f"{activity_date.day}"
        )

    except ValueError:
        return str(
            value
        )


def create_daily_mileage_chart(
    daily_mileage,
    weekly_total,
):
    """Create the branded PDF daily-mileage chart."""

    day_labels = [
        format_day_label(
            value
        )
        for value
        in daily_mileage["Date"]
    ]

    mileage_values = [
        float(
            value
        )
        for value
        in daily_mileage["Miles"]
    ]

    x_positions = list(
        range(
            len(mileage_values)
        )
    )

    figure, axis = plt.subplots(
        figsize=(
            11.2,
            3.5,
        ),
        dpi=150,
    )

    figure.patch.set_facecolor(
        "white"
    )

    axis.set_facecolor(
        "white"
    )

    figure.subplots_adjust(
        left=0.055,
        right=0.985,
        top=0.75,
        bottom=0.23,
    )

    maximum_mileage = max(
        mileage_values
    )

    chart_ceiling = max(
        5,
        maximum_mileage * 1.28,
    )

    axis.set_ylim(
        0,
        chart_ceiling,
    )

    axis.set_axisbelow(
        True
    )

    axis.yaxis.set_major_locator(
        MaxNLocator(
            nbins=4,
            integer=True,
        )
    )

    axis.grid(
        axis="y",
        color=GRID_COLOR,
        linewidth=0.8,
    )

    axis.grid(
        axis="x",
        visible=False,
    )

    for spine in axis.spines.values():
        spine.set_visible(
            False
        )

    axis.axhline(
        0,
        color="#BCCCDC",
        linewidth=1.1,
    )

    bar_colors = [
        PEAK_TEAL
        for _ in mileage_values
    ]

    if bar_colors:
        bar_colors[-1] = (
            PEAK_AQUA
        )

    bars = axis.bar(
        x_positions,
        mileage_values,
        width=0.56,
        color=bar_colors,
        edgecolor="none",
        zorder=3,
    )

    if len(mileage_values) == 1:
        axis.set_xlim(
            -0.8,
            0.8,
        )

    else:
        axis.set_xlim(
            -0.65,
            len(mileage_values) - 0.35,
        )

    axis.set_xticks(
        x_positions
    )

    axis.set_xticklabels(
        day_labels
    )

    axis.tick_params(
        axis="x",
        length=0,
        pad=10,
        labelsize=9,
        colors=SECONDARY_TEXT,
    )

    axis.tick_params(
        axis="y",
        length=0,
        pad=7,
        labelsize=8,
        colors=LIGHT_TEXT,
    )

    axis.set_ylabel(
        "Miles",
        fontsize=8,
        color=SECONDARY_TEXT,
        labelpad=8,
    )

    axis.set_title(
        "Daily Mileage",
        loc="left",
        fontsize=17,
        fontweight="bold",
        color=PEAK_NAVY,
        pad=22,
    )

    axis.text(
        0,
        1.02,
        "Mileage by training day - doubles combined",
        transform=axis.transAxes,
        horizontalalignment="left",
        verticalalignment="bottom",
        fontsize=9,
        color=SECONDARY_TEXT,
    )

    axis.text(
        1,
        1.02,
        (
            f"Week total: "
            f"{weekly_total:.1f} mi"
        ),
        transform=axis.transAxes,
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=10,
        fontweight="bold",
        color=PEAK_TEAL,
    )

    for bar, mileage in zip(
        bars,
        mileage_values,
    ):
        axis.annotate(
            f"{mileage:.1f}",
            (
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
            ),
            xytext=(
                0,
                6,
            ),
            textcoords="offset points",
            horizontalalignment="center",
            verticalalignment="bottom",
            fontsize=9,
            fontweight="bold",
            color=PEAK_NAVY,
            clip_on=False,
        )

    image_buffer = BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        bbox_inches="tight",
        pad_inches=0.08,
        facecolor="white",
    )

    plt.close(
        figure
    )

    image_buffer.seek(
        0
    )

    return image_buffer


def build_summary_page(
    df,
    summary,
    daily_mileage,
    styles,
):
    """Build the first-page weekly dashboard."""

    dates = sorted(
        str(
            value
        )
        for value
        in df["Date"]
    )

    week_display = format_week_range(
        dates[0],
        dates[-1],
    )

    story = [
        Paragraph(
            "PeakMetrics",
            styles["title"],
        ),
        Paragraph(
            "Weekly Training Report",
            styles["subtitle"],
        ),
        Spacer(
            1,
            0.08 * inch,
        ),
    ]

    accent_bar = Table(
        [[""]],
        colWidths=[
            USABLE_WIDTH
        ],
        rowHeights=[
            0.055 * inch
        ],
    )

    accent_bar.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    pdf_color(
                        PEAK_TEAL
                    ),
                ),
            ]
        )
    )

    story.extend(
        [
            accent_bar,
            Spacer(
                1,
                0.12 * inch,
            ),
        ]
    )

    info_widths = [
        3.15 * inch,
        3.15 * inch,
        USABLE_WIDTH
        - 6.30 * inch,
    ]

    info_table = Table(
        [
            [
                build_info_card(
                    "Athlete",
                    CONFIG.athlete_name,
                    info_widths[0],
                    styles,
                ),
                build_info_card(
                    "Team",
                    CONFIG.team,
                    info_widths[1],
                    styles,
                ),
                build_info_card(
                    "Reporting Week",
                    week_display,
                    info_widths[2],
                    styles,
                ),
            ]
        ],
        colWidths=info_widths,
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.extend(
        [
            info_table,
            Spacer(
                1,
                0.15 * inch,
            ),
            build_metric_grid(
                summary,
                styles,
            ),
            Spacer(
                1,
                0.12 * inch,
            ),
        ]
    )

    if daily_mileage.empty:
        story.append(
            Paragraph(
                "No running mileage was found "
                "for this reporting period.",
                styles["center_note"],
            )
        )

    else:
        chart_buffer = (
            create_daily_mileage_chart(
                daily_mileage,
                summary.mileage,
            )
        )

        chart_image = Image(
            chart_buffer,
            width=USABLE_WIDTH,
            height=3.05 * inch,
        )

        chart_image._peakmetrics_buffer = (
            chart_buffer
        )

        story.append(
            chart_image
        )

    story.extend(
        [
            Spacer(
                1,
                0.07 * inch,
            ),
            Paragraph(
                "Strides are displayed in the activity "
                "section but are excluded from all weekly, "
                "year-to-date, and historical totals.",
                styles["note"],
            ),
        ]
    )

    return story


def build_activity_header(
    run,
    styles,
    continued=False,
):
    """Create the colored header for an activity card."""

    run_type = text_value(
        run.get(
            "Run Type",
            "Other",
        )
    )

    accent_color = (
        RUN_TYPE_COLORS.get(
            run_type,
            RUN_TYPE_COLORS[
                "Other"
            ],
        )
    )

    heading = activity_heading(
        run
    )

    if continued:
        heading = (
            f"{heading} - continued"
        )

    header = Table(
        [
            [
                Paragraph(
                    safe_text(
                        heading
                    ),
                    styles[
                        "activity_heading"
                    ],
                ),
                Paragraph(
                    safe_text(
                        run_type
                    ),
                    styles[
                        "activity_type"
                    ],
                ),
            ]
        ],
        colWidths=[
            7.25 * inch,
            USABLE_WIDTH
            - 7.25 * inch,
        ],
        rowHeights=[
            0.34 * inch
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    pdf_color(
                        accent_color
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, 0),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (1, 0),
                    (1, 0),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return header


def build_activity_metrics(
    run,
    styles,
):
    """Create the two-row activity metric grid."""

    metrics = [
        (
            numeric_text(
                run.get(
                    "Miles"
                ),
                "mi",
                decimals=2,
            ),
            "Distance",
        ),
        (
            text_value(
                run.get(
                    "Time"
                )
            ),
            "Time",
        ),
        (
            pace_display(
                run.get(
                    "Pace (/mi)"
                )
            ),
            "Average Pace",
        ),
        (
            numeric_text(
                run.get(
                    "Avg HR"
                ),
                "bpm",
            ),
            "Average HR",
        ),
        (
            numeric_text(
                run.get(
                    "Elevation (ft)"
                ),
                "ft",
            ),
            "Elevation Gain",
        ),
        (
            numeric_text(
                run.get(
                    "Power (W)"
                ),
                "W",
            ),
            "Average Power",
        ),
        (
            numeric_text(
                run.get(
                    "Max HR"
                ),
                "bpm",
            ),
            "Maximum HR",
        ),
        (
            numeric_text(
                run.get(
                    "Cadence (spm)"
                ),
                "spm",
            ),
            "Cadence",
        ),
    ]

    rows = []

    for start_index in (
        0,
        4,
    ):
        rows.append(
            [
                metric_cell(
                    value,
                    label,
                    styles,
                )
                for value, label
                in metrics[
                    start_index:
                    start_index + 4
                ]
            ]
        )

    table = Table(
        rows,
        colWidths=[
            USABLE_WIDTH / 4
        ]
        * 4,
        rowHeights=[
            0.58 * inch,
            0.58 * inch,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    pdf_color(
                        CARD_BACKGROUND
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.55,
                    pdf_color(
                        GRID_COLOR
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def build_lap_table(
    laps,
    styles,
):
    """Create the branded lap-splits table."""

    header_row = [
        Paragraph(
            "Lap",
            styles["lap_header"],
        ),
        Paragraph(
            "Distance",
            styles["lap_header"],
        ),
        Paragraph(
            "Pace",
            styles["lap_header"],
        ),
        Paragraph(
            "Time",
            styles["lap_header"],
        ),
        Paragraph(
            "Avg HR",
            styles["lap_header"],
        ),
    ]

    rows = [
        header_row
    ]

    for index, lap in enumerate(
        laps,
        start=1,
    ):
        lap_number = lap.get(
            "Lap",
            index,
        )

        rows.append(
            [
                Paragraph(
                    safe_text(
                        lap_number
                    ),
                    styles[
                        "lap_cell_bold"
                    ],
                ),
                Paragraph(
                    safe_text(
                        numeric_text(
                            lap.get(
                                "Miles"
                            ),
                            "mi",
                            decimals=2,
                        )
                    ),
                    styles["lap_cell"],
                ),
                Paragraph(
                    safe_text(
                        pace_display(
                            lap.get(
                                "Pace"
                            )
                        )
                    ),
                    styles["lap_cell"],
                ),
                Paragraph(
                    safe_text(
                        text_value(
                            lap.get(
                                "Time"
                            )
                        )
                    ),
                    styles["lap_cell"],
                ),
                Paragraph(
                    safe_text(
                        numeric_text(
                            lap.get(
                                "Avg HR"
                            ),
                            "bpm",
                        )
                    ),
                    styles["lap_cell"],
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            0.65 * inch,
            2.15 * inch,
            2.20 * inch,
            2.20 * inch,
            USABLE_WIDTH
            - 7.20 * inch,
        ],
        repeatRows=1,
    )

    style_commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            pdf_color(
                PEAK_FILL
            ),
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            pdf_color(
                GRID_COLOR
            ),
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    for row_number in range(
        1,
        len(rows),
    ):
        if row_number % 2 == 0:
            style_commands.append(
                (
                    "BACKGROUND",
                    (
                        0,
                        row_number,
                    ),
                    (
                        -1,
                        row_number,
                    ),
                    pdf_color(
                        ALTERNATE_ROW
                    ),
                )
            )

    table.setStyle(
        TableStyle(
            style_commands
        )
    )

    return table


def build_activity_card(
    run,
    styles,
    laps,
    continued=False,
):
    """Build one activity card or continuation card."""

    parts = [
        build_activity_header(
            run,
            styles,
            continued=continued,
        ),
        Spacer(
            1,
            0.05 * inch,
        ),
    ]

    if not continued:
        parts.extend(
            [
                build_activity_metrics(
                    run,
                    styles,
                ),
                Spacer(
                    1,
                    0.06 * inch,
                ),
            ]
        )

        if (
            text_value(
                run.get(
                    "Run Type"
                )
            )
            == "Strides"
        ):
            stride_note = Table(
                [
                    [
                        Paragraph(
                            "This Strides activity is "
                            "shown separately and excluded "
                            "from every report total.",
                            styles["note"],
                        )
                    ]
                ],
                colWidths=[
                    USABLE_WIDTH
                ],
            )

            stride_note.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            pdf_color(
                                "#F1ECF8"
                            ),
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            pdf_color(
                                "#D9CFEA"
                            ),
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            parts.extend(
                [
                    stride_note,
                    Spacer(
                        1,
                        0.06 * inch,
                    ),
                ]
            )

    lap_title = (
        "Lap Splits Continued"
        if continued
        else "Lap Splits"
    )

    parts.append(
        Paragraph(
            lap_title,
            styles["lap_title"],
        )
    )

    parts.append(
        Spacer(
            1,
            0.035 * inch,
        )
    )

    if laps:
        parts.append(
            build_lap_table(
                laps,
                styles,
            )
        )

    else:
        no_laps_table = Table(
            [
                [
                    Paragraph(
                        "No lap data available",
                        styles[
                            "center_note"
                        ],
                    )
                ]
            ],
            colWidths=[
                USABLE_WIDTH
            ],
            rowHeights=[
                0.45 * inch
            ],
        )

        no_laps_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        pdf_color(
                            CARD_BACKGROUND
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        pdf_color(
                            GRID_COLOR
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
            )
        )

        parts.append(
            no_laps_table
        )

    return KeepTogether(
        parts
    )


def build_activity_pages(
    df,
    styles,
):
    """Build all activity-card pages."""

    story = [
        PageBreak(),
        Paragraph(
            "Activity Details",
            styles["section_title"],
        ),
        Paragraph(
            "Activities are listed chronologically. "
            "Activity-type corrections remain editable "
            "in the Excel report.",
            styles["note"],
        ),
        Spacer(
            1,
            0.12 * inch,
        ),
    ]

    for run in df.to_dict(
        "records"
    ):
        laps = run.get(
            "Laps"
        ) or []

        first_chunk = laps[
            :18
        ]

        story.extend(
            [
                CondPageBreak(
                    3.1 * inch
                ),
                build_activity_card(
                    run,
                    styles,
                    first_chunk,
                    continued=False,
                ),
                Spacer(
                    1,
                    0.18 * inch,
                ),
            ]
        )

        remaining_laps = laps[
            18:
        ]

        chunk_size = 24

        for chunk_start in range(
            0,
            len(
                remaining_laps
            ),
            chunk_size,
        ):
            chunk = remaining_laps[
                chunk_start:
                chunk_start + chunk_size
            ]

            story.extend(
                [
                    PageBreak(),
                    build_activity_card(
                        run,
                        styles,
                        chunk,
                        continued=True,
                    ),
                    Spacer(
                        1,
                        0.18 * inch,
                    ),
                ]
            )

    return story


def draw_page_footer(
    canvas,
    document,
):
    """Draw the branded footer and page number."""

    canvas.saveState()

    canvas.setStrokeColor(
        pdf_color(
            GRID_COLOR
        )
    )

    canvas.setLineWidth(
        0.5
    )

    canvas.line(
        document.leftMargin,
        0.30 * inch,
        PAGE_WIDTH
        - document.rightMargin,
        0.30 * inch,
    )

    canvas.setFont(
        FONT_REGULAR,
        8,
    )

    canvas.setFillColor(
        pdf_color(
            SECONDARY_TEXT
        )
    )

    canvas.drawString(
        document.leftMargin,
        0.15 * inch,
        (
            f"PeakMetrics | "
            f"{CONFIG.athlete_name}"
        ),
    )

    canvas.drawRightString(
        PAGE_WIDTH
        - document.rightMargin,
        0.15 * inch,
        (
            f"Page "
            f"{canvas.getPageNumber()}"
        ),
    )

    canvas.restoreState()


def create_pdf_report(
    df,
    summary,
    daily_mileage,
    output_path,
):
    """Create the complete branded PeakMetrics PDF."""

    output_path = build_output_path(
        output_path
    )

    document = SimpleDocTemplate(
        str(
            output_path
        ),
        pagesize=landscape(
            letter
        ),
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=(
            "PeakMetrics Weekly "
            "Training Report"
        ),
        author=CONFIG.athlete_name,
        subject=(
            "Weekly running summary "
            "and activity details"
        ),
    )

    styles = build_styles()

    story = []

    story.extend(
        build_summary_page(
            df,
            summary,
            daily_mileage,
            styles,
        )
    )

    story.extend(
        build_activity_pages(
            df,
            styles,
        )
    )

    document.build(
        story,
        onFirstPage=draw_page_footer,
        onLaterPages=draw_page_footer,
    )

    return output_path