"""Cohort statistics, parameter specifications and preset profiles.

Ported from website/website.v2.html. Cohort means/SDs for CLINICAL come from
data/health_fitness_dataset.csv; HARMONIZED and WEARABLE are the values the
original dashboard hard-coded.
"""

COHORTS = {
    "HARMONIZED": {
        "name": "Harmonized Master Cohort",
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
        "name": "Clinical Telemetry Cohort",
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
        "name": "Wearable Lifestyle Cohort",
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
PARAM_SPECS = [
    {
        "id": "sleep_hours", "name": "Sleep Duration", "unit": "hrs",
        "min": 4.0, "max": 11.0, "step": 0.1, "default": 7.5, "weight": 0.20,
        "info": "Optimal: 7.0–9.0 hrs (Report §11.2 - Sleep Health [2]). Warning if <6h or >10h.",
    },
    {
        "id": "stress_level", "name": "Autonomic Stress Level", "unit": "/10",
        "min": 1.0, "max": 10.0, "step": 0.5, "default": 2.5, "weight": 0.15,
        "info": "Optimal: 2.0–3.0 (Report §11.3 - Adaptive Eustress [6] awards 100 pts).",
    },
    {
        "id": "daily_steps", "name": "Daily Step Count", "unit": "steps",
        "min": 2000, "max": 22000, "step": 250, "default": 8500, "weight": 0.15,
        "info": "Optimal: 7,000–10,000 steps (Report §11.4 - Lancet [1] awards 100 pts). Diminishing returns >10k.",
    },
    {
        "id": "heart_rate", "name": "Resting Heart Rate (RHR)", "unit": "bpm",
        "min": 50, "max": 100, "step": 1, "default": 50, "weight": 0.15,
        "info": "Optimal: ≤50 bpm (awards 100 pts; athletic cardiovascular baseline).",
    },
    {
        "id": "endurance_level", "name": "Aerobic Endurance Score", "unit": "pts",
        "min": 4.0, "max": 20.0, "step": 0.1, "default": 18.0, "weight": 0.15,
        "info": "Optimal: ≥18.0 pts (Report §11.6 awards 100 pts). Scaled with active minutes & steps.",
    },
    {
        "id": "bmi", "name": "Body Mass Index (BMI)", "unit": "kg/m²",
        "min": 15.0, "max": 50.0, "step": 0.1, "default": 21.8, "weight": 0.10,
        "info": "Optimal: 20.2–23.4 kg/m² (awards 100 pts).",
    },
    {
        "id": "hydration_level", "name": "Daily Hydration Intake", "unit": "L",
        "min": 1.0, "max": 4.5, "step": 0.1, "default": 3.1, "weight": 0.10,
        "info": "Optimal: 3.7 L (Men) / 2.7 L (Women) (Report §11.1 - IOM [7]).",
    },
]

PARAM_IDS = [p["id"] for p in PARAM_SPECS]
SPECS_BY_ID = {p["id"]: p for p in PARAM_SPECS}

MOODS = ("Happy", "Neutral", "Sad", "Stressed")


def _by_sex(sex, male, female, other):
    return male if sex == "M" else female if sex == "F" else other


# Presets and sample logs. Hydration depends on the selected sex, so each profile is a function of it.
PROFILES = {
    # Presets
    "report_optimal": lambda sex: {
        "values": {"sleep_hours": 7.8, "stress_level": 2.5, "daily_steps": 8500, "heart_rate": 50,
                   "bmi": 21.8, "hydration_level": _by_sex(sex, 3.7, 2.7, 3.1), "endurance_level": 18.5},
        "active_minutes": 80, "mood": "Happy",
    },
    "clinical_med": lambda sex: {
        "values": {"sleep_hours": 7.05, "stress_level": 5.5, "daily_steps": 8628, "heart_rate": 70,
                   "endurance_level": 9.5, "bmi": 21.7, "hydration_level": _by_sex(sex, 3.7, 2.7, 2.5)},
        "active_minutes": 75, "mood": "Neutral",
    },
    "burnout": lambda sex: {
        "values": {"sleep_hours": 5.2, "stress_level": 8.5, "daily_steps": 4200, "heart_rate": 84,
                   "endurance_level": 6.8, "bmi": 27.5, "hydration_level": 1.6},
        "active_minutes": 15, "mood": "Stressed",
    },
    "athlete": lambda sex: {
        "values": {"sleep_hours": 8.2, "stress_level": 2.5, "daily_steps": 14500, "heart_rate": 50,
                   "endurance_level": 19.0, "bmi": 22.0, "hydration_level": 4.0 if sex == "M" else 3.2},
        "active_minutes": 110, "mood": "Happy",
    },
    # Sample logs
    "user12": lambda sex: {
        "values": {"sleep_hours": 7.8, "daily_steps": 9450, "heart_rate": 60, "stress_level": 2.5,
                   "bmi": 23.5, "hydration_level": 3.7 if sex == "M" else 2.7},
        "active_minutes": 80, "mood": "Happy",
    },
    "user47": lambda sex: {
        "values": {"sleep_hours": 5.4, "daily_steps": 5100, "heart_rate": 86, "stress_level": 7.5,
                   "bmi": 34.2, "hydration_level": 2.0},
        "active_minutes": 20, "mood": "Sad",
    },
    "csv1042": lambda sex: {
        "values": {"sleep_hours": 8.1, "daily_steps": 9200, "heart_rate": 56, "stress_level": 2.0,
                   "bmi": 22.4, "hydration_level": 3.8 if sex == "M" else 2.8},
        "active_minutes": 95, "mood": "Happy",
    },
    "csv2890": lambda sex: {
        "values": {"sleep_hours": 4.8, "daily_steps": 4100, "heart_rate": 82, "stress_level": 9.0,
                   "bmi": 24.1, "hydration_level": 1.8},
        "active_minutes": 10, "mood": "Stressed",
    },
}
