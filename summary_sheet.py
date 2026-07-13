"""PeakMetrics Excel summary dashboard."""

from datetime import datetime
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

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

CARD_FILL = PatternFill(
    fill_type="solid",
    fgColor="F8FAFC",
)

INFO_FILL = PatternFill(
    fill_type="solid",
    fgColor="F5FAFA",
)

ACCENT_FILL = PatternFill(
    fill_type="solid",
    fgColor="169C9C",
)

THIN_GRAY = Side(
    style="thin",
    color="D9E2EC",
)

TEAL_TOP = Side(
    style="medium",
    color="169C9C",
)

CARD_BORDER = Border(
    left=THIN_GRAY,
    right=THIN_GRAY,
    top=TEAL_TOP,
    bottom=THIN_GRAY,
)

INFO_BORDER = Border(
    left=THIN_GRAY,
    right=THIN_GRAY,
    top=THIN_GRAY,
    bottom=THIN_GRAY,
)


def format_week_range(
    start_value,
    end_value,
):
    """Create a clean display date range."""

    try:
        start_date = datetime.fromisoformat(
            str(start_value)
        )

        end_date = datetime.fromisoformat(
            str(end_value)
        )

    except ValueError:
        return (
            f"{start_value} – {end_value}"
        )

    if start_date.year != end_date.year:
        return (
            f"{start_date.strftime('%b')} "
            f"{start_date.day}, "
            f"{start_date.year} – "
            f"{end_date.strftime('%b')} "
            f"{end_date.day}, "
            f"{end_date.year}"
        )

    if start_date.month != end_date.month:
        return (
            f"{start_date.strftime('%b')} "
            f"{start_date.day} – "
            f"{end_date.strftime('%b')} "
            f"{end_date.day}, "
            f"{end_date.year}"
        )

    return (
        f"{start_date.strftime('%b')} "
        f"{start_date.day}–"
        f"{end_date.day}, "
        f"{end_date.year}"
    )


def pace_display(value):
    """Ensure pace values show their unit."""

    value = str(value)

    if value == "N/A":
        return value

    if "/mi" in value:
        return value

    return f"{value}/mi"


def draw_info_card(
    ws,
    start_column,
    end_column,
    label,
    value,
):
    """Draw one athlete-information card."""

    ws.merge_cells(
        start_row=4,
        start_column=start_column,
        end_row=4,
        end_column=end_column,
    )

    ws.merge_cells(
        start_row=5,
        start_column=start_column,
        end_row=6,
        end_column=end_column,
    )

    label_cell = ws.cell(
        row=4,
        column=start_column,
    )

    label_cell.value = label.upper()
    label_cell.font = Font(
        size=8,
        bold=True,
        color=SECONDARY_TEXT.replace(
            "#",
            "",
        ),
    )
    label_cell.alignment = Alignment(
        horizontal="left",
        vertical="center",
    )

    value_cell = ws.cell(
        row=5,
        column=start_column,
    )

    value_cell.value = value
    value_cell.font = Font(
        size=12,
        bold=True,
        color=PEAK_NAVY.replace(
            "#",
            "",
        ),
    )
    value_cell.alignment = Alignment(
        horizontal="left",
        vertical="center",
        wrap_text=True,
    )

    for row_number in range(
        4,
        7,
    ):
        for column_number in range(
            start_column,
            end_column + 1,
        ):
            cell = ws.cell(
                row=row_number,
                column=column_number,
            )

            cell.fill = INFO_FILL
            cell.border = INFO_BORDER


def draw_metric_card(
    ws,
    start_row,
    start_column,
    value,
    label,
):
    """Draw one dashboard metric card."""

    end_column = start_column + 3
    end_row = start_row + 3

    ws.merge_cells(
        start_row=start_row,
        start_column=start_column,
        end_row=start_row + 1,
        end_column=end_column,
    )

    ws.merge_cells(
        start_row=start_row + 2,
        start_column=start_column,
        end_row=end_row,
        end_column=end_column,
    )

    value_cell = ws.cell(
        row=start_row,
        column=start_column,
    )

    value_cell.value = value
    value_cell.font = Font(
        size=18,
        bold=True,
        color=PEAK_NAVY.replace(
            "#",
            "",
        ),
    )
    value_cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
        wrap_text=True,
    )

    label_cell = ws.cell(
        row=start_row + 2,
        column=start_column,
    )

    label_cell.value = label
    label_cell.font = Font(
        size=9,
        color=SECONDARY_TEXT.replace(
            "#",
            "",
        ),
    )
    label_cell.alignment = Alignment(
        horizontal="center",
        vertical="center",
        wrap_text=True,
    )

    for row_number in range(
        start_row,
        end_row + 1,
    ):
        for column_number in range(
            start_column,
            end_column + 1,
        ):
            cell = ws.cell(
                row=row_number,
                column=column_number,
            )

            cell.fill = CARD_FILL
            cell.border = CARD_BORDER


def format_day_label(value):
    """Create labels such as Mon and 6/29."""

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
        return str(value)


