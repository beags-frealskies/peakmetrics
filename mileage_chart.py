"""Shared PeakMetrics mileage-chart rendering."""

from datetime import datetime
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


PEAK_NAVY = "#12304A"
PEAK_TEAL = "#169C9C"
PEAK_AQUA = "#63D6D0"
SECONDARY_TEXT = "#486581"
LIGHT_TEXT = "#829AB1"
GRID_COLOR = "#D9E2EC"

# Activities are stacked chronologically. These colors repeat only
# when a day contains more activities than the palette length.
SEGMENT_STYLES = [
    ("#169C9C", "white"),
    ("#63D6D0", PEAK_NAVY),
    ("#12304A", "white"),
    ("#46BDB7", "white"),
    ("#91E5E1", PEAK_NAVY),
]


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


def format_mileage_label(value):
    """Show whole miles without .0 and preserve useful decimals."""

    mileage = float(value)

    if mileage.is_integer():
        return str(int(mileage))

    return f"{mileage:.1f}"


def get_segments(record):
    """Return a clean list of mileage segments for one day."""

    raw_segments = record.get("Segments")
    segments = []

    if isinstance(raw_segments, list):
        for segment in raw_segments:
            if isinstance(segment, dict):
                value = segment.get("Miles", 0)
            else:
                value = segment

            try:
                miles = float(value)
            except (TypeError, ValueError):
                continue

            if miles > 0:
                segments.append(miles)

    if segments:
        return segments

    try:
        total = float(record.get("Miles", 0))
    except (TypeError, ValueError):
        total = 0

    if total > 0:
        return [total]

    return []


def create_daily_mileage_chart(
    daily_mileage,
    weekly_total,
    *,
    figsize=(12.8, 4.35),
    dpi=140,
    title_font_size=18,
    subtitle_font_size=10,
    total_font_size=11,
    axis_font_size=9,
    segment_font_size=10,
    total_label_font_size=10,
    pad_inches=0.12,
):
    """Create a stacked daily-mileage chart with doubles separated."""

    records = daily_mileage.to_dict("records")

    day_labels = [
        format_day_label(record.get("Date", ""))
        for record in records
    ]

    daily_totals = [
        float(record.get("Miles", 0) or 0)
        for record in records
    ]

    daily_segments = [
        get_segments(record)
        for record in records
    ]

    x_positions = list(range(len(records)))

    figure, axis = plt.subplots(
        figsize=figsize,
        dpi=dpi,
    )

    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")

    figure.subplots_adjust(
        left=0.055,
        right=0.985,
        top=0.76,
        bottom=0.22,
    )

    maximum_mileage = max(daily_totals)

    chart_ceiling = max(
        5,
        maximum_mileage * 1.30,
    )

    axis.set_ylim(0, chart_ceiling)
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

    bar_width = 0.58
    small_segment_threshold = chart_ceiling * 0.055

    for day_index, (segments, total) in enumerate(
        zip(daily_segments, daily_totals)
    ):
        bottom = 0.0

        for segment_index, segment_miles in enumerate(segments):
            fill_color, label_color = SEGMENT_STYLES[
                segment_index % len(SEGMENT_STYLES)
            ]

            axis.bar(
                day_index,
                segment_miles,
                width=bar_width,
                bottom=bottom,
                color=fill_color,
                edgecolor="white",
                linewidth=1.5,
                zorder=3,
            )

            center_y = bottom + segment_miles / 2
            label = format_mileage_label(segment_miles)

            if segment_miles >= small_segment_threshold:
                axis.text(
                    day_index,
                    center_y,
                    label,
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=segment_font_size,
                    fontweight="bold",
                    color=label_color,
                    zorder=5,
                )

            else:
                axis.annotate(
                    label,
                    (day_index + bar_width / 2, center_y),
                    xytext=(6, 0),
                    textcoords="offset points",
                    horizontalalignment="left",
                    verticalalignment="center",
                    fontsize=max(segment_font_size - 1, 7),
                    fontweight="bold",
                    color=PEAK_NAVY,
                    arrowprops={
                        "arrowstyle": "-",
                        "color": SECONDARY_TEXT,
                        "linewidth": 0.7,
                    },
                    zorder=6,
                    clip_on=False,
                )

            bottom += segment_miles

        axis.annotate(
            f"{total:.1f}",
            (day_index, total),
            xytext=(0, 7),
            textcoords="offset points",
            horizontalalignment="center",
            verticalalignment="bottom",
            fontsize=total_label_font_size,
            fontweight="bold",
            color=PEAK_NAVY,
            clip_on=False,
            zorder=6,
        )

    if len(records) == 1:
        axis.set_xlim(-0.8, 0.8)
    else:
        axis.set_xlim(-0.65, len(records) - 0.35)

    axis.set_xticks(x_positions)
    axis.set_xticklabels(day_labels)

    axis.tick_params(
        axis="x",
        length=0,
        pad=12,
        labelsize=axis_font_size,
        colors=SECONDARY_TEXT,
    )

    axis.tick_params(
        axis="y",
        length=0,
        pad=8,
        labelsize=axis_font_size,
        colors=LIGHT_TEXT,
    )

    axis.set_ylabel(
        "Miles",
        fontsize=axis_font_size,
        color=SECONDARY_TEXT,
        labelpad=10,
    )

    axis.set_title(
        "Daily Mileage",
        loc="left",
        fontsize=title_font_size,
        fontweight="bold",
        color=PEAK_NAVY,
        pad=24,
    )

    axis.text(
        0,
        1.02,
        (
            "Individual activities stacked chronologically "
            "- earliest at bottom"
        ),
        transform=axis.transAxes,
        horizontalalignment="left",
        verticalalignment="bottom",
        fontsize=subtitle_font_size,
        color=SECONDARY_TEXT,
    )

    axis.text(
        1,
        1.02,
        f"Week total: {weekly_total:.1f} mi",
        transform=axis.transAxes,
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=total_font_size,
        fontweight="bold",
        color=PEAK_TEAL,
    )

    image_buffer = BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        bbox_inches="tight",
        pad_inches=pad_inches,
        facecolor="white",
    )

    plt.close(figure)
    image_buffer.seek(0)

    return image_buffer
