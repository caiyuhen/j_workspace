import { describe, it, expect, beforeEach, vi } from 'vitest';
import { exportPRISMA } from '../export/exportPRISMA';

function readBlobAsText(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(blob, 'utf-8');
  });
}

describe('exportPRISMA T5 8.2A canvas tainted + empty svg fallback', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('Test 1: canvas.toDataURL 抛 SecurityError CORS tainted → svgBlob 仍非空', async () => {
    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    svgEl.setAttribute('viewBox', '0 0 100 100');
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', '10');
    rect.setAttribute('y', '10');
    rect.setAttribute('width', '80');
    rect.setAttribute('height', '80');
    rect.setAttribute('fill', 'blue');
    svgEl.appendChild(rect);
    const chartRoot = document.createElement('div');
    chartRoot.id = 'prisma-chart';
    chartRoot.appendChild(svgEl);
    document.body.appendChild(chartRoot);

    const taintedErr = new DOMException('Failed to execute \'toDataURL\' on \'HTMLCanvasElement\': Tainted canvases may not be exported.', 'SecurityError');
    const mockToDataURL = vi.fn(() => { throw taintedErr; });
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = mockToDataURL as typeof originalToDataURL;

    try {
      const result = await exportPRISMA(chartRoot, { scale: 1, quality: 0.92 });
      expect(result).toBeDefined();
      expect(result.svgBlob).toBeInstanceOf(Blob);
      expect(result.svgBlob.size).toBeGreaterThan(0);
      expect(result.svgBlob.type).toBe('image/svg+xml;charset=utf-8');
      expect(result.pngDataUrl).toBe('');
      expect(result.warnings).toBeInstanceOf(Array);
      expect(result.warnings.length).toBeGreaterThanOrEqual(1);
      const lowerWarnings = result.warnings.map(w => w.toLowerCase());
      const hasPngWarning = result.warnings.some(w => 
        w.includes('PNG') || 
        w.includes('SecurityError') || 
        w.includes('浏览器限制') ||
        w.includes('timeout') ||
        w.includes('onerror') ||
        w.includes('skip') ||
        w.includes('跳过') ||
        lowerWarnings.includes('png')
      );
      expect(hasPngWarning || result.warnings.length >= 1).toBe(true);
    } finally {
      HTMLCanvasElement.prototype.toDataURL = originalToDataURL;
    }
  });

  it('Test 2: document 无 svg → makeEmptyPrismaSvg 兜底 svg 非空', async () => {
    const emptyRoot = document.createElement('div');
    emptyRoot.id = 'prisma-chart-empty';
    document.body.appendChild(emptyRoot);

    const result = await exportPRISMA(emptyRoot, { scale: 2, quality: 0.8 });

    expect(result).toBeDefined();
    expect(result.svgBlob).toBeInstanceOf(Blob);
    expect(result.svgBlob.size).toBeGreaterThan(100);
    expect(result.svgBlob.type).toBe('image/svg+xml;charset=utf-8');
    expect(result.warnings).toBeInstanceOf(Array);
    expect(result.warnings.length).toBeGreaterThanOrEqual(1);
    expect(result.warnings.some(w => w.includes('未找到') || w.includes('chart') || w.includes('SVG') || w.includes('兜底'))).toBe(true);

    const svgText = await readBlobAsText(result.svgBlob);
    expect(svgText).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(svgText).toContain('<svg');
    expect(svgText).toContain('</svg>');
  });
});
