const WIN_RESERVED = /[\\/:*?"<>|]/g;
const CTRL = /[\x00-\x1f]/g;
export function sanitizeFilename(raw: string, fallback: string = "meda_export"): string {
  let s = String(raw ?? "").replace(CTRL, "").replace(WIN_RESERVED, "_").trim();
  const dotIdx = s.lastIndexOf(".");
  let base: string;
  let ext: string;
  if (dotIdx > 0) {
    base = s.slice(0, dotIdx);
    ext = s.slice(dotIdx);
  } else {
    base = s;
    ext = "";
  }
  while (base.endsWith(".") || base.endsWith(" ")) base = base.slice(0, -1);
  s = ext ? base + ext : base;
  while (s.endsWith(".") || s.endsWith(" ")) s = s.slice(0, -1);
  if (s.length === 0) return fallback;
  if (s.length > 200) {
    const dotIdx2 = s.lastIndexOf(".");
    const ext2 = dotIdx2 > 160 ? s.slice(dotIdx2) : "";
    const base2 = ext2 ? s.slice(0, dotIdx2) : s;
    const maxBase = 200 - ext2.length;
    s = base2.slice(0, Math.max(1, maxBase)) + ext2;
  }
  return s || fallback;
}