def create_daily_mileage_chart(
    daily_mileage,
    weekly_total,
):
    """Create the branded daily-mileage bar chart."""

    day_labels = [
        format_day_label(value)
        for value in daily_mileage["Date"]
    ]

    mileage_values = [
        float(value)
        for value in daily_mileage["Miles"]
    ]

    x_positions = list(
        range(len(mileage_values))
    )

    figure, axis = plt.subplots(
        figsize=(12.8, 4.35),
        dpi=140,
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
        top=0.76,
        bottom=0.22,
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

    axis.set_axisbelow(True)

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
        spine.set_visible(False)

    axis.axhline(
        0,
        color="#BCCCDC",
        linewidth=1.1,
    )

    bar_colors = [
        PEAK_TEAL
        for _ in mileage_values
    ]

    # Highlight the most recent training day.
    if bar_colors:
        bar_colors[-1] = PEAK_AQUA

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
        pad=12,
        labelsize=9,
        colors=SECONDARY_TEXT,
    )

    axis.tick_params(
        axis="y",
        length=0,
        pad=8,
        labelsize=9,
        colors=LIGHT_TEXT,
    )

    axis.set_ylabel(
        "Miles",
        fontsize=9,
        color=SECONDARY_TEXT,
        labelpad=10,
    )

    axis.set_title(
        "Daily Mileage",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color=PEAK_NAVY,
        pad=24,
    )

    axis.text(
        0,
        1.02,
        "Mileage by training day • doubles combined",
        transform=axis.transAxes,
        horizontalalignment="left",
        verticalalignment="bottom",
        fontsize=10,
        color=SECONDARY_TEXT,
    )

    axis.text(
        1,
        1.02,
        f"Week total: {weekly_total:.1f} mi",
        transform=axis.transAxes,
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=11,
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
                7,
            ),
            textcoords="offset points",
            horizontalalignment="center",
            verticalalignment="bottom",
            fontsize=10,
            fontweight="bold",
            color=PEAK_NAVY,
            clip_on=False,
        )

    image_buffer = BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        bbox_inches="tight",
        pad_inches=0.12,
        facecolor="white",
    )

    plt.close(
        figure
    )

    image_buffer.seek(0)

    return image_buffer


def create_summary_sheet(
    wb,
    df,
    summary,
    daily_mileage,
):
    """Create the complete Summary dashboard."""

    ws = wb.active
    ws.title = "Summary"

    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 90
    ws.freeze_panes = None
    ws.sheet_properties.tabColor = "169C9C"

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    ws.merge_cells(
        "A1:P1"
    )

    ws["A1"] = "PeakMetrics"
    ws["A1"].font = Font(
        size=26,
        bold=True,
        color="12304A",
    )
    ws["A1"].alignment = Alignment(
        vertical="center",
    )

    ws.row_dimensions[1].height = 35

    ws.merge_cells(
        "A2:P2"
    )

    ws["A2"] = "Weekly Training Overview"
    ws["A2"].font = Font(
        size=12,
        color="486581",
    )

    ws["A2"].alignment = Alignment(
        vertical="center",
    )

    ws.merge_cells(
        "A3:P3"
    )

    ws["A3"].fill = ACCENT_FILL
    ws.row_dimensions[3].height = 4

    dates = sorted(
        str(value)
        for value in df["Date"]
    )

    week_display = format_week_range(
        dates[0],
        dates[-1],
    )

    draw_info_card(
        ws,
        1,
        5,
        "Athlete",
        CONFIG.athlete_name,
    )

    draw_info_card(
        ws,
        6,
        10,
        "Team",
        CONFIG.team,
    )

    draw_info_card(
        ws,
        11,
        16,
        "Reporting Week",
        week_display,
    )

    # Primary weekly metrics.
    draw_metric_card(
        ws,
        8,
        1,
        f"{summary.mileage:.1f} mi",
        "Weekly Mileage",
    )

    draw_metric_card(
        ws,
        8,
        5,
        summary.weekly_time,
        "Weekly Time",
    )

    draw_metric_card(
        ws,
        8,
        9,
        pace_display(
            summary.average_pace
        ),
        "Average Pace",
    )

    draw_metric_card(
        ws,
        8,
        13,
        summary.runs,
        "Runs",
    )

    # Supporting weekly metrics.
    draw_metric_card(
        ws,
        13,
        1,
        f"{summary.average_hr} bpm",
        "Average Heart Rate",
    )

    draw_metric_card(
        ws,
        13,
        5,
        f"{summary.max_hr} bpm",
        "Maximum Heart Rate",
    )

    draw_metric_card(
        ws,
        13,
        9,
        f"{summary.average_power} W",
        "Average Power",
    )

    draw_metric_card(
        ws,
        13,
        13,
        f"{summary.elevation_gain:,} ft",
        "Elevation Gain",
    )

    if daily_mileage.empty:
        ws.merge_cells(
            "A20:P23"
        )

        ws["A20"] = (
            "No running mileage was found "
            "for this reporting period."
        )

        ws["A20"].font = Font(
            size=12,
            italic=True,
            color="486581",
        )

        ws["A20"].alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    else:
        chart_buffer = (
            create_daily_mileage_chart(
                daily_mileage,
                summary.mileage,
            )
        )

        chart_image = ExcelImage(
            chart_buffer
        )

        # Keep the image buffer alive until
        # the workbook finishes saving.
        chart_image._peakmetrics_buffer = (
            chart_buffer
        )

        chart_image.width = 1120
        chart_image.height = 385

        ws.add_image(
            chart_image,
            "A19",
        )

    for row_number in range(
        19,
        40,
    ):
        ws.row_dimensions[
            row_number
        ].height = 18

    for column_number in range(
        1,
        17,
    ):
        column_letter = get_column_letter(
            column_number
        )

        ws.column_dimensions[
            column_letter
        ].width = 9.5

    ws.sheet_view.selection[0].activeCell = "A1"
    ws.sheet_view.selection[0].sqref = "A1"