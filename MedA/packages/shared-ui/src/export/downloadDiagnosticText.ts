export function downloadBlob(filename: string, blob: Blob): void {
  try {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch {
    /* swallow, caller should try clipboard fallback */
  }
}
export function downloadDataUrl(filename: string, dataUrl: string): void {
  try {
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch {}
}
export function downloadDiagnosticText(stage: string, err: unknown, runId: number | null, extra: Record<string, unknown> = {}): void {
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  const fn = `meda_run${runId ?? "NULL"}_${stage.toUpperCase()}_ERROR_DIAGNOSTIC_${ts}.txt`;
  const stack = (err instanceof Error ? err.stack : String(err)) ?? "";
  const msg = err instanceof Error ? err.message : String(err);
  const payload: Record<string, unknown> = {
    stage,
    timestamp: ts,
    runId,
    errorMessage: msg.slice(0, 500),
    errorStack: stack.slice(0, 1500),
    ...extra,
  };
  const text = Object.entries(payload).map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`).join("\n");
  try { downloadBlob(fn, new Blob([text], { type: "text/plain;charset=utf-8" })); } catch {}
  try { void navigator.clipboard?.writeText(text); } catch {}
}
