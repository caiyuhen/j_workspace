import { truncateField } from './truncateField';

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

const RIS_MAX_TITLE_BYTES = 200;
const RIS_MAX_ABSTRACT_BYTES = 2000;

function risLine(tag: string, value: unknown): string {
  if (value === null || value === undefined) return '';
  const s = String(value).trim();
  if (!s) return '';
  return `${tag}  - ${s}\n`;
}

function splitPages(pages?: string): { sp: string; ep: string } {
  if (!pages) return { sp: '', ep: '' };
  const parts = pages.split(/[-–—]/).map((p) => p.trim());
  return { sp: parts[0] || '', ep: parts[1] || '' };
}

export function serializeRIS(entries: LitEntry[]): string {
  let out = '';
  for (const e of entries) {
    out += risLine('TY', 'JOUR');
    out += risLine('TI', truncateField(e.title, RIS_MAX_TITLE_BYTES));
    for (const au of e.authors || []) {
      if (au?.trim()) out += risLine('AU', au.trim());
    }
    out += risLine('JO', e.journal);
    out += risLine('PY', e.year);
    out += risLine('VL', e.volume);
    out += risLine('IS', e.issue);
    const { sp, ep } = splitPages(e.pages);
    out += risLine('SP', sp);
    out += risLine('EP', ep);
    out += risLine('AB', truncateField(e.abstract, RIS_MAX_ABSTRACT_BYTES));
    out += risLine('DO', e.doi);
    out += risLine('PM', e.pmid);
    out += risLine('PMC', e.pmcid);
    out += risLine('UR', e.url);
    for (const kw of e.keywords || []) {
      if (kw?.trim()) out += risLine('KW', kw.trim());
    }
    out += risLine('N1', `source:${e.source};id:${e.id}`);
    out += 'ER  - \n\n';
  }
  return out;
}
