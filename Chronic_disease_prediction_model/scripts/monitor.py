import argparse
import pandas as pd
from src.monitoring import detect_drift, should_rollback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline_path", required=True)
    parser.add_argument("--current_path", required=True)
    parser.add_argument("--baseline_auroc", type=float, required=True)
    parser.add_argument("--current_auroc", type=float, required=True)
    args = parser.parse_args()
    baseline = pd.read_csv(args.baseline_path)["risk"].values
    current = pd.read_csv(args.current_path)["risk"].values
    drift = detect_drift(baseline, current)
    rollback = should_rollback(args.current_auroc, args.baseline_auroc)
    result = {"drift": drift, "rollback": rollback}
    print(result)


if __name__ == "__main__":
    main()
