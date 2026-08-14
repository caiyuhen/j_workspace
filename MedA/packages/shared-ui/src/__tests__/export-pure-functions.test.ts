// packages/shared-ui/src/__tests__/export-pure-functions.test.ts
import { describe, it, expect } from 'vitest';
import { sanitizeFilename } from '../export/sanitizeFilename';
import { truncateField } from '../export/truncateField';
import { makeEmptyPrismaSvg } from '../export/makeEmptyPrismaSvg';

describe('sanitizeFilename E5', () => {
  it('replaces Windows reserved chars with underscore', () => {
    expect(sanitizeFilename('a\\b:c*d?e"f<g>h|i.txt')).toBe('a_b_c_d_e_f_g_h_i.txt');
  });
  it('removes ASCII ctrl chars 0x00-0x1f', () => {
    expect(sanitizeFilename('abc\x00\x1fdef')).toBe('abcdef');
  });
  it('truncates 300 chars to 200 UTF-16', () => {
    const long = 'a'.repeat(300) + '.ris';
    const res = sanitizeFilename(long);
    expect(res.length).toBe(200);
    expect(res.endsWith('.ris')).toBe(true);
  });
  it('removes trailing spaces and dots', () => {
    expect(sanitizeFilename('  my file...  .ris  ')).toBe('my file.ris');
  });
  it('empty result falls back to given fallback default meda_export', () => {
    expect(sanitizeFilename('      \x00\x01  ')).toBe('meda_export');
    expect(sanitizeFilename('', 'custom.bin')).toBe('custom.bin');
  });
});

describe('truncateField E2 UTF-8 bytes', () => {
  it('truncates CJK by UTF-8 bytes with default suffix', () => {
    const cjk = '一二三四五六七八九十';
    const cjkUtf8 = new TextEncoder().encode(cjk);
    expect(cjkUtf8.length).toBe(30);
    const res = truncateField(cjk, 20);
    expect(new TextEncoder().encode(res).length).toBeLessThanOrEqual(20 + 14);
    expect(res).toContain('[truncated]');
  });
  it('value null/undefined returns empty string', () => {
    expect(truncateField(null, 100)).toBe('');
    expect(truncateField(undefined, 100)).toBe('');
    expect(truncateField(12345, 3)).toContain('[truncated]');
  });
});

describe('makeEmptyPrismaSvg E1', () => {
  it('returns string with xmlns + n=0 four boxes', () => {
    const svg = makeEmptyPrismaSvg(42, '本次检索 0 条');
    expect(svg).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(svg).toContain('本次检索 0 条');
    expect(svg).toContain('runId="42"');
    expect(svg.length).toBeGreaterThan(100);
  });
});
