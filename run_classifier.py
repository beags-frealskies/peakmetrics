"""Automatic activity classification for PeakMetrics."""

import math


RUNNING_WORDS = (
    "running",
    "run",
    "trail_running",
    "treadmill",
    "jogging",
)

LIFTING_WORDS = (
    "strength",
    "weight",
    "lifting",
    "resistance",
)

CORE_WORDS = (
    "core",
    "abdominal",
)

CROSS_TRAINING_WORDS = (
    "cycling",
    "bike",
    "biking",
    "swimming",
    "rowing",
    "elliptical",
    "stair",
    "walking",
    "hiking",
    "cardio",
    "indoor_cycling",
    "fitness_equipment",
)


def safe_float(value, default=None):
    """Convert a value to float without crashing."""

    if value is None:
        return default

    try:
        number = float(value)

        if math.isnan(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def normalize_activity_text(run):
    """Combine and normalize the FIT sport fields."""

    sport = str(
        run.get("Sport") or ""
    ).lower()

    sub_sport = str(
        run.get("Sub Sport") or ""
    ).lower()

    text = f"{sport} {sub_sport}"

    return (
        text.replace("-", "_")
        .replace(" ", "_")
        .strip("_")
    )


def is_running_activity(run):
    """Return True when an activity counts as running."""

    activity_text = normalize_activity_text(
        run
    )

    # Older FIT files may not contain sport data.
    if not activity_text:
        return True

    return any(
        word in activity_text
        for word in RUNNING_WORDS
    )


def classify_non_running_activity(run):
    """Classify activities that are not runs."""

    activity_text = normalize_activity_text(
        run
    )

    if not activity_text:
        return None

    if any(
        word in activity_text
        for word in CORE_WORDS
    ):
        return "Core"

    if any(
        word in activity_text
        for word in LIFTING_WORDS
    ):
        return "Lifting"

    if any(
        word in activity_text
        for word in CROSS_TRAINING_WORDS
    ):
        return "Cross Training"

    if not is_running_activity(run):
        return "Other"

    return None


def time_to_seconds(value):
    """Convert H:MM:SS or MM:SS into seconds."""

    if value is None:
        return None

    parts = str(value).split(":")

    try:
        numbers = [
            int(float(part))
            for part in parts
        ]
    except ValueError:
        return None

    if len(numbers) == 3:
        hours, minutes, seconds = numbers

        return (
            hours * 3600
            + minutes * 60
            + seconds
        )

    if len(numbers) == 2:
        minutes, seconds = numbers

        return minutes * 60 + seconds

    return None


def pace_to_seconds(value):
    """Convert a pace such as 6:42 into seconds per mile."""

    if value is None:
        return None

    pace_text = (
        str(value)
        .replace("/mi", "")
        .strip()
    )

    parts = pace_text.split(":")

    if len(parts) != 2:
        return None

    try:
        minutes = int(parts[0])
        seconds = int(float(parts[1]))
    except ValueError:
        return None

    return minutes * 60 + seconds


def calculate_run_pace(run):
    """Calculate full activity pace in seconds per mile."""

    miles = safe_float(
        run.get("Miles")
    )

    total_seconds = time_to_seconds(
        run.get("Time")
    )

    if (
        miles is None
        or total_seconds is None
        or miles <= 0
    ):
        return None

    return total_seconds / miles


def has_stride_pattern(run, overall_pace):
    """Detect short and fast stride repetitions."""

    if overall_pace is None:
        return False

    short_fast_laps = []
    longer_fast_laps = []

    for lap in run.get("Laps") or []:
        lap_seconds = time_to_seconds(
            lap.get("Time")
        )

        lap_pace = pace_to_seconds(
            lap.get("Pace")
        )

        lap_miles = safe_float(
            lap.get("Miles"),
            0,
        )

        if (
            lap_seconds is None
            or lap_pace is None
            or lap_miles <= 0
        ):
            continue

        is_fast = (
            lap_pace
            <= overall_pace - 40
        )

        if not is_fast:
            continue

        if (
            6 <= lap_seconds <= 25
            and lap_miles <= 0.16
        ):
            short_fast_laps.append(lap)

        elif lap_seconds > 25:
            longer_fast_laps.append(lap)

    return (
        len(short_fast_laps) >= 3
        and len(longer_fast_laps) == 0
    )


def has_workout_lap(run, weekly_pace):
    """
    Detect a workout when at least one lap is:

    1. At least 60 seconds per mile faster than weekly pace.
    2. At least 0.10 miles long.
    """

    if weekly_pace is None:
        return False

    workout_pace_cutoff = (
        weekly_pace - 60
    )

    for lap in run.get("Laps") or []:
        lap_pace = pace_to_seconds(
            lap.get("Pace")
        )

        lap_miles = safe_float(
            lap.get("Miles"),
            0,
        )

        if (
            lap_pace is None
            or lap_miles < 0.10
        ):
            continue

        if lap_pace <= workout_pace_cutoff:
            return True

    return False


def classify_runs(
    df,
    summary,
    overrides=None,
):
    """Assign a training category to every activity."""

    result = df.copy()

    overrides = overrides or {}

    weekly_miles = max(
        safe_float(
            summary.mileage,
            0,
        ),
        0,
    )

    weekly_seconds = max(
        safe_float(
            summary.total_seconds,
            0,
        ),
        0,
    )

    weekly_pace = None

    if weekly_miles > 0:
        weekly_pace = (
            weekly_seconds
            / weekly_miles
        )

    running_indices = [
        index
        for index, run in result.iterrows()
        if is_running_activity(run)
    ]

    longest_run_index = None

    if running_indices:
        longest_run_index = max(
            running_indices,
            key=lambda index: safe_float(
                result.loc[
                    index,
                    "Miles",
                ],
                0,
            ),
        )

    long_run_threshold = max(
        9.0,
        weekly_miles * 0.14,
    )

    classifications = []

    for index, run in result.iterrows():
        source_file = str(
            run.get(
                "Source File",
                "",
            )
        )

        # Saved manual corrections have highest priority.
        if source_file in overrides:
            classifications.append(
                overrides[source_file]
            )
            continue

        # Categorize non-running activities.
        non_running_label = (
            classify_non_running_activity(
                run
            )
        )

        if non_running_label is not None:
            classifications.append(
                non_running_label
            )
            continue

        miles = safe_float(
            run.get("Miles"),
            0,
        )

        run_pace = calculate_run_pace(
            run
        )

        # Long Run takes priority over every running category.
        if (
            index == longest_run_index
            and miles >= long_run_threshold
        ):
            classifications.append(
                "Long Run"
            )
            continue

        # Strides are checked before Workout.
        if has_stride_pattern(
            run,
            run_pace,
        ):
            classifications.append(
                "Strides"
            )
            continue

        # Workout rule:
        # one lap at least 0.10 mi long and
        # 60 sec/mi faster than weekly average.
        if has_workout_lap(
            run,
            weekly_pace,
        ):
            classifications.append(
                "Workout"
            )
            continue

        classifications.append(
            "Easy Run"
        )

    result["Run Type"] = classifications

    return result