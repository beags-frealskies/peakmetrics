"""PeakMetrics user configuration."""

import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)


CONFIG_PATH = Path("config.json")


@dataclass(frozen=True)
class PeakMetricsConfig:
    """User-editable PeakMetrics settings."""

    athlete_name: str
    team: str
    timezone: str


def load_config(
    config_path=CONFIG_PATH,
):
    """Read and validate config.json."""

    config_path = Path(
        config_path
    )

    if not config_path.exists():
        raise FileNotFoundError(
            "PeakMetrics could not find "
            f"{config_path}.\n\n"
            "Create config.json in the main "
            "project folder."
        )

    try:
        with config_path.open(
            "r",
            encoding="utf-8",
        ) as config_file:
            raw_config = json.load(
                config_file
            )

    except json.JSONDecodeError as error:
        raise ValueError(
            "config.json contains invalid JSON.\n"
            f"Problem near line {error.lineno}, "
            f"column {error.colno}."
        ) from error

    required_settings = [
        "athlete_name",
        "team",
        "timezone",
    ]

    missing_settings = [
        setting
        for setting in required_settings
        if setting not in raw_config
    ]

    if missing_settings:
        missing_text = ", ".join(
            missing_settings
        )

        raise ValueError(
            "config.json is missing these "
            f"settings: {missing_text}"
        )

    athlete_name = str(
        raw_config["athlete_name"]
    ).strip()

    team = str(
        raw_config["team"]
    ).strip()

    timezone_name = str(
        raw_config["timezone"]
    ).strip()

    if not athlete_name:
        raise ValueError(
            "athlete_name cannot be blank "
            "in config.json."
        )

    if not team:
        raise ValueError(
            "team cannot be blank in "
            "config.json."
        )

    try:
        ZoneInfo(
            timezone_name
        )

    except ZoneInfoNotFoundError as error:
        raise ValueError(
            "The timezone in config.json is "
            f"not valid: {timezone_name}"
        ) from error

    return PeakMetricsConfig(
        athlete_name=athlete_name,
        team=team,
        timezone=timezone_name,
    )


CONFIG = load_config()