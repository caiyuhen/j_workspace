import argparse
import json
import os
import pandas as pd
from src.schema import FeatureSchema
from src.training import (
    train_xgb_pipeline,
    train_lstm_pipeline,
    train_xgb_multi_pipeline,
    train_transformer_pipeline,
    persist_artifacts,
    persist_lstm_artifacts,
    persist_multi_artifacts,
    persist_transformer_artifacts,
)


def render_progress(done: int, total: int, stage: str, width: int = 36):
    total = max(total, 1)
    ratio = min(max(done / total, 0.0), 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "-" * (width - filled)
    return f"\r训练进度 [{bar}] {done}/{total} {ratio * 100:6.2f}% | {stage}"


def print_progress(done: int, total: int, stage: str):
    print(render_progress(done, total, stage), end="", flush=True)
    if done >= total:
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--output_dir", default="models")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--variants", nargs="+", default=["A", "B"])
    parser.add_argument(
        "--imbalance_strategy",
        choices=["none", "class_weight", "oversample"],
        default="class_weight",
    )
    parser.add_argument(
        "--model_types",
        nargs="+",
        choices=["xgb", "lstm", "xgb_multi", "transformer"],
        default=["xgb", "lstm", "xgb_multi", "transformer"],
    )
    parser.add_argument("--horizons", nargs="+", type=int, default=[7, 30])
    parser.add_argument("--max_rows", type=int, default=None)
    parser.add_argument("--show_progress", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.data_path)
    schema = FeatureSchema()
    if args.max_rows is not None and args.max_rows > 0 and len(df) > args.max_rows:
        if schema.date_col in df.columns:
            df = df.sort_values(schema.date_col).head(args.max_rows).reset_index(drop=True)
        else:
            df = df.head(args.max_rows).reset_index(drop=True)
    results = {}
    positive_rate_summary = {}
    total_steps = len(args.variants) * len(args.horizons) * len(args.model_types) * 2
    done_steps = 0
    if args.show_progress:
        print_progress(done_steps, total_steps, "准备开始训练")

    def advance(stage: str):
        nonlocal done_steps
        done_steps += 1
        if args.show_progress:
            print_progress(done_steps, total_steps, stage)

    for variant_idx, variant in enumerate(args.variants):
        seed = args.seed + variant_idx
        for horizon in args.horizons:
            xgb_artifacts = None
            lstm_artifacts = None
            xgb_multi_artifacts = None
            transformer_artifacts = None
            if "xgb" in args.model_types:
                try:
                    xgb_artifacts = train_xgb_pipeline(
                        df,
                        schema,
                        horizon_days=horizon,
                        seed=seed,
                        imbalance_strategy=args.imbalance_strategy,
                    )
                    results[f"xgb_{horizon}d_{variant}"] = xgb_artifacts["metrics"]
                    advance(f"完成 xgb horizon={horizon} variant={variant}")
                except Exception as exc:
                    results[f"xgb_{horizon}d_{variant}"] = {"error": str(exc)}
                    advance(f"xgb失败 horizon={horizon} variant={variant}")
            if "lstm" in args.model_types:
                try:
                    lstm_artifacts = train_lstm_pipeline(df, schema, horizon_days=horizon, seed=seed)
                    results[f"lstm_{horizon}d_{variant}"] = lstm_artifacts["metrics"]
                    advance(f"完成 lstm horizon={horizon} variant={variant}")
                except Exception as exc:
                    results[f"lstm_{horizon}d_{variant}"] = {"error": str(exc)}
                    advance(f"lstm失败 horizon={horizon} variant={variant}")
            if "xgb_multi" in args.model_types:
                try:
                    xgb_multi_artifacts = train_xgb_multi_pipeline(
                        df,
                        schema,
                        horizon_days=horizon,
                        seed=seed,
                        target_cols=list(schema.target_cols),
                        imbalance_strategy=args.imbalance_strategy,
                    )
                    results[f"xgb_multi_{horizon}d_{variant}"] = xgb_multi_artifacts["metrics"]
                    positive_rate_summary[f"xgb_multi_{horizon}d_{variant}"] = xgb_multi_artifacts[
                        "positive_rate_stats"
                    ]
                    advance(f"完成 xgb_multi horizon={horizon} variant={variant}")
                except Exception as exc:
                    results[f"xgb_multi_{horizon}d_{variant}"] = {"error": str(exc)}
                    advance(f"xgb_multi失败 horizon={horizon} variant={variant}")
            if "transformer" in args.model_types:
                try:
                    transformer_artifacts = train_transformer_pipeline(
                        df, schema, horizon_days=horizon, seed=seed, target_cols=list(schema.target_cols)
                    )
                    results[f"transformer_{horizon}d_{variant}"] = transformer_artifacts["metrics"]
                    advance(f"完成 transformer horizon={horizon} variant={variant}")
                except Exception as exc:
                    results[f"transformer_{horizon}d_{variant}"] = {"error": str(exc)}
                    advance(f"transformer失败 horizon={horizon} variant={variant}")
            if "xgb" in args.model_types and xgb_artifacts is not None:
                persist_artifacts(
                    args.output_dir,
                    xgb_artifacts,
                    horizon_days=horizon,
                    suffix=variant,
                    risk_thresholds=schema.risk_thresholds,
                )
                advance(f"保存 xgb horizon={horizon} variant={variant}")
            elif "xgb" in args.model_types:
                advance(f"跳过保存 xgb horizon={horizon} variant={variant}")
            if "lstm" in args.model_types and lstm_artifacts is not None:
                persist_lstm_artifacts(args.output_dir, lstm_artifacts, horizon_days=horizon, suffix=variant)
                advance(f"保存 lstm horizon={horizon} variant={variant}")
            elif "lstm" in args.model_types:
                advance(f"跳过保存 lstm horizon={horizon} variant={variant}")
            if "xgb_multi" in args.model_types and xgb_multi_artifacts is not None:
                persist_multi_artifacts(
                    args.output_dir,
                    xgb_multi_artifacts,
                    horizon_days=horizon,
                    suffix=variant,
                    risk_thresholds=schema.risk_thresholds,
                )
                advance(f"保存 xgb_multi horizon={horizon} variant={variant}")
            elif "xgb_multi" in args.model_types:
                advance(f"跳过保存 xgb_multi horizon={horizon} variant={variant}")
            if "transformer" in args.model_types and transformer_artifacts is not None:
                persist_transformer_artifacts(
                    args.output_dir,
                    transformer_artifacts,
                    horizon_days=horizon,
                    suffix=variant,
                    risk_thresholds=schema.risk_thresholds,
                )
                advance(f"保存 transformer horizon={horizon} variant={variant}")
            elif "transformer" in args.model_types:
                advance(f"跳过保存 transformer horizon={horizon} variant={variant}")
    os.makedirs(args.output_dir, exist_ok=True)
    with open(os.path.join(args.output_dir, "risk_thresholds.json"), "w", encoding="utf-8") as f:
        json.dump(schema.risk_thresholds, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output_dir, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output_dir, "positive_rate_summary.json"), "w", encoding="utf-8") as f:
        json.dump(positive_rate_summary, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
