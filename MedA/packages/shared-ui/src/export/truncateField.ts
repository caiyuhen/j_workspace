export function truncateField(value: unknown, maxBytes: number, suffix: string = "...[truncated]"): string {
  if (value === null || value === undefined) return "";
  let s = String(value);
  const enc = new TextEncoder();
  const sufBytes = enc.encode(suffix).length;
  let bytes = enc.encode(s);
  if (bytes.length <= maxBytes) return s;
  const hardMax = Math.max(10, maxBytes);
  const target = Math.max(20, hardMax - sufBytes);
  while (bytes.length > target && s.length > 0) {
    const m = s.match(/^(.*)[。.!?！？；;,\s]/);
    if (m && m[1].length > 0) {
      s = m[1];
    } else {
      s = s.slice(0, -1);
    }
    bytes = enc.encode(s);
  }
  return s + suffix;
}
