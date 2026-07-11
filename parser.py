"""FIT file parsing for PeakMetrics."""

from pathlib import Path

import fitdecode


def message_value(message, *field_names, default=None):
    """Return the first matching field value from a FIT message."""

    for field_name in field_names:
        for field in message.fields:
            if field.name == field_name:
                return field.value

    return default


def read_fit_file(file_path):
    """Read session and lap information from one FIT file."""

    session = None
    laps = []

    with fitdecode.FitReader(str(file_path)) as fit_reader:
        for frame in fit_reader:
            if not isinstance(
                frame,
                fitdecode.FitDataMessage,
            ):
                continue

            if frame.name == "session":
                session = {
                    "start_time": message_value(
                        frame,
                        "start_time",
                    ),
                    "sport": message_value(
                        frame,
                        "sport",
                    ),
                    "sub_sport": message_value(
                        frame,
                        "sub_sport",
                    ),
                    "total_distance": message_value(
                        frame,
                        "total_distance",
                        default=0,
                    ),
                    "total_timer_time": message_value(
                        frame,
                        "total_timer_time",
                        default=0,
                    ),
                    "avg_heart_rate": message_value(
                        frame,
                        "avg_heart_rate",
                    ),
                    "max_heart_rate": message_value(
                        frame,
                        "max_heart_rate",
                    ),
                    "total_ascent": message_value(
                        frame,
                        "total_ascent",
                        default=0,
                    ),
                    "avg_running_cadence": message_value(
                        frame,
                        "avg_running_cadence",
                        "avg_cadence",
                    ),
                    "avg_power": message_value(
                        frame,
                        "avg_power",
                    ),
                }

            elif frame.name == "lap":
                laps.append(
                    {
                        "start_time": message_value(
                            frame,
                            "start_time",
                        ),
                        "total_distance": message_value(
                            frame,
                            "total_distance",
                            default=0,
                        ),
                        "total_timer_time": message_value(
                            frame,
                            "total_timer_time",
                            default=0,
                        ),
                        "avg_heart_rate": message_value(
                            frame,
                            "avg_heart_rate",
                        ),
                    }
                )

    if session is None:
        raise ValueError(
            f"No session data was found in "
            f"{Path(file_path).name}"
        )

    session["laps"] = laps
    session["source_file"] = Path(file_path).name

    return session