import argparse
import json
import os
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, roc_curve, log_loss
from sklearn.model_selection import StratifiedKFold, train_test_split, GroupShuffleSplit
from src.schema import FeatureSchema
from src.monitoring import detect_drift, compare_feature_distributions, should_rollback
from src.preprocessing import build_preprocess_pipeline, ensure_datetime, apply_range_clipping


def split_721(df, target_col, seed):
    train_df, temp_df = train_test_split(
        df,
        test_size=0.3,
        stratify=df[target_col],
        random_state=seed,
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=2 / 3,
        stratify=temp_df[target_col],
        random_state=seed,
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True), val_df.reset_index(drop=True)


def split_721_group(df, id_col, seed):
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=seed)
    train_idx, temp_idx = next(splitter.split(df, groups=df[id_col]))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    temp_df = df.iloc[temp_idx].reset_index(drop=True)
    splitter_2 = GroupShuffleSplit(n_splits=1, test_size=2 / 3, random_state=seed)
    val_idx, test_idx = next(splitter_2.split(temp_df, groups=temp_df[id_col]))
    val_df = temp_df.iloc[val_idx].reset_index(drop=True)
    test_df = temp_df.iloc[test_idx].reset_index(drop=True)
    return train_df, test_df, val_df


def split_721_time(df, date_col):
    df_sorted = df.sort_values(date_col).reset_index(drop=True)
    n = len(df_sorted)
    n_train = int(n * 0.7)
    n_test = int(n * 0.2)
    train_df = df_sorted.iloc[:n_train].reset_index(drop=True)
    test_df = df_sorted.iloc[n_train:n_train + n_test].reset_index(drop=True)
    val_df = df_sorted.iloc[n_train + n_test:].reset_index(drop=True)
    return train_df, test_df, val_df


def split_data(df, schema, target_col, seed, split_mode):
    if split_mode == "group":
        return split_721_group(df, schema.id_col, seed)
    if split_mode == "time":
        return split_721_time(df, schema.date_col)
    return split_721(df, target_col, seed)


def split_leakage_stats(train_df, test_df, val_df, id_col):
    train_ids = set(train_df[id_col].unique())
    test_ids = set(test_df[id_col].unique())
    val_ids = set(val_df[id_col].unique())
    overlap_train_test = train_ids.intersection(test_ids)
    overlap_train_val = train_ids.intersection(val_ids)
    overlap_test_val = test_ids.intersection(val_ids)
    total_overlap = len(overlap_train_test) + len(overlap_train_val) + len(overlap_test_val)
    return {
        "overlap_train_test": int(len(overlap_train_test)),
        "overlap_train_val": int(len(overlap_train_val)),
        "overlap_test_val": int(len(overlap_test_val)),
        "has_overlap": bool(total_overlap > 0),
    }


def build_model(params, seed):
    try:
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            learning_rate=params["learning_rate"],
            subsample=params["subsample"],
            colsample_bytree=params["colsample_bytree"],
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=seed,
        )
    except ModuleNotFoundError:
        return GradientBoostingClassifier(
            n_estimators=params["n_estimators"],
            learning_rate=params["learning_rate"],
            max_depth=params["max_depth"],
            random_state=seed,
        )


def distribution_summary(split_map, target_cols):
    result = {}
    for split_name, split_df in split_map.items():
        targets = {}
        for target in target_cols:
            if target in split_df.columns:
                targets[target] = float(split_df[target].mean())
        result[split_name] = {
            "rows": int(len(split_df)),
            "target_positive_rate": targets,
        }
    return result


