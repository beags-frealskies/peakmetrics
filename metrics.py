from datetime import timedelta


def meters_to_miles(meters):
    return round(meters / 1609.344, 2)


def meters_to_feet(meters):
    return round(meters * 3.28084)


def cadence_to_spm(cadence):
    if cadence is None:
        return None
    return cadence * 2


def seconds_to_hms(seconds):
    return str(timedelta(seconds=int(seconds)))


def pace_from_time(distance_miles, seconds):
    if distance_miles == 0:
        return ""

    pace = seconds / distance_miles

    minutes = int(pace // 60)
    sec = int(round(pace % 60))

    if sec == 60:
        minutes += 1
        sec = 0

    return f"{minutes}:{sec:02d}"