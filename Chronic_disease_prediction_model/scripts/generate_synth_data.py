import argparse
import json
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.schema import FeatureSchema


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _build_propensity_scores(static: dict, dynamic: dict):
    return {
        "stroke": (
            0.04 * (static["age"] - 50)
            + 0.9 * static["atrial_fibrillation"]
            + 0.7 * static["previous_stroke"]
            + 0.03 * (dynamic["systolic_bp"] - 130)
            + 0.6 * (dynamic["hba1c"] > 7)
        ),
        "diabetes": (
            0.03 * (dynamic["fasting_glucose"] - 95)
            + 0.6 * (dynamic["hba1c"] - 5.8)
            + 0.04 * (dynamic["bmi"] - 24)
        ),
        "arrhythmia": (
            0.7 * static["atrial_fibrillation"]
            + 0.04 * (dynamic["heart_rate"] - 70)
            - 0.02 * (dynamic["heart_rate_variability"] - 30)
        ),
        "hypertension": (
            0.06 * (dynamic["systolic_bp"] - 125)
            + 0.05 * (dynamic["diastolic_bp"] - 78)
            + 0.25 * (static["age"] > 60)
        ),
        "kidney_disease": (
            0.8 * static["chronic_kidney_disease"]
            + 0.15 * static["diabetes_years"]
            + 0.25 * (dynamic["crp"] > 2)
        ),
        "depression": (
            -0.25 * (dynamic["sleep_hours"] - 7)
            - 0.12 * (dynamic["physical_activity_days"] - 3)
            - 0.2 * (static["socioeconomic_score"] - 5)
        ),
        "anxiety": (
            -0.3 * (dynamic["sleep_efficiency"] - 80) / 10
            - 0.35 * (dynamic["heart_rate_variability"] - 30) / 10
        ),
        "alzheimer": (
            0.06 * (static["age"] - 60)
            + 0.8 * static["white_matter_lesions"]
        ),
        "coronary_heart_disease": (
            0.03 * (dynamic["ldl_cholesterol"] - 110)
            + 0.5 * static["heart_disease"]
            + 0.03 * (dynamic["systolic_bp"] - 125)
        ),
        "gout": (
            0.02 * (dynamic["triglycerides"] - 140)
            + 0.03 * (dynamic["bmi"] - 24)
            + 0.1 * static["diabetes_years"]
        ),
        "parkinson": (
            0.05 * (static["age"] - 60)
            - 0.02 * (dynamic["physical_activity_days"] - 3)
        ),
        "heart_failure": (
            -0.06 * (dynamic["left_ventricular_ejection"] - 55)
            + 0.6 * static["heart_disease"]
            + 0.02 * (dynamic["systolic_bp"] - 130)
        ),
        "asthma": (
            0.03 * (dynamic["air_quality"] - 70)
            + 0.08 * (dynamic["bmi"] - 24)
        ),
        "bronchiectasis": (
            0.035 * (dynamic["air_quality"] - 80)
            + 0.03 * (dynamic["crp"] - 1)
        ),
    }


def _apply_balanced_labels(df: pd.DataFrame, schema: FeatureSchema, target_positive_rate: float):
    for target in schema.target_cols:
        prob_col = f"{target}_score"
        threshold = np.quantile(df[prob_col], 1 - target_positive_rate)
        df[target] = (df[prob_col] >= threshold).astype(int)
    return df


def _time_split(df: pd.DataFrame, schema: FeatureSchema, train_ratio: float, val_ratio: float):
    df_sorted = df.sort_values(schema.date_col).reset_index(drop=True)
    n = len(df_sorted)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train_df = df_sorted.iloc[:n_train].copy()
    val_df = df_sorted.iloc[n_train:n_train + n_val].copy()
    test_df = df_sorted.iloc[n_train + n_val:].copy()
    return train_df, val_df, test_df


def _build_positive_rate_summary(datasets: dict, schema: FeatureSchema):
    summary = {}
    for split_name, split_df in datasets.items():
        split_stats = {}
        for target in schema.target_cols:
            rate = float(split_df[target].mean()) if len(split_df) else 0.0
            split_stats[target] = {
                "rows": int(len(split_df)),
                "positives": int(split_df[target].sum()) if len(split_df) else 0,
                "positive_rate": rate,
            }
        summary[split_name] = split_stats
    return summary