def tune_with_cv(X_train, y_train, seed):
    param_grid = [
        {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8},
        {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.9, "colsample_bytree": 0.8},
        {"n_estimators": 400, "max_depth": 4, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.9},
    ]
    kfold = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
    cv_results = []
    best = None
    for params in param_grid:
        fold_train_losses = []
        fold_val_losses = []
        for fold_idx, (tr_idx, va_idx) in enumerate(kfold.split(X_train, y_train)):
            model = build_model(params, seed + fold_idx)
            model.fit(X_train[tr_idx], y_train[tr_idx])
            train_prob = model.predict_proba(X_train[tr_idx])[:, 1]
            val_prob = model.predict_proba(X_train[va_idx])[:, 1]
            train_loss = float(log_loss(y_train[tr_idx], train_prob, labels=[0, 1]))
            val_loss = float(log_loss(y_train[va_idx], val_prob, labels=[0, 1]))
            fold_train_losses.append(train_loss)
            fold_val_losses.append(val_loss)
        row = {
            "params": params,
            "mean_train_loss": float(np.mean(fold_train_losses)),
            "mean_val_loss": float(np.mean(fold_val_losses)),
            "fold_train_losses": fold_train_losses,
            "fold_val_losses": fold_val_losses,
        }
        cv_results.append(row)
        if best is None or row["mean_val_loss"] < best["mean_val_loss"]:
            best = row
    return best, cv_results


def train_with_loss_curve(X_train, y_train, X_val, y_val, params, seed):
    model = build_model(params, seed)
    train_curve = []
    val_curve = []
    try:
        model.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_val, y_val)], verbose=False)
        evals_result = model.evals_result()
        train_curve = evals_result.get("validation_0", {}).get("logloss", [])
        val_curve = evals_result.get("validation_1", {}).get("logloss", [])
    except Exception:
        model.fit(X_train, y_train)
        train_prob = model.predict_proba(X_train)[:, 1]
        val_prob = model.predict_proba(X_val)[:, 1]
        train_curve = [float(log_loss(y_train, train_prob, labels=[0, 1]))]
        val_curve = [float(log_loss(y_val, val_prob, labels=[0, 1]))]
    return model, train_curve, val_curve


def evaluate_on_test(model, X_test, y_test):
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "auroc": float(roc_auc_score(y_test, prob)),
    }
    cm = confusion_matrix(y_test, pred).tolist()
    fpr, tpr, thresholds = roc_curve(y_test, prob)
    roc_data = {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
    }
    return metrics, cm, roc_data, prob, pred


def feature_importance_report(model, feature_names):
    if not hasattr(model, "feature_importances_"):
        return []
    importances = model.feature_importances_
    ranking = np.argsort(importances)[::-1]
    result = []
    for idx in ranking:
        result.append({"feature": feature_names[idx], "importance": float(importances[idx])})
    return result


def error_sample_report(test_df, y_true, y_pred, y_prob, id_col, date_col):
    error_idx = np.where(y_true != y_pred)[0]
    columns = [id_col, date_col]
    result = test_df.iloc[error_idx][columns].copy()
    result["y_true"] = y_true[error_idx]
    result["y_pred"] = y_pred[error_idx]
    result["y_prob"] = y_prob[error_idx]
    result["confidence"] = np.abs(y_prob[error_idx] - 0.5) * 2
    result = result.sort_values("confidence", ascending=False)
    return result


def confidence_distribution(y_prob):
    bins = np.linspace(0, 1, 11)
    counts, edges = np.histogram(y_prob, bins=bins)
    return {"bin_edges": edges.tolist(), "counts": counts.tolist()}


def stability_test(train_X, train_y, test_X, test_y, params, seed, runs):
    metrics = []
    for i in range(runs):
        model = build_model(params, seed + i)
        model.fit(train_X, train_y)
        prob = model.predict_proba(test_X)[:, 1]
        pred = (prob >= 0.5).astype(int)
        metrics.append(
            {
                "seed": seed + i,
                "accuracy": float(accuracy_score(test_y, pred)),
                "f1": float(f1_score(test_y, pred, zero_division=0)),
                "auroc": float(roc_auc_score(test_y, prob)),
            }
        )
    summary = {
        "accuracy_mean": float(np.mean([m["accuracy"] for m in metrics])),
        "accuracy_std": float(np.std([m["accuracy"] for m in metrics])),
        "f1_mean": float(np.mean([m["f1"] for m in metrics])),
        "f1_std": float(np.std([m["f1"] for m in metrics])),
        "auroc_mean": float(np.mean([m["auroc"] for m in metrics])),
        "auroc_std": float(np.std([m["auroc"] for m in metrics])),
    }
    return metrics, summary


