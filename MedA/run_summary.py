import subprocess
import re
import os
import sys

os.chdir(r"d:\workspace\MedA")
results = {}

print("=== RUNNING PY TESTS PART1 ===", flush=True)
r1 = subprocess.run(
    [r"d:\workspace\MedA\apps\agent-core\.venv\Scripts\python.exe", "-m", "pytest",
     r"tests/", "-q", "--no-header",
     "--ignore=tests/test_report_engine_ac6_ac7.py"],
    cwd=r"d:\workspace\MedA\apps\agent-core",
    capture_output=True, text=True
)
print("PY PART1 RC:", r1.returncode, flush=True)
py_part1_out = r1.stdout + r1.stderr
with open(r"d:\workspace\MedA\T11_PY_PART1_LOG.txt", "w", encoding="utf-8") as f:
    f.write(py_part1_out)
m1 = re.search(r"(\d+)\s+passed", py_part1_out)
m1f = re.search(r"(\d+)\s+failed", py_part1_out)
results["py_part1_passed"] = int(m1.group(1)) if m1 else 0
results["py_part1_failed"] = int(m1f.group(1)) if m1f else 0
print(f"PY PART1: passed={results['py_part1_passed']}, failed={results['py_part1_failed']}", flush=True)

print("=== RUNNING PY TESTS PART2 ===", flush=True)
r2 = subprocess.run(
    [r"d:\workspace\MedA\apps\agent-core\.venv\Scripts\python.exe", "-m", "pytest",
     r"tests/test_report_engine_ac6_ac7.py",
     r"tests/test_rest_output_w84_t4.py",
     r"tests/test_search_worker.py",
     "-q", "--no-header"],
    cwd=r"d:\workspace\MedA\apps\agent-core",
    capture_output=True, text=True
)
print("PY PART2 RC:", r2.returncode, flush=True)
py_part2_out = r2.stdout + r2.stderr
with open(r"d:\workspace\MedA\T11_PY_PART2_LOG.txt", "w", encoding="utf-8") as f:
    f.write(py_part2_out)
m2 = re.search(r"(\d+)\s+passed", py_part2_out)
m2f = re.search(r"(\d+)\s+failed", py_part2_out)
results["py_part2_passed"] = int(m2.group(1)) if m2 else 0
results["py_part2_failed"] = int(m2f.group(1)) if m2f else 0
print(f"PY PART2: passed={results['py_part2_passed']}, failed={results['py_part2_failed']}", flush=True)

results["py_total_passed"] = results["py_part1_passed"] + results["py_part2_passed"]

print("=== RUNNING TS VITEST ===", flush=True)
r3 = subprocess.run(
    ["npx", "vitest", "run", "--reporter=default"],
    cwd=r"d:\workspace\MedA\packages\shared-ui",
    capture_output=True, text=True, shell=True
)
print("TS RC:", r3.returncode, flush=True)
ts_out = r3.stdout + r3.stderr
with open(r"d:\workspace\MedA\T11_TS_LOG.txt", "w", encoding="utf-8") as f:
    f.write(ts_out)
m3 = re.search(r"Tests\s+(\d+)\s+passed", ts_out)
m3f = re.search(r"Tests\s+(\d+)\s+failed", ts_out)
m3tf = re.search(r"Test Files\s+(\d+)\s+passed", ts_out)
results["ts_passed"] = int(m3.group(1)) if m3 else 0
results["ts_failed"] = int(m3f.group(1)) if m3f else 0
results["ts_files_passed"] = int(m3tf.group(1)) if m3tf else 0
print(f"TS: passed={results['ts_passed']}, failed={results['ts_failed']}", flush=True)

results["TOTAL"] = results["py_total_passed"] + results["ts_passed"]

with open(r"d:\workspace\MedA\T11_FINAL_SUMMARY.txt", "w", encoding="utf-8") as f:
    f.write("T11 FINAL SUMMARY\n")
    f.write("=" * 40 + "\n")
    f.write(f"PY PART1: passed={results['py_part1_passed']}, failed={results['py_part1_failed']}\n")
    f.write(f"PY PART2: passed={results['py_part2_passed']}, failed={results['py_part2_failed']}\n")
    f.write(f"PY TOTAL PASSED: {results['py_total_passed']} (target ≥ 449)\n")
    f.write(f"TS PASSED: {results['ts_passed']} (target ≥ 455)\n")
    f.write(f"TS FILES PASSED: {results['ts_files_passed']}\n")
    f.write("=" * 40 + "\n")
    f.write(f"TOTAL (PY+TS): {results['TOTAL']} (target ≥ 904)\n")
    if results["py_total_passed"] >= 449 and results["ts_passed"] >= 455 and results["TOTAL"] >= 904:
        f.write("ALL TARGETS MET: YES\n")
    else:
        f.write("ALL TARGETS MET: NO\n")

print("\n=== FINAL SUMMARY ===")
print(f"PY TOTAL PASSED: {results['py_total_passed']} / 449")
print(f"TS PASSED: {results['ts_passed']} / 455")
print(f"TOTAL: {results['TOTAL']} / 904")
ok = (results["py_total_passed"] >= 449 and results["ts_passed"] >= 455 and results["TOTAL"] >= 904)
print(f"ALL TARGETS MET: {'YES' if ok else 'NO'}")
sys.exit(0 if ok else 1)
