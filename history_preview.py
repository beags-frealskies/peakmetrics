"""Display the current PeakMetrics weekly history."""

from history_analytics import (
    load_weekly_history,
)


def main():
    """Print weekly training history."""

    history = load_weekly_history()

    if history.empty:
        print(
            "No training history was found."
        )
        return

    print()
    print("PeakMetrics Weekly History")
    print("-" * 90)

    print(
        history[
            [
                "Week",
                "Miles",
                "Runs",
                "Workouts",
                "Long Runs",
                "Strides",
                "Time",
                "Average Pace",
                "Average HR",
            ]
        ].to_string(index=False)
    )

    print()
    print(
        f"Stored weeks: {len(history)}"
    )


if __name__ == "__main__":
    main()