def build_dashboard_data(baseline_accuracy, current_accuracy, drift_alert_count):
    trend = [baseline_accuracy, current_accuracy]
    retrain_trigger = should_rollback(current_accuracy, baseline_accuracy, drop=0.05)
    return {
        "accuracy_trend": trend,
        "baseline_accuracy": baseline_accuracy,
        "current_accuracy": current_accuracy,
        "performance_drop_ratio": float(max((baseline_accuracy - current_accuracy) / max(baseline_accuracy, 1e-6), 0.0)),
        "retrain_trigger": retrain_trigger,
        "drift_alert_count": int(drift_alert_count),
    }


def subset_if_needed(df, max_rows, seed):
    if max_rows is None or max_rows <= 0 or len(df) <= max_rows:
        return df.reset_index(drop=True)
    return df.sample(n=max_rows, random_state=seed).reset_index(drop=True)


def evaluate_target(df, schema, target_col, seed, stability_runs, split_mode):
    train_df, test_df, val_df = split_data(df, schema, target_col, seed, split_mode)
    leakage = split_leakage_stats(train_df, test_df, val_df, schema.id_col)
    split_map = {"train": train_df, "test": test_df, "val": val_df}
    split_stats = distribution_summary(split_map, schema.target_cols)
    feature_cols = [schema.id_col, schema.date_col] + list(schema.target_cols)
    X_train_raw = train_df.drop(columns=feature_cols)
    X_test_raw = test_df.drop(columns=feature_cols)
    X_val_raw = val_df.drop(columns=feature_cols)
    y_train = train_df[target_col].values
    y_test = test_df[target_col].values
    y_val = val_df[target_col].values
    preprocess = build_preprocess_pipeline(schema, feature_columns=X_train_raw.columns.tolist())
    X_train = preprocess.fit_transform(X_train_raw)
    X_test = preprocess.transform(X_test_raw)
    X_val = preprocess.transform(X_val_raw)
    best, cv_results = tune_with_cv(X_train, y_train, seed)
    model, train_curve, val_curve = train_with_loss_curve(
        X_train, y_train, X_val, y_val, best["params"], seed
    )
    metrics, cm, roc_data, y_prob, y_pred = evaluate_on_test(model, X_test, y_test)
    feature_importance = feature_importance_report(model, preprocess.get_feature_names_out())
    error_samples = error_sample_report(test_df, y_test, y_pred, y_prob, schema.id_col, schema.date_col)
    confidence_dist = confidence_distribution(y_prob)
    stability_records, stability_summary = stability_test(
        X_train, y_train, X_test, y_test, best["params"], seed, stability_runs
    )
    val_prob = model.predict_proba(X_val)[:, 1]
    risk_drift = detect_drift(val_prob, y_prob, threshold=0.1)
    numeric_cols = [c for c in X_train_raw.columns if pd.api.types.is_numeric_dtype(train_df[c])]
    feature_drift = compare_feature_distributions(val_df, test_df, numeric_cols, threshold=0.1)
    drift_alert_count = sum(1 for item in feature_drift.values() if item["alert"]) + int(risk_drift["alert"])
    dashboard = build_dashboard_data(
        baseline_accuracy=float(accuracy_score(y_val, (val_prob >= 0.5).astype(int))),
        current_accuracy=metrics["accuracy"],
        drift_alert_count=drift_alert_count,
    )
    report = {
        "target": target_col,
        "split_ratio": {"train": 0.7, "test": 0.2, "val": 0.1},
        "evaluation_protocol": {
            "split_mode": split_mode,
            "optimistic_risk": bool(split_mode == "random"),
        },
        "leakage_audit": leakage,
        "distribution_consistency": split_stats,
        "hyperparameter_search": {"best": best, "cv_results": cv_results},
        "loss_curve": {"train_logloss": train_curve, "val_logloss": val_curve},
        "test_metrics": metrics,
        "confusion_matrix": cm,
        "roc_curve": roc_data,
        "feature_importance": feature_importance,
        "error_analysis": {
            "error_count": int(len(error_samples)),
            "error_rate": float(len(error_samples) / max(len(test_df), 1)),
        },
        "confidence_distribution": confidence_dist,
        "stability_test": {"records": stability_records, "summary": stability_summary},
        "drift_detection": {
            "threshold": 0.1,
            "risk_score_drift": risk_drift,
            "feature_drift": feature_drift,
        },
        "dashboard_monitoring": dashboard,
        "retraining": {
            "triggered": dashboard["retrain_trigger"],
            "condition": "性能下降超过5%",
        },
    }
    return report, train_df, test_df, val_df, cv_results, train_curve, val_curve, metrics, cm, roc_data, feature_importance, error_samples, confidence_dist


