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

const BIB_MAX_TITLE_BYTES = 200;
const BIB_MAX_ABSTRACT_BYTES = 2000;

const LATEX_ESCAPE_MAP: Record<string, string> = {
  '\\': '\\textbackslash{}',
  '&': '\\&',
  '%': '\\%',
  '#': '\\#',
  '_': '\\_',
  '{': '\\{',
  '}': '\\}',
  '~': '\\textasciitilde{}',
  '^': '\\textasciicircum{}',
  '<': '\\textless{}',
  '>': '\\textgreater{}',
  '|': '\\textbar{}',
  '"': '\\textquotedbl{}',
  "'": '\\textquotesingle{}',
  '`': '\\textasciigrave{}',
  '$': '\\$',
  '@': '{\\char64}',
  '§': '{\\S}',
};

function escapeLaTeX(value: unknown): string {
  if (value === null || value === undefined) return '';
  let s = String(value);
  const keys = Object.keys(LATEX_ESCAPE_MAP).sort((a, b) => b.length - a.length);
  for (const k of keys) {
    s = s.split(k).join(LATEX_ESCAPE_MAP[k]);
  }
  return s;
}

function bibField(name: string, value: unknown, doEscape: boolean = true, maxBytes?: number): string {
  if (value === null || value === undefined) return '';
  let raw = String(value).trim();
  if (!raw) return '';
  if (maxBytes !== undefined) {
    raw = truncateField(raw, maxBytes);
  }
  const content = doEscape ? escapeLaTeX(raw) : raw;
  return `  ${name} = {${content}},\n`;
}

function citeKeyPrefix(): string {
  return 'meda_';
}

function makeCiteKey(e: LitEntry, idx: number): string {
  const firstAuthor = (e.authors?.[0] || 'anon').replace(/[^\w\u4e00-\u9fff]/g, '').slice(0, 12);
  const year = e.year ? String(e.year) : '0000';
  const serial = String(idx + 1).padStart(2, '0');
  return `${citeKeyPrefix()}${firstAuthor}${year}_${serial}`;
}

function splitPages(pages?: string): string {
  if (!pages) return '';
  return pages.trim().replace(/[–—]/g, '--');
}

export function serializeBibTeX(entries: LitEntry[]): string {
  let out = '';
  entries.forEach((e, idx) => {
    const ck = makeCiteKey(e, idx);
    out += `@article{${ck},\n`;
    out += bibField('title', e.title, true, BIB_MAX_TITLE_BYTES);
    const authors = (e.authors || []).map((a) => escapeLaTeX(a.trim())).filter(Boolean).join(' and ');
    if (authors) out += `  author = {${authors}},\n`;
    out += bibField('journal', e.journal);
    out += bibField('year', e.year, false);
    out += bibField('volume', e.volume);
    out += bibField('number', e.issue);
    const pages = splitPages(e.pages);
    if (pages) out += `  pages = {${pages}},\n`;
    out += bibField('abstract', e.abstract, true, BIB_MAX_ABSTRACT_BYTES);
    out += bibField('doi', e.doi, true);
    if (e.pmid?.trim()) out += `  pmid = {${escapeLaTeX(e.pmid.trim())}},\n`;
    if (e.pmcid?.trim()) out += `  pmcid = {${escapeLaTeX(e.pmcid.trim())}},\n`;
    out += bibField('url', e.url, true);
    const kws = (e.keywords || []).map((k) => escapeLaTeX(k.trim())).filter(Boolean).join(', ');
    if (kws) out += `  keywords = {${kws}},\n`;
    out += `  source = {${escapeLaTeX(e.source)}},\n`;
    out += `  meda_id = {${escapeLaTeX(e.id)}}\n`;
    out += '}\n\n';
  });
  return out;
}
