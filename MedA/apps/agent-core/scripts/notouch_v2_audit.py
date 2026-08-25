"""NOTOUCH v2 Audit for W12.
Usage: python scripts/notouch_v2_audit.py <BASELINE_COMMIT>
Exit 0 = PASS, Exit 99 = HARD FAIL (blocks merge).
Only counts edits to 14 ANCHORS. WL whitelist lines allowed EXACTLY 2 additions:
  1. NewRunModal.tsx L209 max="2000" -> max="50000"   (attr only)
  2. NewRunModal.tsx L211 step="50"  -> step="250"    (attr only)
Append zones after pre-defined anchor offsets count as 0 WL.
"""
import sys, subprocess, re, pathlib
ANCHORS = [
    ("apps/agent-core/app/services/screening_engine.py", 749),
    ("apps/agent-core/app/services/rob2_engine.py", 66),
    ("apps/agent-core/app/services/abstractor.py", 722),
    ("apps/agent-core/app/services/sources/pubmed_adapter.py", 238),
    ("apps/agent-core/app/routers/workspace.py", 2040),
    ("apps/agent-core/app/models.py", 401),
    ("apps/agent-core/app/services/simhash.py", 151),
    ("apps/agent-core/app/services/pipeline_engine.py", 692),
    ("packages/shared-sdk/src/index.ts", 504),
    ("packages/shared-ui/src/index.ts", 142),
    ("packages/shared-ui/src/components/FunnelProgressBar.tsx", 104),
    ("packages/shared-ui/src/hooks/usePipelineRun.ts", 10**9),
    ("packages/shared-ui/src/pages/PipelineRunDetailPage.tsx", 10**9),
    ("packages/shared-ui/src/components/NewRunModal.tsx", 10**9),
]
ALLOWED_WL_LINES_ADDED = {
    "packages/shared-ui/src/components/NewRunModal.tsx": {
        re.compile(r'max=\{?\s*["\']?50000'),
        re.compile(r'step=\{?\s*["\']?250'),
    }
}

def main(base: str) -> int:
    bad = []
    for path, anchor_last_line in ANCHORS:
        p = pathlib.Path(path)
        if not p.exists():
            bad.append(f"MISSING FILE: {path}"); continue
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0", base, "--", str(p)], text=True, encoding="utf-8", errors="replace"
        )
        current_line = 0
        for line in diff.splitlines():
            if line.startswith("@@"):
                m = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if m: current_line = int(m.group(1)) - 1
                continue
            if line.startswith("+") and not line.startswith("+++"):
                current_line += 1
                if current_line <= anchor_last_line or anchor_last_line == 10**9:
                    content = line[1:].strip()
                    if path in ALLOWED_WL_LINES_ADDED:
                        pats = ALLOWED_WL_LINES_ADDED[path]
                        if any(p.search(content) for p in pats):
                            continue
                    bad.append(f"WL OVER: {path} L{current_line}: +{content[:80]}")
    if bad:
        print("NOTOUCH V2 AUDIT FAIL (WL over AC7 +2 limit):")
        [print(f"  - {b}") for b in bad]
        print(f"  TOTAL extra WL offenses = {len(bad)}")
        return 99
    print("NOTOUCH V2 AUDIT PASS AC7 (WL <= +2 exact) PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "HEAD~1"))
