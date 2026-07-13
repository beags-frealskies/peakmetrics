"""PDF report generation for PeakMetrics."""

from datetime import datetime
from html import escape
import math
from pathlib import Path
from config import CONFIG

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_SIZE = landscape(letter)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

LEFT_MARGIN = 30
RIGHT_MARGIN = 30
TOP_MARGIN = 30
BOTTOM_MARGIN = 28

AVAILABLE_WIDTH = (
    PAGE_WIDTH
    - LEFT_MARGIN
    - RIGHT_MARGIN
)


RUN_TYPE_STYLES = {
    "Easy Run": {
        "fill": "#EAF4FC",
        "text": "#1F4E78",
    },
    "Long Run": {
        "fill": "#E2F0D9",
        "text": "#375623",
    },
    "Workout": {
        "fill": "#FCE4D6",
        "text": "#9C0006",
    },
    "Strides": {
        "fill": "#FFF2CC",
        "text": "#7F6000",
    },
    "Cross Training": {
        "fill": "#E4DFEC",
        "text": "#5F497A",
    },
    "Core": {
        "fill": "#DDEBF7",
        "text": "#1F4E78",
    },
    "Lifting": {
        "fill": "#D9EAD3",
        "text": "#274E13",
    },
    "Other": {
        "fill": "#E7E6E6",
        "text": "#595959",
    },
}


def build_output_path(output_path):
    """Return a path without overwriting an existing PDF."""

    path = Path(output_path)
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


def is_missing(value):
    """Return True when a value is blank or unavailable."""

    if value is None:
        return True

    text = str(value).strip().lower()

    if text in {
        "",
        "none",
        "nan",
        "<na>",
        "n/a",
    }:
        return True

    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def format_number(
    value,
    suffix="",
    decimals=0,
):
    """Format a numeric value safely."""

    if is_missing(value):
        return "N/A"

    number = float(value)

    if decimals == 0:
        result = f"{number:,.0f}"
    else:
        result = f"{number:,.{decimals}f}"

    if suffix:
        return f"{result} {suffix}"

    return result


def format_text(value):
    """Format text safely."""

    if is_missing(value):
        return "N/A"

    return str(value)


def friendly_date(value):
    """Convert an ISO date into a readable date."""

    try:
        date = datetime.fromisoformat(
            str(value)
        )

        return (
            date.strftime("%A, %B ")
            + str(date.day)
        )

    except ValueError:
        return str(value)


def chart_day_label(value):
    """Convert an ISO date into a weekday and numeric date."""

    try:
        date = datetime.fromisoformat(
            str(value)
        )

        return (
            f"{date.strftime('%a')} "
            f"{date.month}/{date.day}"
        )

    except ValueError:
        return str(value)


def get_styles():
    """Create the report's paragraph styles."""

    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "PeakMetricsTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor(
                "#1F2937"
            ),
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "PeakMetricsSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor(
                "#667085"
            ),
            alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "PeakMetricsSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor(
                "#1F2937"
            ),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.HexColor(
                "#1F2937"
            ),
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(
                "#667085"
            ),
            alignment=TA_CENTER,
        ),
        "header_left": ParagraphStyle(
            "CardHeaderLeft",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
        ),
        "header_right": ParagraphStyle(
            "CardHeaderRight",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_RIGHT,
        ),
        "lap_title": ParagraphStyle(
            "LapTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor(
                "#344054"
            ),
            alignment=TA_CENTER,
        ),
        "lap_header": ParagraphStyle(
            "LapHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor(
                "#475467"
            ),
            alignment=TA_CENTER,
        ),
        "lap_value": ParagraphStyle(
            "LapValue",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor(
                "#344054"
            ),
            alignment=TA_CENTER,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(
                "#667085"
            ),
        ),
    }


