"""Compute the dataset statistics the dashboard uses and write them to app/dataset_stats.json.

- ranges: observed min/max of each metric per dataset (used to shade the sliders and to
  decide when a percentile would be extrapolation)
- medians: per-metric medians of the combined data (used as the sliders' starting values)

Run from dashboard/backend:  python scripts/dataset_stats.py
Requires pandas and openpyxl (scripts/requirements.txt). The app itself only reads the JSON.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
OUT = Path(__file__).resolve().parents[1] / "app" / "dataset_stats.json"

METRICS = ["sleep_hours", "stress_level", "daily_steps", "heart_rate", "endurance_level", "bmi", "hydration_level"]


def load_dataset1():
    df = pd.read_csv(DATA_DIR / "health_fitness_dataset.csv")
    df = df.rename(columns={"resting_heart_rate": "heart_rate"})
    df.loc[df["daily_steps"] < 0, "daily_steps"] = pd.NA  # two impossible negative step counts
    return df[METRICS]


def load_dataset2():
    df = pd.read_excel(DATA_DIR / "Fitness_Health_Tracking_Dataset_with_Missing_Values.xlsx")
    out = pd.DataFrame({
        "sleep_hours": df["Hours_Slept"],
        "stress_level": df["Stress_Level (1-10)"],
        "daily_steps": df["Steps_Taken"],
        "heart_rate": df["Heart_Rate (bpm)"],  # daily heart rate; the dataset has no resting heart rate
        "bmi": df["Weight (kg)"] / (df["Height (cm)"] / 100) ** 2,
        "hydration_level": df["Water_Intake (Liters)"],
    })
    out["endurance_level"] = pd.NA  # not measured in this dataset
    return out[METRICS]


def ranges(df):
    result = {}
    for m in METRICS:
        col = pd.to_numeric(df[m], errors="coerce").dropna()
        result[m] = [round(float(col.min()), 2), round(float(col.max()), 2)] if len(col) else None
    return result


def main():
    d1, d2 = load_dataset1(), load_dataset2()
    combined = pd.concat([d1, d2], ignore_index=True)
    stats = {
        "ranges": {"CLINICAL": ranges(d1), "WEARABLE": ranges(d2), "HARMONIZED": ranges(combined)},
        "medians": {m: round(float(pd.to_numeric(combined[m], errors="coerce").median()), 2) for m in METRICS},
        "rows": {"CLINICAL": len(d1), "WEARABLE": len(d2), "HARMONIZED": len(combined)},
    }
    OUT.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