def save_svg_bar_chart(path, labels, values, title):
    width = 1200
    height = 680
    margin_left = 180
    margin_right = 40
    margin_top = 70
    margin_bottom = 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    n = max(len(labels), 1)
    bar_gap = 10
    band = plot_width / n
    bar_width = max(band - bar_gap, 6)
    max_val = max(values) if len(values) > 0 else 1.0
    max_val = max(max_val, 1e-8)
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="36" text-anchor="middle" font-size="24" font-family="Arial">{title}</text>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    for i in range(6):
        tick_val = max_val * i / 5
        y = margin_top + plot_height - plot_height * i / 5
        parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{margin_left + plot_width}" y2="{y}" stroke="#eee" stroke-width="1"/>')
        parts.append(f'<text x="{margin_left - 10}" y="{y + 4}" text-anchor="end" font-size="11" font-family="Arial">{tick_val:.3f}</text>')
    for i, (lab, val) in enumerate(zip(labels, values)):
        x = margin_left + i * band + (band - bar_width) / 2
        h = (val / max_val) * plot_height if max_val > 0 else 0
        y = margin_top + plot_height - h
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" fill="#4F81BD"/>')
        parts.append(f'<text x="{x + bar_width/2}" y="{y - 6}" text-anchor="middle" font-size="10" font-family="Arial">{val:.4f}</text>')
        parts.append(f'<text x="{x + bar_width/2}" y="{margin_top + plot_height + 18}" text-anchor="middle" font-size="10" font-family="Arial" transform="rotate(30 {x + bar_width/2},{margin_top + plot_height + 18})">{lab}</text>')
    parts.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def generate_overview_report(output_dir, all_reports, used_rows, split_mode):
    rows = []
    for target, report in all_reports.items():
        tm = report["test_metrics"]
        st = report["stability_test"]["summary"]
        drift = report["drift_detection"]["risk_score_drift"]
        dash = report["dashboard_monitoring"]
        rows.append(
            {
                "target": target,
                "accuracy": tm["accuracy"],
                "precision": tm["precision"],
                "recall": tm["recall"],
                "f1": tm["f1"],
                "auroc": tm["auroc"],
                "stability_accuracy_std": st["accuracy_std"],
                "stability_f1_std": st["f1_std"],
                "stability_auroc_std": st["auroc_std"],
                "risk_drift_psi": drift["psi"],
                "risk_drift_ks": drift["ks_stat"],
                "risk_drift_alert": int(drift["alert"]),
                "retrain_trigger": int(dash["retrain_trigger"]),
            }
        )
    metrics_df = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    metrics_df.to_csv(os.path.join(output_dir, "per_disease_metrics.csv"), index=False)
    summary = {
        "disease_count": int(len(metrics_df)),
        "used_rows": int(used_rows),
        "split_mode": split_mode,
        "means": metrics_df[["accuracy", "precision", "recall", "f1", "auroc"]].mean().to_dict(),
        "mins": metrics_df[["accuracy", "precision", "recall", "f1", "auroc"]].min().to_dict(),
        "maxs": metrics_df[["accuracy", "precision", "recall", "f1", "auroc"]].max().to_dict(),
        "drift_alert_count": int(metrics_df["risk_drift_alert"].sum()),
        "retrain_trigger_count": int(metrics_df["retrain_trigger"].sum()),
        "best_f1_target": str(metrics_df.iloc[0]["target"]) if len(metrics_df) else "",
        "worst_f1_target": str(metrics_df.iloc[-1]["target"]) if len(metrics_df) else "",
        "leakage_overlap_targets": int(sum(1 for r in all_reports.values() if r["leakage_audit"]["has_overlap"])),
    }
    with open(os.path.join(output_dir, "overview_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    save_svg_bar_chart(
        os.path.join(output_dir, "chart_f1_by_disease.svg"),
        metrics_df["target"].tolist(),
        metrics_df["f1"].tolist(),
        "F1 by Disease",
    )
    save_svg_bar_chart(
        os.path.join(output_dir, "chart_auroc_by_disease.svg"),
        metrics_df["target"].tolist(),
        metrics_df["auroc"].tolist(),
        "AUROC by Disease",
    )
    mean_names = ["accuracy", "precision", "recall", "f1", "auroc"]
    mean_vals = [float(summary["means"][k]) for k in mean_names]
    save_svg_bar_chart(
        os.path.join(output_dir, "chart_overview_means.svg"),
        mean_names,
        mean_vals,
        "Overview Metric Means",
    )
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# 模型总览报告")
    lines.append("")
    lines.append(f"- 生成时间: {ts}")
    lines.append(f"- 评估病种数: {summary['disease_count']}")
    lines.append(f"- 使用样本数: {summary['used_rows']}")
    lines.append(f"- 切分模式: {summary['split_mode']}")
    lines.append(f"- 存在患者跨集合重叠的病种数: {summary['leakage_overlap_targets']}")
    lines.append(f"- 漂移告警数: {summary['drift_alert_count']}")
    lines.append(f"- 重训练触发数: {summary['retrain_trigger_count']}")
    lines.append("")
    lines.append("## 总览图表")
    lines.append("")
    lines.append("![F1 by Disease](chart_f1_by_disease.svg)")
    lines.append("")
    lines.append("![AUROC by Disease](chart_auroc_by_disease.svg)")
    lines.append("")
    lines.append("![Overview Means](chart_overview_means.svg)")
    lines.append("")
    lines.append("## 每病指标")
    lines.append("")
    lines.append("| 疾病 | Accuracy | Precision | Recall | F1 | AUROC | 稳定性F1_STD | PSI | KS | 漂移告警 | 重训练触发 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, row in metrics_df.iterrows():
        lines.append(
            f"| {row['target']} | {row['accuracy']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['auroc']:.4f} | {row['stability_f1_std']:.6f} | {row['risk_drift_psi']:.4f} | {row['risk_drift_ks']:.4f} | {int(row['risk_drift_alert'])} | {int(row['retrain_trigger'])} |"
        )
    lines.append("")
    lines.append("## 关键信息")
    lines.append("")
    lines.append(f"- 最佳F1病种: {summary['best_f1_target']}")
    lines.append(f"- 最低F1病种: {summary['worst_f1_target']}")
    lines.append(f"- 汇总均值: accuracy={summary['means']['accuracy']:.4f}, precision={summary['means']['precision']:.4f}, recall={summary['means']['recall']:.4f}, f1={summary['means']['f1']:.4f}, auroc={summary['means']['auroc']:.4f}")
    if split_mode == "random":
        lines.append("- 风险提示: random切分可能出现同一患者跨集合，结果偏乐观。建议改用group或time模式。")
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return summary, metrics_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--output_dir", default="evaluation_output")
    parser.add_argument("--target_col", default="stroke")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability_runs", type=int, default=5)
    parser.add_argument("--all_targets", action="store_true")
    parser.add_argument("--max_rows", type=int, default=None)
    parser.add_argument("--split_mode", choices=["random", "group", "time"], default="random")
    args = parser.parse_args()
    df = pd.read_csv(args.data_path)
    schema = FeatureSchema()
    os.makedirs(args.output_dir, exist_ok=True)
    df = subset_if_needed(df, args.max_rows, args.seed)
    df = ensure_datetime(df, schema)
    df = apply_range_clipping(df, schema)
    if args.all_targets:
        all_reports = {}
        for idx, target in enumerate(schema.target_cols):
            report, _, _, _, _, _, _, _, _, _, _, _, _ = evaluate_target(
                df,
                schema,
                target,
                args.seed + idx,
                args.stability_runs,
                args.split_mode,
            )
            all_reports[target] = report
        with open(os.path.join(args.output_dir, "all_disease_reports.json"), "w", encoding="utf-8") as f:
            json.dump(all_reports, f, ensure_ascii=False, indent=2)
        summary, metrics_df = generate_overview_report(args.output_dir, all_reports, used_rows=len(df), split_mode=args.split_mode)
        print(json.dumps({"status": "ok", "report": os.path.join(args.output_dir, "report.md"), "summary": summary, "rows": int(len(metrics_df))}, ensure_ascii=False))
        return
    report, train_df, test_df, val_df, cv_results, train_curve, val_curve, metrics, cm, roc_data, feature_importance, error_samples, confidence_dist = evaluate_target(
        df,
        schema,
        args.target_col,
        args.seed,
        args.stability_runs,
        args.split_mode,
    )
    report["improvement_suggestions"] = [
        "增加近30天动态特征统计并进行特征筛选",
        "对高错误率区间样本进行重采样与阈值优化",
        "针对告警特征执行分桶稳定性修复与数据质量校验",
    ]
    train_df.to_csv(os.path.join(args.output_dir, "train_split.csv"), index=False)
    test_df.to_csv(os.path.join(args.output_dir, "test_split.csv"), index=False)
    val_df.to_csv(os.path.join(args.output_dir, "val_split.csv"), index=False)
    pd.DataFrame(cv_results).to_json(os.path.join(args.output_dir, "cv_results.json"), orient="records", force_ascii=False, indent=2)
    pd.DataFrame({"iteration": list(range(1, len(train_curve) + 1)), "train_logloss": train_curve, "val_logloss": val_curve}).to_csv(
        os.path.join(args.output_dir, "loss_curve.csv"), index=False
    )
    pd.DataFrame([metrics]).to_csv(os.path.join(args.output_dir, "test_metrics.csv"), index=False)
    pd.DataFrame(cm, columns=["pred_0", "pred_1"], index=["true_0", "true_1"]).to_csv(
        os.path.join(args.output_dir, "confusion_matrix.csv")
    )
    pd.DataFrame(roc_data).to_csv(os.path.join(args.output_dir, "roc_curve.csv"), index=False)
    pd.DataFrame(feature_importance).to_csv(os.path.join(args.output_dir, "feature_importance.csv"), index=False)
    error_samples.to_csv(os.path.join(args.output_dir, "error_samples.csv"), index=False)
    with open(os.path.join(args.output_dir, "confidence_distribution.json"), "w", encoding="utf-8") as f:
        json.dump(confidence_dist, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output_dir, "drift_report.json"), "w", encoding="utf-8") as f:
        json.dump(report["drift_detection"], f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output_dir, "dashboard_monitoring.json"), "w", encoding="utf-8") as f:
        json.dump(report["dashboard_monitoring"], f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.output_dir, "model_evaluation_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({"status": "ok", "report": os.path.join(args.output_dir, "model_evaluation_report.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
