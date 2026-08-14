import { describe, it, expect } from 'vitest';
import { serializeRIS } from '../export/serializeRIS';
import { serializeBibTeX } from '../export/serializeBibTeX';
import sampleEntries from '../../../../apps/agent-core/tests/fixtures/export/sample_3entries_metadata.json';

interface LitEntry {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  year: number;
  volume?: string;
  issue?: string;
  pages?: string;
  abstract?: string;
  source: string;
  doi?: string;
  pmid?: string;
  pmcid?: string;
  url?: string;
  keywords?: string[];
}

const entries = sampleEntries as LitEntry[];

describe('serializeRIS L2 snapshot CJK+18特符', () => {
  it('3 entries pubmed/cnki/wanfang RIS matches snapshot', () => {
    const ris = serializeRIS(entries);
    expect(ris).toBeTruthy();
    expect(ris).toContain('TY  - JOUR');
    expect(ris).toContain('ER  - ');
    expect((ris.match(/TY  - JOUR/g) || []).length).toBe(3);
    expect((ris.match(/ER  - /g) || []).length).toBe(3);
    expect(ris).toMatchSnapshot();
  });
});

describe('serializeBibTeX L2 snapshot CJK+18特符 LaTeX转义', () => {
  it('3 entries BibTeX matches snapshot with meda_ citeKey prefix', () => {
    const bib = serializeBibTeX(entries);
    expect(bib).toBeTruthy();
    expect(bib).toContain('@article{meda_');
    expect((bib.match(/@article\{meda_/g) || []).length).toBe(3);
    expect(bib).toMatchSnapshot();
  });

  it('BibTeX 18 LaTeX特殊字符全部转义正确', () => {
    const bib = serializeBibTeX(entries);
    const fieldMatches = bib.match(/  \w+ = \{[\s\S]*?\}(?:,|\n)/g) || [];
    let fieldVals = '';
    for (const m of fieldMatches) {
      const valMatch = m.match(/ = \{([\s\S]*?)\}(?:,|\n)/);
      if (valMatch) fieldVals += valMatch[1] + '\n';
    }
    function noUnescaped(s: string, ch: string): boolean {
      const escCh = ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const removed = s.replace(new RegExp('\\\\' + escCh, 'g'), '');
      return !removed.includes(ch);
    }
    expect(noUnescaped(fieldVals, '&')).toBe(true);
    expect(noUnescaped(fieldVals, '%')).toBe(true);
    expect(noUnescaped(fieldVals, '#')).toBe(true);
    expect(noUnescaped(fieldVals, '_')).toBe(true);
    expect(bib).toContain('\\&');
    expect(bib).toContain('\\%');
    expect(bib).toContain('\\#');
    expect(bib).toContain('\\_');
    expect(bib).toContain('\\{');
    expect(bib).toContain('\\}');
    expect(bib).toMatchSnapshot();
  });
});
