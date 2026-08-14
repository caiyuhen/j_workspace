export function makeEmptyPrismaSvg(runId: number, reason: string): string {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" runId="${String(runId)}">
<title>PRISMA 2020 Flow Diagram (Empty Run ${String(runId)})</title>
<desc>${esc(reason)}</desc>
<rect x="50" y="50" width="700" height="500" fill="#fafafa" stroke="#ccc" />
<g font-family="sans-serif" font-size="14" fill="#333" text-anchor="middle">
<rect x="300" y="60" width="200" height="80" fill="#fff" stroke="#888"/>
<text x="400" y="105">Identification<br/>(n = 0)</text>
<rect x="300" y="180" width="200" height="80" fill="#fff" stroke="#888"/>
<text x="400" y="225">Screening<br/>(n = 0)</text>
<rect x="300" y="300" width="200" height="80" fill="#fff" stroke="#888"/>
<text x="400" y="345">Eligibility<br/>(n = 0)</text>
<rect x="300" y="420" width="200" height="80" fill="#fff" stroke="#888"/>
<text x="400" y="465">Included<br/>(n = 0)</text>
<text x="400" y="560" fill="#888" font-size="12">${esc(reason)}</text>
</g>
</svg>`;
}
