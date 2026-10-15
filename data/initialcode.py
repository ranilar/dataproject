import tkinter as tk
from tkinter import ttk


def compute_health_metrics(sleep, stress, endurance, steps, resting_hr, bmi, hydration):
    """
    Computes sub-scores (0-100) and composite health score calibrated against
    the baseline means and standard deviations in health_fitness_dataset.csv.
    """
    # 1. Optimal Range: Sleep (Target: 7.0 - 8.0 hrs, mean = 7.05, std = 0.97)
    if 7.0 <= sleep <= 8.0:
        sleep_score = 100.0
    elif sleep < 7.0:
        z = (7.0 - sleep) / 0.97
        sleep_score = max(0.0, 100.0 - 25.0 * (z ** 1.5))
    else:
        z = (sleep - 8.0) / 0.97
        sleep_score = max(0.0, 100.0 - 30.0 * (z ** 1.5))

    # 2. Lower is Better: Stress (Scale 1-10, mean = 5.47, std = 1.91)
    stress_score = max(0.0, min(100.0, 100.0 - (stress - 1.0) / 9.0 * 95.0))

    # 3. Higher is Better: Endurance Level (mean = 9.49, std = 2.25)
    z_end = (endurance - 9.49) / 2.25
    endurance_score = max(0.0, min(100.0, 50.0 + z_end * 22.0))

    # 4. Higher is Better: Daily Steps (mean = 8,628, std = 2,055)
    z_steps = (steps - 8628.0) / 2055.0
    steps_score = max(0.0, min(100.0, 50.0 + z_steps * 20.0))

    # 5. Lower is Better: Resting Heart Rate (mean = 70.0 bpm, std = 5.07)
    z_rhr = (70.0 - resting_hr) / 5.07
    rhr_score = max(0.0, min(100.0, 50.0 + z_rhr * 22.0))

    # 6. Optimal Range: BMI (Target: 20.0 - 23.0, mean = 21.66)
    if 20.0 <= bmi <= 23.0:
        bmi_score = 100.0
    elif bmi < 20.0:
        bmi_score = max(0.0, 100.0 - ((20.0 - bmi) / 1.5) * 45.0)
    else:
        bmi_score = max(0.0, 100.0 - ((bmi - 23.0) / 2.0) * 45.0)

    # 7. Higher is Better: Hydration Level (mean = 2.50 L, std = 0.58)
    z_hyd = (hydration - 2.50) / 0.58
    hydration_score = max(0.0, min(100.0, 60.0 + z_hyd * 25.0))

    # Weighted composite score
    base_score = (
        0.20 * sleep_score +
        0.15 * stress_score +
        0.15 * endurance_score +
        0.15 * steps_score +
        0.15 * rhr_score +
        0.10 * bmi_score +
        0.10 * hydration_score
    )

    # Synergy / Interaction Penalty: Short sleep (< 6.0h) + High stress (> 7.0)
    interaction_penalty = 0.0
    if sleep < 6.0 and stress > 7.0:
        severity = ((6.0 - sleep) / 2.0) * ((stress - 7.0) / 3.0)
        interaction_penalty = min(15.0, severity * 12.0)

    final_score = max(0.0, min(100.0, base_score - interaction_penalty))

    sub_scores = {
        'Sleep': sleep_score,
        'Stress': stress_score,
        'Endurance': endurance_score,
        'Steps': steps_score,
        'Resting HR': rhr_score,
        'BMI': bmi_score,
        'Hydration': hydration_score
    }
    return final_score, interaction_penalty, sub_scores


class HealthScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Health Score Simulator")
        self.geometry("780x780")
        self.configure(bg="#f8fafc")

        # Parameter configurations [name, min, max, default, step, unit, archetype]
        self.param_specs = [
            ("sleep", "Sleep Duration", 4.0, 10.0, 7.0, 0.1, "hrs", "Optimal: 7-8h (Mean: 7.05h)"),
            ("stress", "Stress Level", 1.0, 10.0, 5.0, 0.5, "/10", "Lower is better (Mean: 5.47)"),
            ("endurance", "Endurance Level", 4.5, 18.0, 9.5, 0.1, "pts", "Higher is better (Mean: 9.49)"),
            ("steps", "Daily Steps", 2000, 16000, 8600, 100, "steps", "Higher is better (Mean: 8,628)"),
            ("resting_hr", "Resting Heart Rate", 50, 88, 70, 1, "bpm", "Lower is better (Mean: 70 bpm)"),
            ("bmi", "BMI", 18.5, 25.0, 21.7, 0.1, "", "Optimal: 20-23 (Mean: 21.66)"),
            ("hydration", "Hydration", 1.5, 3.5, 2.5, 0.1, "L", "Higher is better (Mean: 2.50L)")
        ]

        self.vars = {}
        self.val_labels = {}
        self.sub_labels = {}

        self.setup_ui()
        self.recalculate()

    def setup_ui(self):
        header_frame = tk.Frame(self, bg="#1e293b", pady=16)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="Health Score Calculator",
            font=("Helvetica", 18, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        ).pack()
        tk.Label(
            header_frame,
            text="Calibrated against population distribution in health_fitness_dataset.csv",
            font=("Helvetica", 10),
            fg="#94a3b8",
            bg="#1e293b"
        ).pack()

        # Score display frame
        score_card = tk.Frame(self, bg="#ffffff", bd=1, relief="ridge", pady=12, padx=20)
        score_card.pack(fill="x", padx=20, pady=12)

        self.score_label = tk.Label(score_card, text="--", font=("Helvetica", 36, "bold"), fg="#2563eb", bg="#ffffff")
        self.score_label.pack()

        self.verdict_label = tk.Label(score_card, text="", font=("Helvetica", 12, "bold"), bg="#ffffff")
        self.verdict_label.pack()

        self.penalty_label = tk.Label(score_card, text="", font=("Helvetica", 9, "italic"), fg="#dc2626", bg="#ffffff")
        self.penalty_label.pack()

        # Sliders container
        sliders_frame = tk.Frame(self, bg="#f8fafc", padx=20)
        sliders_frame.pack(fill="both", expand=True)

        for key, name, min_val, max_val, default_val, step, unit, desc in self.param_specs:
            row = tk.Frame(sliders_frame, bg="#f8fafc", pady=4)
            row.pack(fill="x")

            col1 = tk.Frame(row, width=230, bg="#f8fafc")
            col1.pack(side="left", fill="y")
            col1.pack_propagate(False)

            tk.Label(col1, text=name, font=("Helvetica", 10, "bold"), anchor="w", bg="#f8fafc").pack(fill="x")
            tk.Label(col1, text=desc, font=("Helvetica", 8), fg="#64748b", anchor="w", bg="#f8fafc").pack(fill="x")

            var = tk.DoubleVar(value=default_val)
            self.vars[key] = var

            slider = ttk.Scale(
                row,
                from_=min_val,
                to=max_val,
                variable=var,
                command=lambda val, k=key: self.on_slider_moved()
            )
            slider.pack(side="left", fill="x", expand=True, padx=10)

            val_lbl = tk.Label(row, text=f"{default_val:.1f} {unit}", width=10, font=("Courier", 10), anchor="e", bg="#f8fafc")
            val_lbl.pack(side="left")
            self.val_labels[key] = (val_lbl, unit)

            sub_lbl = tk.Label(row, text="Sub: 50", width=12, font=("Helvetica", 9), anchor="e", fg="#334155", bg="#f8fafc")
            sub_lbl.pack(side="left", padx=5)
            self.sub_labels[key] = sub_lbl

    def on_slider_moved(self):
        # Update slider text values
        for key, _, _, _, _, _, unit, _ in self.param_specs:
            val = self.vars[key].get()
            lbl, u = self.val_labels[key]
            if key == "steps":
                lbl.config(text=f"{int(val)} {u}".strip())
            else:
                lbl.config(text=f"{val:.1f} {u}".strip())
        self.recalculate()

    def recalculate(self):
        val = {k: self.vars[k].get() for k in self.vars}
        score, penalty, sub_scores = compute_health_metrics(
            val['sleep'], val['stress'], val['endurance'],
            val['steps'], val['resting_hr'], val['bmi'], val['hydration']
        )

        self.score_label.config(text=f"{score:.1f} / 100")

        # Color and text feedback
        if score >= 80:
            color = "#16a34a"
            verdict = "Optimal Health & Recovery"
        elif score >= 60:
            color = "#2563eb"
            verdict = "Average / Moderate Health"
        elif score >= 40:
            color = "#d97706"
            verdict = "Sub-optimal: Attention Needed"
        else:
            color = "#dc2626"
            verdict = "Elevated Health Risk"

        self.score_label.config(fg=color)
        self.verdict_label.config(text=verdict, fg=color)

        if penalty > 0:
            self.penalty_label.config(
                text=f"⚠️ Synergy Alert: Sleep Deprivation + High Stress detected (-{penalty:.1f} penalty pts)"
            )
        else:
            self.penalty_label.config(text="")

        # Update individual sub-score badges
        sub_key_mapping = {
            'sleep': 'Sleep', 'stress': 'Stress', 'endurance': 'Endurance',
            'steps': 'Steps', 'resting_hr': 'Resting HR', 'bmi': 'BMI', 'hydration': 'Hydration'
        }
        for k, sub_name in sub_key_mapping.items():
            s_val = sub_scores[sub_name]
            lbl = self.sub_labels[k]
            lbl.config(text=f"Score: {s_val:.0f}/100")
            if s_val >= 75:
                lbl.config(fg="#16a34a")
            elif s_val >= 50:
                lbl.config(fg="#2563eb")
            else:
                lbl.config(fg="#dc2626")


if __name__ == "__main__":
    app = HealthScoreApp()
    app.mainloop()