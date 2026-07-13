"""Rules for which activities count toward training totals."""

from run_classifier import is_running_activity


EXCLUDED_TOTAL_TYPES = {
    "Strides",
}


def get_activity_type(activity):
    """Read the activity type from either app or database data."""

    for key in (
        "Run Type",
        "run_type",
    ):
        value = activity.get(
            key
        )

        if value is not None:
            return str(value).strip()

    return ""


def counts_toward_totals(activity):
    """Return True when an activity belongs in running totals."""

    if not is_running_activity(
        activity
    ):
        return False

    activity_type = get_activity_type(
        activity
    )

    return (
        activity_type
        not in EXCLUDED_TOTAL_TYPES
    )