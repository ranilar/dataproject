import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

# 1. Load Datasets
df_csv = pd.read_csv("health_fitness_dataset.csv")
df_xlsx = pd.read_excel("Fitness_Health_Tracking_Dataset_with_Missing_Values.xlsx")

# 2. Clean Anomalies in CSV
df_csv.loc[df_csv["daily_steps"] < 0, "daily_steps"] = np.nan
df_csv["daily_steps"] = df_csv["daily_steps"].fillna(df_csv["daily_steps"].median())

# 3. Train Endurance Bridge Model on CSV Telemetry
endurance_features = ["age", "duration_minutes", "daily_steps", "resting_heart_rate", "bmi"]
X_train = df_csv[endurance_features]
y_train = df_csv["endurance_level"]

reg_endurance = Ridge(alpha=1.0)
reg_endurance.fit(X_train, y_train)

# 4. Harmonize and Impute Excel Data
df_xlsx_clean = df_xlsx.sort_values(["User_ID", "Date"]).copy()

# Impute missing wearable sensor data using user-specific medians
impute_cols = ["Hours_Slept", "Water_Intake (Liters)", "Active_Minutes", "Heart_Rate (bpm)"]
for col in impute_cols:
    df_xlsx_clean[col] = df_xlsx_clean.groupby("User_ID")[col].transform(
        lambda s: s.ffill().bfill().fillna(s.median())
    )

# Compute derived metrics for Excel cohort
df_xlsx_clean["bmi"] = df_xlsx_clean["Weight (kg)"] / ((df_xlsx_clean["Height (cm)"] / 100.0) ** 2)

# Estimate endurance_level for Excel cohort
X_excel = df_xlsx_clean[[
    "Age", "Active_Minutes", "Steps_Taken", "Heart_Rate (bpm)", "bmi"
]].rename(columns={
    "Age": "age",
    "Active_Minutes": "duration_minutes",
    "Steps_Taken": "daily_steps",
    "Heart_Rate (bpm)": "resting_heart_rate"
})
df_xlsx_clean["endurance_level"] = np.clip(reg_endurance.predict(X_excel), 4.0, 19.0)

# Standardize categorical columns
gender_map = {"Female": "F", "Male": "M", "Other": "Other"}
df_xlsx_clean["gender_std"] = df_xlsx_clean["Gender"].map(gender_map)

# 5. Build Unified Dataframes
csv_standard = pd.DataFrame({
    "source_dataset": "clinical_csv",
    "subject_id": "CSV_" + df_csv["participant_id"].astype(str),
    "date": pd.to_datetime(df_csv["date"]),
    "age": df_csv["age"],
    "gender": df_csv["gender"],
    "bmi": df_csv["bmi"],
    "daily_steps": df_csv["daily_steps"],
    "sleep_hours": df_csv["sleep_hours"],
    "stress_level": df_csv["stress_level"],
    "hydration_liters": df_csv["hydration_level"],
    "resting_hr": df_csv["resting_heart_rate"],
    "endurance_level": df_csv["endurance_level"],
    "active_minutes": df_csv["duration_minutes"],
    "mood": np.nan,
    "chronic_condition": df_csv["health_condition"].fillna("None")
})

xlsx_standard = pd.DataFrame({
    "source_dataset": "wearable_xlsx",
    "subject_id": "XLS_" + df_xlsx_clean["User_ID"].astype(str),
    "date": pd.to_datetime(df_xlsx_clean["Date"]),
    "age": df_xlsx_clean["Age"],
    "gender": df_xlsx_clean["gender_std"],
    "bmi": df_xlsx_clean["bmi"],
    "daily_steps": df_xlsx_clean["Steps_Taken"],
    "sleep_hours": df_xlsx_clean["Hours_Slept"],
    "stress_level": df_xlsx_clean["Stress_Level (1-10)"],
    "hydration_liters": df_xlsx_clean["Water_Intake (Liters)"],
    "resting_hr": df_xlsx_clean["Heart_Rate (bpm)"],
    "endurance_level": df_xlsx_clean["endurance_level"],
    "active_minutes": df_xlsx_clean["Active_Minutes"],
    "mood": df_xlsx_clean["Mood"],
    "chronic_condition": "Unknown"
})

# 6. Concatenate into Master Cohort
master_df = pd.concat([csv_standard, xlsx_standard], ignore_index=True)
print(f"Master Cohort Shape: {master_df.shape}")