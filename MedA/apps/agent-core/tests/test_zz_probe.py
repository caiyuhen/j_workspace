import asyncio

from sqlmodel import Session

from app.db import engine
from app.models import PipelineRun
from app.services import pipeline_engine as pe
from app.services.pipeline_engine import create_pipeline_run, run_pipeline
from tests.test_w10_e2e_2preset import WORKSPACE_ID, _ensure_workspace


def test_probe(monkeypatch):
    with Session(engine) as s:
        _ensure_workspace(s, WORKSPACE_ID)
    run = create_pipeline_run(
        workspace_id=WORKSPACE_ID, preset="sglt2i_ckd", mode="snapshot", max_records=200
    )

    orig = pe._exec_step_N

    def wrapped(idx, run_obj, ctx):
        print(
            "ENTER",
            idx,
            "ctxkeys",
            sorted(k for k in (ctx or {}) if not k.startswith("_")),
            "abs",
            len((ctx or {}).get("abstracted_records") or []),
            "ft",
            len((ctx or {}).get("ft_records") or []),
            "ta",
            len((ctx or {}).get("ta_records") or []),
            "kept",
            len((ctx or {}).get("kept_records") or []),
            flush=True,
        )
        out = orig(idx, run_obj, ctx)
        print("EXIT ", idx, out, "abs", len((ctx or {}).get("abstracted_records") or []), flush=True)
        return out

    monkeypatch.setattr(pe, "_exec_step_N", wrapped)
    asyncio.run(run_pipeline(run.id, ctx={}))
    with Session(engine) as s:
        db_run = s.get(PipelineRun, run.id)
        for st in db_run.steps_json:
            print(st["step_index"], st["step_name"], st.get("n_in"), st.get("n_out"))
    assert False