def generate_synthetic_data(patients=100, days=60, seed=42, balance_targets=False, target_positive_rate=0.5):
    rng = np.random.default_rng(seed)
    schema = FeatureSchema()
    records = []
    base_date = datetime(2024, 1, 1)
    for pid in range(patients):
        age = rng.integers(30, 80)
        gender = rng.integers(0, 2)
        static = {
            "age": age,
            "gender": gender,
            "ethnicity": rng.choice(["Asian", "Black", "Hispanic", "White", "Other"]),
            "education_years": rng.integers(6, 18),
            "socioeconomic_score": rng.integers(1, 10),
            "atrial_fibrillation": rng.integers(0, 2),
            "previous_stroke": rng.integers(0, 2),
            "previous_tia": rng.integers(0, 2),
            "heart_disease": rng.integers(0, 2),
            "diabetes_years": rng.integers(0, 15),
            "hypertension_years": rng.integers(0, 20),
            "hypertension_controlled": rng.integers(0, 2),
            "chronic_kidney_disease": rng.integers(0, 2),
            "peripheral_artery_disease": rng.integers(0, 2),
            "family_stroke_history": rng.integers(0, 2),
            "family_heart_disease": rng.integers(0, 2),
            "genetic_risk_score": rng.integers(1, 10),
            "carotid_plaque": rng.integers(0, 2),
            "white_matter_lesions": rng.integers(0, 2),
        }
        for day in range(days):
            date = base_date + timedelta(days=day)
            dynamic = {
                "systolic_bp": rng.normal(130, 15),
                "diastolic_bp": rng.normal(80, 10),
                "total_cholesterol": rng.normal(200, 30),
                "hdl_cholesterol": rng.normal(50, 10),
                "ldl_cholesterol": rng.normal(120, 25),
                "triglycerides": rng.normal(150, 40),
                "fasting_glucose": rng.normal(100, 20),
                "hba1c": rng.normal(6, 1),
                "bmi": rng.normal(26, 4),
                "waist_circumference": rng.normal(90, 10),
                "waist_hip_ratio": rng.normal(0.9, 0.08),
                "heart_rate": rng.normal(72, 8),
                "alcohol_units_week": rng.integers(0, 10),
                "physical_activity_days": rng.integers(0, 7),
                "mediterranean_diet_score": rng.integers(4, 12),
                "sleep_hours": rng.normal(7, 1),
                "crp": abs(rng.normal(1, 0.8)),
                "fibrinogen": rng.normal(300, 60),
                "left_ventricular_ejection": rng.normal(55, 8),
                "avg_systolic_bp_24h": rng.normal(128, 10),
                "bp_variability": rng.normal(10, 3),
                "heart_rate_variability": rng.normal(35, 8),
                "daily_steps": rng.normal(7000, 2000),
                "sleep_efficiency": rng.normal(80, 7),
                "air_quality": rng.normal(80, 20),
                "season": (date.month % 12) // 3,
            }
            disease_scores = _build_propensity_scores(static, dynamic)
            disease_probs = {name: float(_sigmoid(score / 3.0)) for name, score in disease_scores.items()}
            record = {
                schema.id_col: f"P{pid:04d}",
                schema.date_col: date,
                **static,
                **dynamic,
            }
            for disease in schema.target_cols:
                score_col = f"{disease}_score"
                record[score_col] = disease_probs[disease]
                if balance_targets:
                    record[disease] = 0
                else:
                    record[disease] = int(rng.random() < disease_probs[disease])
            records.append(record)
    df = pd.DataFrame(records)
    if balance_targets:
        df = _apply_balanced_labels(df, schema, target_positive_rate=target_positive_rate)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--patients", type=int, default=800)
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", default=r"d:\workspace\Chronic_disease_prediction_model\input")
    parser.add_argument("--train_ratio", type=float, default=0.7)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument("--target_positive_rate", type=float, default=0.5)
    parser.add_argument("--balance_targets", action="store_true")
    args = parser.parse_args()

    schema = FeatureSchema()
    df = generate_synthetic_data(
        patients=args.patients,
        days=args.days,
        seed=args.seed,
        balance_targets=args.balance_targets,
        target_positive_rate=args.target_positive_rate,
    )
    train_df, val_df, test_df = _time_split(df, schema, train_ratio=args.train_ratio, val_ratio=args.val_ratio)
    os.makedirs(args.output_dir, exist_ok=True)
    keep_cols = [c for c in df.columns if not c.endswith("_score")]
    train_df[keep_cols].to_csv(os.path.join(args.output_dir, "train.csv"), index=False)
    val_df[keep_cols].to_csv(os.path.join(args.output_dir, "val.csv"), index=False)
    test_df[keep_cols].to_csv(os.path.join(args.output_dir, "test.csv"), index=False)
    full_df = df[keep_cols]
    full_df.to_csv(os.path.join(args.output_dir, "all_balanced.csv"), index=False)
    summary = _build_positive_rate_summary(
        {"train": train_df, "val": val_df, "test": test_df, "all": df},
        schema,
    )
    with open(os.path.join(args.output_dir, "positive_rate_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
