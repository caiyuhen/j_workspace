"""Standalone: measure avg pipeline total duration for W11 2-presets N=2000.

Runs 2 full pipelines per preset and reports avg. Independent from pytest hooks.
"""

import asyncio
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "agent-core"))

from sqlmodel import Session
from app.db import engine, init_db, reset_db
from app.models import Workspace
import app.services.pipeline_engine as _pe
from app.services.pipeline_engine import create_pipeline_run, run_pipeline, PipelineRun
from app.services.sources.pubmed_adapter import _load_preset_snapshot_2000

reset_db()
init_db()

WSID = "meda-w11-dur-ws-001"
N = 2000
RUNS_PER_PRESET = 2
TIMEOUT_S = 240

_pe.MAX_RECORDS_HARD_CAP = 10000

with Session(engine) as s:
    if not s.get(Workspace, WSID):
        s.add(Workspace(id=WSID))
        s.commit()

all_dur: dict[str, list[float]] = defaultdict(list)

for preset in ("sglt2i_ckd", "glp1_weightloss"):
    print(f"\n[preset={preset}] measuring {RUNS_PER_PRESET} runs...", flush=True)
    records = _load_preset_snapshot_2000(preset)
    assert len(records) == N
    for trial in range(RUNS_PER_PRESET):
        run = create_pipeline_run(
            workspace_id=WSID, preset=preset, mode="snapshot", max_records=N
        )
        ctx = {"fetched_records": records, "pubmed_out": f"storage/{preset}"}
        t0 = time.perf_counter()

        async def _coro():
            await run_pipeline(run.id, ctx=ctx)

        asyncio.run(asyncio.wait_for(_coro(), timeout=TIMEOUT_S))
        dur = time.perf_counter() - t0
        with Session(engine) as s:
            db_run = s.get(PipelineRun, run.id)
            ok = db_run.status == "success"
        all_dur[preset].append(dur)
        tag = "OK" if ok else "FAIL"
        print(f"  trial#{trial+1}: {dur:6.2f}s  status={tag}", flush=True)

print("\n" + "=" * 72)
print("W11 E2E 2000-records — avg pipeline total duration per preset")
for preset, durs in all_dur.items():
    avg_s = sum(durs) / len(durs)
    print(
        f"  preset={preset:<20s}  n_runs={len(durs):<3d}  avg={avg_s:8.2f}s  "
        f"min={min(durs):8.2f}s  max={max(durs):8.2f}s"
    )
print("=" * 72)
