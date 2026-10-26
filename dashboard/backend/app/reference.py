"""Cohort statistics, parameter specifications and preset profiles.

Ported from website/health_score_website_v4.html. Cohort means/SDs for CLINICAL come from
data/health_fitness_dataset.csv; HARMONIZED and WEARABLE are the values the
original dashboard hard-coded.

The slider starting values (medians) come from dataset_stats.json, generated from both data
files by scripts/dataset_stats.py.
"""

import json
from pathlib import Path

DATASET_STATS = json.loads((Path(__file__).parent / "dataset_stats.json").read_text())

COHORTS = {
    "HARMONIZED": {
        "name": "Combined Master Dataset",
        "count": 724201,
        "stats": {
            "sleep_hours": {"mean": 7.05, "std": 0.98},
            "stress_level": {"mean": 5.47, "std": 1.93},
            "daily_steps": {"mean": 8624, "std": 2102},
            "heart_rate": {"mean": 70.48, "std": 5.68},
            "endurance_level": {"mean": 9.49, "std": 2.23},
            "bmi": {"mean": 22.05, "std": 2.82},
            "hydration_level": {"mean": 2.51, "std": 0.60},
        },
    },
    "CLINICAL": {
        "name": "Dataset 1: Plain",
        "count": 687701,
        "stats": {
            "sleep_hours": {"mean": 7.05, "std": 0.97},
            "stress_level": {"mean": 5.47, "std": 1.91},
            "daily_steps": {"mean": 8628, "std": 2055},
            "heart_rate": {"mean": 70.00, "std": 5.07},
            "endurance_level": {"mean": 9.49, "std": 2.25},
            "bmi": {"mean": 21.66, "std": 1.94},
            "hydration_level": {"mean": 2.50, "std": 0.58},
        },
    },
    "WEARABLE": {
        "name": "Dataset 2: Wearable Lifestyle",
        "count": 36500,
        "stats": {
            "sleep_hours": {"mean": 7.01, "std": 1.22},
            "stress_level": {"mean": 5.51, "std": 2.30},
            "daily_steps": {"mean": 8550, "std": 2850},
            "heart_rate": {"mean": 79.60, "std": 10.40},
            "endurance_level": {"mean": 9.50, "std": 1.85},
            "bmi": {"mean": 29.46, "std": 6.15},
            "hydration_level": {"mean": 2.74, "std": 0.82},
        },
    },
}

# `weight` stays server-side; everything else is sent to the client to build the sliders.
# `hint` is the short target shown next to each slider name.
PARAM_SPECS = [
    {
        "id": "sleep_hours", "name": "Sleep Duration", "unit": "hrs",
        "min": 4.0, "max": 11.0, "step": 0.1, "weight": 0.20,
        "hint": "Optimal: 7.0–9.0 hrs",
    },
    {
        "id": "stress_level", "name": "Stress Level", "unit": "/10",
        "min": 1.0, "max": 10.0, "step": 0.5, "weight": 0.15,
        "hint": "Optimal: 2.0–3.0 (healthy stress)",
    },
    {
        "id": "daily_steps", "name": "Daily Step Count", "unit": "steps",
        "min": 2000, "max": 22000, "step": 250, "weight": 0.15,
        "hint": "Optimal: 7,000–10,000 steps",
    },
    {
        "id": "heart_rate", "name": "Resting Heart Rate", "unit": "bpm",
        "min": 50, "max": 100, "step": 1, "weight": 0.15,
        "hint": "Optimal: ≤ 60 bpm",
    },
    {
        "id": "endurance_level", "name": "Aerobic Endurance", "unit": "pts",
        "min": 4.0, "max": 20.0, "step": 0.1, "weight": 0.15,
        "hint": "Optimal: ≥ 18.0 pts",
    },
    {
        "id": "bmi", "name": "Body Mass Index (BMI)", "unit": "kg/m²",
        "min": 15.0, "max": 50.0, "step": 0.1, "weight": 0.10,
        "hint": "Optimal: 22.0–25.0 kg/m² (<18 or >30 flagged)",
    },
    {
        "id": "hydration_level", "name": "Daily Hydration", "unit": "L",
        "min": 1.0, "max": 4.5, "step": 0.1, "weight": 0.10,
        "hint": "Optimal: 3.7 L (Men) / 2.7 L (Women)",
    },
]

# Sliders start at the combined dataset's median, snapped to the slider grid
for _p in PARAM_SPECS:
    _steps = round((DATASET_STATS["medians"][_p["id"]] - _p["min"]) / _p["step"])
    _p["default"] = round(_p["min"] + _steps * _p["step"], 2)

PARAM_IDS = [p["id"] for p in PARAM_SPECS]
SPECS_BY_ID = {p["id"]: p for p in PARAM_SPECS}

# Presets. Hydration can depend on the selected sex, so each profile is a function of it.
PROFILES = {
    "burnout": lambda sex: {
        "values": {"sleep_hours": 5.2, "stress_level": 8.5, "daily_steps": 4200, "heart_rate": 84,
                   "endurance_level": 6.8, "bmi": 27.5, "hydration_level": 1.6},
        "active_minutes": 15,
    },
    "athlete": lambda sex: {
        "values": {"sleep_hours": 8.2, "stress_level": 2.5, "daily_steps": 14500, "heart_rate": 54,
                   "endurance_level": 19.0, "bmi": 22.5, "hydration_level": 4.0 if sex == "M" else 3.2},
        "active_minutes": 110,
    },
}
