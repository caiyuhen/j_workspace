"""Where generated artifacts are written on disk.

The pipeline's report step used to report a payload_ref of
`storage/{run_id}/report.pdf` without ever writing a file, so the run detail page
linked to something that did not exist. Reports are now really written, and this
module owns the one thing that has to be agreed on for that: the root directory.

The root is overridable through `MEDA_STORAGE_ROOT` so a deployment can point it
at a mounted volume; the default keeps everything inside the service directory
(and out of git).
"""

from __future__ import annotations

import os
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parents[1] / ".storage"

STORAGE_ROOT = Path(os.environ.get("MEDA_STORAGE_ROOT") or _DEFAULT_ROOT)

# Every stored path is reported relative to STORAGE_ROOT and starts with this
# segment, so a payload_ref stays meaningful if the root ever moves.
_RUNS_DIR = "storage"


def run_artifact_dir(run_id: str) -> Path:
    """The directory holding one pipeline run's artifacts, created if missing."""
    d = STORAGE_ROOT / _RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_run_artifact(run_id: str, filename: str, text: str) -> str:
    """Write one artifact and return its path relative to the storage root."""
    path = run_artifact_dir(run_id) / filename
    path.write_text(text, encoding="utf-8")
    return f"{_RUNS_DIR}/{run_id}/{filename}"


def read_run_artifact(run_id: str, filename: str) -> str | None:
    """Read back a stored artifact, or None if the run never produced it."""
    path = STORAGE_ROOT / _RUNS_DIR / run_id / filename
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")