def metric_card(
    value,
    label,
    styles,
    width,
):
    """Create one summary metric card."""

    table = Table(
        [
            [
                Paragraph(
                    escape(str(value)),
                    styles["metric_value"],
                )
            ],
            [
                Paragraph(
                    escape(str(label)),
                    styles["metric_label"],
                )
            ],
        ],
        colWidths=[width],
        rowHeights=[30, 18],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F8FAFC"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor(
                        "#D9E2EC"
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
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


def build_summary_cards(
    summary,
    styles,
):
    """Create the weekly summary card grid."""

    card_width = (
        AVAILABLE_WIDTH - 24
    ) / 4

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
            summary.average_pace,
            "Average Pace",
        ),
        (
            f"{summary.average_hr} bpm",
            "Average HR",
        ),
        (
            str(summary.runs),
            "Runs",
        ),
        (
            f"{summary.max_hr} bpm",
            "Maximum HR",
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

    cards = [
        metric_card(
            value,
            label,
            styles,
            card_width,
        )
        for value, label in metrics
    ]

    outer = Table(
        [
            cards[:4],
            cards[4:],
        ],
        colWidths=[
            AVAILABLE_WIDTH / 4
        ] * 4,
    )

    outer.setStyle(
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
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return outer


def build_mileage_chart(
    daily_mileage,
    styles,
):
    """Create the daily mileage bar chart."""

    if daily_mileage.empty:
        return Paragraph(
            "No running mileage was found.",
            styles["small"],
        )

    mileage = [
        float(value)
        for value in daily_mileage[
            "Miles"
        ].tolist()
    ]

    labels = [
        chart_day_label(value)
        for value in daily_mileage[
            "Date"
        ].tolist()
    ]

    drawing = Drawing(
        AVAILABLE_WIDTH,
        215,
    )

    chart = VerticalBarChart()

    chart.x = 48
    chart.y = 32
    chart.width = (
        AVAILABLE_WIDTH - 78
    )
    chart.height = 155

    chart.data = [mileage]

    chart.categoryAxis.categoryNames = (
        labels
    )

    maximum = max(mileage)

    axis_maximum = max(
        5,
        math.ceil(maximum / 5) * 5,
    )

    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = axis_maximum

    chart.valueAxis.valueStep = max(
        1,
        math.ceil(axis_maximum / 5),
    )

    chart.bars[0].fillColor = (
        colors.HexColor("#4F86C6")
    )

    chart.bars[0].strokeColor = (
        colors.HexColor("#4F86C6")
    )

    # Display mileage in the center of each bar.
    chart.barLabelFormat = (
        lambda value: f"{value:.1f}"
    )

    chart.barLabels.visible = True
    chart.barLabels.boxTarget = "mid"
    chart.barLabels.boxAnchor = "c"
    chart.barLabels.textAnchor = "middle"
    chart.barLabels.fontName = (
        "Helvetica-Bold"
    )
    chart.barLabels.fontSize = 8
    chart.barLabels.fillColor = (
        colors.white
    )

    chart.categoryAxis.labels.fontName = (
        "Helvetica"
    )

    chart.categoryAxis.labels.fontSize = 8

    chart.valueAxis.labels.fontName = (
        "Helvetica"
    )

    chart.valueAxis.labels.fontSize = 8

    chart.categoryAxis.strokeColor = (
        colors.HexColor("#98A2B3")
    )

    chart.valueAxis.strokeColor = (
        colors.HexColor("#98A2B3")
    )

    chart.valueAxis.gridStrokeColor = (
        colors.HexColor("#E4E7EC")
    )

    chart.valueAxis.gridStrokeWidth = 0.5

    chart.barSpacing = 4
    chart.groupSpacing = 10

    drawing.add(chart)

    return drawing

def build_metric_grid(
    run,
    styles,
    width,
):
    """Create the left-side activity metrics."""

    metrics = [
        (
            format_number(
                run.get("Miles"),
                "mi",
                decimals=2,
            ),
            "Distance",
        ),
        (
            format_text(
                run.get("Time")
            ),
            "Time",
        ),
        (
            format_text(
                run.get("Pace (/mi)")
            ),
            "Average Pace",
        ),
        (
            format_number(
                run.get("Avg HR"),
                "bpm",
            ),
            "Average HR",
        ),
        (
            format_number(
                run.get(
                    "Elevation (ft)"
                ),
                "ft",
            ),
            "Elevation",
        ),
        (
            format_number(
                run.get("Power (W)"),
                "W",
            ),
            "Average Power",
        ),
        (
            format_number(
                run.get("Max HR"),
                "bpm",
            ),
            "Maximum HR",
        ),
        (
            format_number(
                run.get(
                    "Cadence (spm)"
                ),
                "spm",
            ),
            "Cadence",
        ),
    ]

    values_one = [
        Paragraph(
            escape(value),
            styles["metric_value"],
        )
        for value, _ in metrics[:4]
    ]

    labels_one = [
        Paragraph(
            escape(label),
            styles["metric_label"],
        )
        for _, label in metrics[:4]
    ]

    values_two = [
        Paragraph(
            escape(value),
            styles["metric_value"],
        )
        for value, _ in metrics[4:]
    ]

    labels_two = [
        Paragraph(
            escape(label),
            styles["metric_label"],
        )
        for _, label in metrics[4:]
    ]

    table = Table(
        [
            values_one,
            labels_one,
            values_two,
            labels_two,
        ],
        colWidths=[width / 4] * 4,
        rowHeights=[
            27,
            16,
            27,
            16,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F8FAFC"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor(
                        "#E4E7EC"
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
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


def build_lap_table(
    run,
    styles,
    width,
):
    """Create the activity lap-splits table."""

    laps = run.get("Laps") or []

    data = [
        [
            Paragraph(
                "Lap Splits",
                styles["lap_title"],
            ),
            "",
            "",
            "",
        ],
        [
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
                "Avg HR",
                styles["lap_header"],
            ),
        ],
    ]

    if laps:
        for index, lap in enumerate(
            laps,
            start=1,
        ):
            data.append(
                [
                    Paragraph(
                        escape(
                            str(
                                lap.get(
                                    "Lap",
                                    index,
                                )
                            )
                        ),
                        styles[
                            "lap_value"
                        ],
                    ),
                    Paragraph(
                        escape(
                            format_number(
                                lap.get(
                                    "Miles"
                                ),
                                "mi",
                                decimals=2,
                            )
                        ),
                        styles[
                            "lap_value"
                        ],
                    ),
                    Paragraph(
                        escape(
                            format_text(
                                lap.get(
                                    "Pace"
                                )
                            )
                        ),
                        styles[
                            "lap_value"
                        ],
                    ),
                    Paragraph(
                        escape(
                            format_number(
                                lap.get(
                                    "Avg HR"
                                ),
                                "bpm",
                            )
                        ),
                        styles[
                            "lap_value"
                        ],
                    ),
                ]
            )

    else:
        data.append(
            [
                Paragraph(
                    "No lap data found",
                    styles["small"],
                ),
                "",
                "",
                "",
            ]
        )

    table = Table(
        data,
        colWidths=[
            width * 0.13,
            width * 0.28,
            width * 0.29,
            width * 0.30,
        ],
        repeatRows=2,
    )

    commands = [
        (
            "SPAN",
            (0, 0),
            (-1, 0),
        ),
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor(
                "#E8EEF5"
            ),
        ),
        (
            "BACKGROUND",
            (0, 1),
            (-1, 1),
            colors.HexColor(
                "#F0F4F8"
            ),
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.HexColor(
                "#D9E2EC"
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
            2,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
    ]

    if not laps:
        commands.append(
            (
                "SPAN",
                (0, 2),
                (-1, 2),
            )
        )

    table.setStyle(
        TableStyle(commands)
    )

    return table


def build_activity_card(
    run,
    styles,
):
    """Create one complete PDF activity card."""

    run_type = str(
        run.get("Run Type")
        or "Other"
    )

    style = RUN_TYPE_STYLES.get(
        run_type,
        RUN_TYPE_STYLES["Other"],
    )

    fill_color = colors.HexColor(
        style["fill"]
    )
    text_color = colors.HexColor(
        style["text"]
    )

    header_left_style = ParagraphStyle(
        "DynamicHeaderLeft",
        parent=styles["header_left"],
        textColor=text_color,
    )

    header_right_style = ParagraphStyle(
        "DynamicHeaderRight",
        parent=styles["header_right"],
        textColor=text_color,
    )

    date_text = (
        f"{friendly_date(run.get('Date'))}"
        f" - {format_text(run.get('Time of Day'))}"
    )

    header = Table(
        [
            [
                Paragraph(
                    escape(date_text),
                    header_left_style,
                ),
                Paragraph(
                    escape(run_type),
                    header_right_style,
                ),
            ]
        ],
        colWidths=[
            AVAILABLE_WIDTH * 0.68,
            AVAILABLE_WIDTH * 0.32,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    fill_color,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#D0D5DD"
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
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    left_width = (
        AVAILABLE_WIDTH * 0.49
    )
    right_width = (
        AVAILABLE_WIDTH * 0.51
    )

    metrics = build_metric_grid(
        run,
        styles,
        left_width - 12,
    )

    laps = build_lap_table(
        run,
        styles,
        right_width - 12,
    )

    body = Table(
        [[metrics, laps]],
        colWidths=[
            left_width,
            right_width,
        ],
    )

    body.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
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
                    5,
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

    card = Table(
        [
            [header],
            [body],
        ],
        colWidths=[AVAILABLE_WIDTH],
    )

    card.setStyle(
        TableStyle(
            [
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
                    0,
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

    return KeepTogether(
        [
            card,
            Spacer(1, 10),
        ]
    )


def draw_footer(
    canvas,
    document,
):
    """Draw the footer and page number."""

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        8,
    )
    canvas.setFillColor(
        colors.HexColor("#667085")
    )

    canvas.drawString(
        LEFT_MARGIN,
        15,
        "PeakMetrics",
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        15,
        f"Page {document.page}",
    )

    canvas.restoreState()


def create_pdf_report(
    df,
    summary,
    daily_mileage,
    output_path,
):
    """Create the complete PeakMetrics PDF report."""

    output_path = build_output_path(
        output_path
    )

    styles = get_styles()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="PeakMetrics Weekly Training Report",
        author="PeakMetrics",
    )

    dates = sorted(
        str(value)
        for value in df["Date"]
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
        Spacer(1, 8),
        Paragraph(
            (
                "<b>Athlete:</b> CONFIG.athlete_name"
                " &nbsp;&nbsp;&nbsp; "
                "<b>Team:</b> CONFIG.team"
                " &nbsp;&nbsp;&nbsp; "
                f"<b>Week:</b> "
                f"{escape(dates[0])}"
                f" to "
                f"{escape(dates[-1])}"
            ),
            styles["small"],
        ),
        Spacer(1, 12),
        build_summary_cards(
            summary,
            styles,
        ),
        Spacer(1, 14),
        Paragraph(
            "Daily Mileage",
            styles["section"],
        ),
        build_mileage_chart(
            daily_mileage,
            styles,
        ),
        PageBreak(),
        Paragraph(
            "Activity Details",
            styles["title"],
        ),
        Paragraph(
            (
                f"{len(df)} activities"
                " in chronological order"
            ),
            styles["subtitle"],
        ),
        Spacer(1, 12),
    ]

    for run in df.to_dict(
        "records"
    ):
        story.append(
            build_activity_card(
                run,
                styles,
            )
        )

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path