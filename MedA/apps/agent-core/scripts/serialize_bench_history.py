import json, os, sys, pathlib, glob, datetime
SIZES_SLO = {"n500":1.0,"n1000":1.5,"n2000":3.0,"n10000":9.6,"n50000":45.0}
ALERT_LEVELS = [(0.95,"HARD_BLOCK"), (0.90,"WARN"), (-1,"PASS")]

def classify(target_s, median_s):
    r = median_s / target_s
    for thr, lvl in ALERT_LEVELS:
        if r >= thr:
            return lvl
    return "PASS"

def main(artifacts_dir: str, out_dir: str):
    files = sorted(glob.glob(os.path.join(artifacts_dir, "meda_bench_*.json")))
    entries = []
    for fp in files[-600:]:
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        slo = {}; alerts = []
        for sz, target in SIZES_SLO.items():
            med = d.get(f"{sz}_median_ms", 0) / 1000.0
            p95 = d.get(f"{sz}_p95_ms", 0) / 1000.0
            status = classify(target, med)
            slo[sz] = {"target_s": target, "median_s": round(med,3), "p95_s": round(p95,3), "status": status}
            if status != "PASS":
                alerts.append({"severity": status, "size": sz,
                               "message": f"{sz} median={med:.1f}s / target {target}s = {med/target*100:.0f}% of SLO"})
        baseline_2k = 2.419
        speedup = {
            "n2000": round(baseline_2k / (slo["n2000"]["median_s"] or 1e-9), 2),
            "n10000": round(31.0 / (slo["n10000"]["median_s"] or 1e-9), 2),
            "n50000": round(775.0 / (slo["n50000"]["median_s"] or 1e-9), 2),
        }
        entries.append({
            "sha": d.get("sha", "unknown")[:8], "commit_msg": d.get("commit_msg", "")[:80],
            "branch": d.get("branch", "main"), "date": d.get("run_at", d.get("date","")),
            "python": d.get("python",""), "os": d.get("os",""),
            "slo": slo, "vs_baseline_v0110_speedup_x": speedup, "alerts": alerts,
        })
    entries.sort(key=lambda e: e["date"] or "")
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    for window, limit in [("7d", 70), ("60d", 600)]:
        payload = {"generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                   "window_days": 7 if window == "7d" else 60,
                   "entries": entries[-limit:]}
        out_path = os.path.join(out_dir, f"history_{window}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        print(f"Wrote {out_path} ({len(payload['entries'])} entries)")
    tmpl = pathlib.Path(__file__).resolve().parents[2] / ".." / ".." / "docs" / "bench" / "index.html"
    if tmpl.exists():
        import shutil
        shutil.copy(tmpl, os.path.join(out_dir, "index.html"))
        print(f"Copied Dashboard static template → {out_dir}/index.html")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "./gh-pages-build/bench")
