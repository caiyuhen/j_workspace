import pytest, json, tempfile, os, datetime
from scripts.serialize_bench_history import main as serialize_main, classify

class TestSerializeBenchHistory:
    def test_classify_pass_under_90pct(self):
        assert classify(10.0, 5.0) == "PASS"
    def test_classify_warn_90_to_95pct(self):
        assert classify(10.0, 9.3) == "WARN"
    def test_classify_hardblock_over_95pct(self):
        assert classify(10.0, 9.7) == "HARD_BLOCK"
    def test_main_0_artifacts_produces_2_history_files_with_schema(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            serialize_main(art, out)
            for w in ["7d","60d"]:
                fp = os.path.join(out, f"history_{w}.json")
                assert os.path.exists(fp)
                d = json.load(open(fp, encoding="utf-8"))
                for k in ["generated_at","window_days","entries"]:
                    assert k in d
                assert isinstance(d["entries"], list)
                assert d["window_days"] == (7 if w=="7d" else 60)
    def test_main_writes_empty_entries_len_zero(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            serialize_main(art, out)
            d7 = json.load(open(os.path.join(out, "history_7d.json")))
            assert len(d7["entries"]) == 0
    def test_fake_3_artifacts_collects_all_3_entries(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            for i in range(3):
                d = {
                    "sha": f"abc1230{i}", "commit_msg": f"commit {i}",
                    "branch": "main", "run_at": f"2026-08-2{i}T10:00:00Z",
                    "n500_median_ms": 500, "n1000_median_ms": 1200, "n2000_median_ms": 2400,
                    "n10000_median_ms": 8000, "n50000_median_ms": 40000,
                }
                with open(os.path.join(art, f"meda_bench_{i:04d}.json"), "w") as f:
                    json.dump(d, f)
            serialize_main(art, out)
            d7 = json.load(open(os.path.join(out, "history_7d.json")))
            assert len(d7["entries"]) == 3
            ent0 = d7["entries"][0]
            for k in ["sha","commit_msg","branch","date","slo","vs_baseline_v0110_speedup_x","alerts"]:
                assert k in ent0, f"entry missing key {k}"
            for sz in ["n500","n1000","n2000","n10000","n50000"]:
                assert sz in ent0["slo"], f"slo missing size {sz}"
    def test_fake_alert_hard_block_populated_when_over(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"a1b2c3","run_at":"2026-08-20T00:00:00Z",
                 "n500_median_ms":99999, "n1000_median_ms":99999, "n2000_median_ms":99999,
                 "n10000_median_ms":99999, "n50000_median_ms":99999}
            json.dump(d, open(os.path.join(art, "meda_bench_0001.json"),"w"))
            serialize_main(art, out)
            d7 = json.load(open(os.path.join(out, "history_7d.json")))
            alerts = d7["entries"][0]["alerts"]
            assert len(alerts) >= 1 and any(a["severity"] == "HARD_BLOCK" for a in alerts)
    def test_fake_n50k_40s_is_pass(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"z","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2400,"n10000_median_ms":8000,"n50000_median_ms":40000}
            json.dump(d, open(os.path.join(art, "meda_bench_m1.json"),"w"))
            serialize_main(art, out)
            d7 = json.load(open(os.path.join(out, "history_7d.json")))
            assert d7["entries"][0]["slo"]["n50000"]["status"] == "PASS"
    def test_fake_n10k_9s_is_warn(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"zz","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2400,"n10000_median_ms":9000,"n50000_median_ms":40000}
            json.dump(d, open(os.path.join(art, "meda_bench_m2.json"),"w"))
            serialize_main(art, out)
            s = json.load(open(os.path.join(out, "history_7d.json")))["entries"][0]["slo"]["n10000"]
            assert s["status"] == "WARN"
    def test_fake_n50k_44s_under_slo_pass(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"y","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2400,"n10000_median_ms":9000,"n50000_median_ms":40400}
            json.dump(d, open(os.path.join(art, "meda_bench_m3.json"),"w"))
            serialize_main(art, out)
            s = json.load(open(os.path.join(out, "history_7d.json")))["entries"][0]["slo"]["n50000"]
            assert s["status"] == "PASS"
    def test_speedup_dict_has_3_keys(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"s","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2419,"n10000_median_ms":9600,"n50000_median_ms":45000}
            json.dump(d, open(os.path.join(art, "meda_bench_m4.json"),"w"))
            serialize_main(art, out)
            e = json.load(open(os.path.join(out, "history_7d.json")))["entries"][0]
            sp = e["vs_baseline_v0110_speedup_x"]
            for k in ["n2000","n10000","n50000"]:
                assert k in sp and isinstance(sp[k], (int,float))
    def test_speedup_n2000_baseline_equal_1x_when_2419ms(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            d = {"sha":"s","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2419,"n10000_median_ms":9600,"n50000_median_ms":45000}
            json.dump(d, open(os.path.join(art, "meda_bench_m5.json"),"w"))
            serialize_main(art, out)
            sp = json.load(open(os.path.join(out, "history_7d.json")))["entries"][0]["vs_baseline_v0110_speedup_x"]
            assert abs(sp["n2000"] - 1.0) < 0.01
    def test_60d_window_caps_at_600_entries(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            for i in range(800):
                json.dump({"sha":f"{i:04d}","run_at":f"2026-01-{(i%28)+1:02d}","n500_median_ms":500,"n1000_median_ms":1000,"n2000_median_ms":2000,"n10000_median_ms":8000,"n50000_median_ms":40000},
                          open(os.path.join(art,f"meda_bench_{i:04d}.json"),"w"))
            serialize_main(art, out)
            d60 = json.load(open(os.path.join(out, "history_60d.json")))
            d7 = json.load(open(os.path.join(out, "history_7d.json")))
            assert len(d60["entries"]) <= 600
            assert len(d7["entries"]) <= 70
    def test_output_dir_created_if_missing(self):
        with tempfile.TemporaryDirectory() as art:
            out_nested = os.path.join(art, "nested", "sub", "out")
            serialize_main(art, out_nested)
            assert os.path.isdir(out_nested)
    def test_generated_at_is_utc_iso8601_format(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            serialize_main(art, out)
            d = json.load(open(os.path.join(out, "history_7d.json")))
            assert d["generated_at"].endswith("Z") and "T" in d["generated_at"]
    def test_corrupt_artifact_skips_gracefully_no_crash(self):
        with tempfile.TemporaryDirectory() as art, tempfile.TemporaryDirectory() as out:
            with open(os.path.join(art, "meda_bench_bad.json"), "wb") as f:
                f.write(b"\x00\x01\x02 NOT JSON")
            d = {"sha":"ok","run_at":"2026-08-20","n500_median_ms":500,"n1000_median_ms":1200,"n2000_median_ms":2400,"n10000_median_ms":8000,"n50000_median_ms":40000}
            json.dump(d, open(os.path.join(art, "meda_bench_good.json"),"w"))
            serialize_main(art, out)
            e = json.load(open(os.path.join(out, "history_7d.json")))["entries"]
            assert len(e) == 1
