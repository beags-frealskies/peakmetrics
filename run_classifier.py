"""Automatic activity classification for PeakMetrics."""

import math


# Use the exact FIT filename when PeakMetrics guesses incorrectly.
#
# Example:
#
# RUN_TYPE_OVERRIDES = {
#     "Morning_Strength.fit": "Core",
#     "Afternoon_Strength.fit": "Lifting",
#     "Friday_Run.fit": "Easy Run",
# }
#
RUN_TYPE_OVERRIDES = {}


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
    """Return True when an activity should count as running."""

    activity_text = normalize_activity_text(run)

    # Older FIT files may not contain sport information.
    if not activity_text:
        return True

    return any(
        word in activity_text
        for word in RUNNING_WORDS
    )


def classify_non_running_activity(run):
    """Classify activities that are not runs."""

    activity_text = normalize_activity_text(run)

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
    """Calculate the full activity pace in seconds per mile."""

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

        # A stride must be clearly faster than the
        # average pace of the full activity.
        is_fast = (
            lap_pace <= overall_pace - 40
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
    Detect a workout when any lap is at least
    45 seconds per mile faster than weekly pace.
    """

    if weekly_pace is None:
        return False

    workout_pace_cutoff = (
        weekly_pace - 45
    )

    for lap in run.get("Laps") or []:
        lap_pace = pace_to_seconds(
            lap.get("Pace")
        )

        if lap_pace is None:
            continue

        if lap_pace <= workout_pace_cutoff:
            return True

    return False


def classify_runs(df, summary):
    """Assign a training category to every activity."""

    result = df.copy()

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
                result.loc[index, "Miles"],
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
            run.get("Source File", "")
        )

        # Manual override always has first priority.
        if source_file in RUN_TYPE_OVERRIDES:
            classifications.append(
                RUN_TYPE_OVERRIDES[source_file]
            )
            continue

        # Detect non-running activities.
        non_running_label = (
            classify_non_running_activity(run)
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

        # Long Run takes priority over Workout.
        if (
            index == longest_run_index
            and miles >= long_run_threshold
        ):
            classifications.append(
                "Long Run"
            )
            continue

        # Strides are checked before Workout so short
        # repetitions do not become workouts.
        if has_stride_pattern(
            run,
            run_pace,
        ):
            classifications.append(
                "Strides"
            )
            continue

        # Any lap 45 sec/mi faster than the weekly
        # average makes the activity a Workout.
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