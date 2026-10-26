"""Parse a pasted wearable log (JSON object or comma-separated values) into dashboard inputs."""

import json
import math

from .reference import MOODS

# Dashboard field -> accepted keys, wearable-export name first
JSON_KEYS = {
    "sleep_hours": ("Hours_Slept", "sleep_hours"),
    "daily_steps": ("Steps_Taken", "daily_steps"),
    "heart_rate": ("Heart_Rate", "heart_rate"),
    "stress_level": ("Stress_Level", "stress_level"),
    "hydration_level": ("Water_Intake", "hydration_level"),
    "bmi": ("bmi", "BMI"),
}

# Positional order for CSV input; the first four are required
CSV_ORDER = ("sleep_hours", "daily_steps", "heart_rate", "stress_level", "bmi", "hydration_level")


class LogParseError(ValueError):
    pass


def _number(raw, field):
    try:
        x = float(raw)
    except (TypeError, ValueError):
        raise LogParseError(f"{field}: {raw!r} is not a number") from None
    if not math.isfinite(x):
        raise LogParseError(f"{field}: {raw!r} is not a finite number")
    return x


def _first_present(obj, keys):
    for k in keys:
        if obj.get(k) not in (None, ""):
            return obj[k]
    return None


def parse_log(raw):
    """Return {"values": {...}, "active_minutes": float|None, "mood": str|None}. Raises LogParseError."""
    raw = raw.strip()
    if not raw:
        raise LogParseError("empty input")

    values = {}
    active_minutes = None
    mood = None

    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            raise LogParseError(f"invalid JSON: {e.msg}") from None
        if not isinstance(obj, dict):
            raise LogParseError("JSON input must be an object")

        for field, keys in JSON_KEYS.items():
            v = _first_present(obj, keys)
            if v is not None:
                values[field] = _number(v, field)

        v = _first_present(obj, ("Active_Minutes", "active_minutes"))
        if v is not None:
            active_minutes = _number(v, "active_minutes")

        v = _first_present(obj, ("Mood", "mood"))
        if v is not None:
            if v not in MOODS:
                raise LogParseError(f"mood: {v!r} is not one of {', '.join(MOODS)}")
            mood = v
    else:
        parts = [s.strip() for s in raw.split(",")]
        if len(parts) < 4:
            raise LogParseError("CSV input needs at least 4 values: sleep, steps, heart rate, stress")
        for field, part in zip(CSV_ORDER, parts):
            if part:
                values[field] = _number(part, field)

    if not values and active_minutes is None and mood is None:
        raise LogParseError("no recognised fields")

    return {"values": values, "active_minutes": active_minutes, "mood": mood}
