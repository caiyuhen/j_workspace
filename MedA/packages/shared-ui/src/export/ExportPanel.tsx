import React from 'react';
import { downloadBlob, downloadDataUrl, downloadDiagnosticText } from './downloadDiagnosticText';
import { sanitizeFilename } from './sanitizeFilename';
import { serializeRIS as defaultSerializeRIS } from './serializeRIS';
import { serializeBibTeX as defaultSerializeBibTeX } from './serializeBibTeX';
import { exportPRISMA as defaultExportPRISMA } from './exportPRISMA';

type ExportPanelProps = {
  detail: any;
  onDone?: (...args: any[]) => void;
  serializeRIS?: (rows: any[]) => string;
  serializeBibTeX?: (rows: any[]) => string;
  exportPRISMA?: () => Promise<{ svgBlob: Blob; pngDataUrl: string }>;
  serializeCSV?: (rows: any[]) => string;
  serializeJSONL?: (rows: any[]) => string;
  onRisExport?: () => void;
  onBibTeXExport?: () => void;
  onPRISMAExport?: () => void;
  onCsvExport?: () => void;
  onJsonlExport?: () => void;
  children?: React.ReactNode;
  onExportEvidenceCsv?: () => void;
  onExportForestSvg?: () => void;
};

const EXPORTABLE_STATUSES = new Set(['completed', 'partial_failed']);

function defaultSerializeCSV(rows: any[]): string {
  if (!rows.length) return '';
  const headers = Object.keys(rows[0]);
  const headerLine = headers.join(',');
  const bodyLines = rows.map((r) =>
    headers.map((h) => {
      const v = (r as any)[h];
      const s = v === null || v === undefined ? '' : String(v);
      if (s.includes(',') || s.includes('"') || s.includes('\n')) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    }).join(','),
  );
  return [headerLine, ...bodyLines].join('\r\n');
}

function defaultSerializeJSONL(rows: any[]): string {
  return rows.map((r) => JSON.stringify(r)).join('\n');
}

function makeDateStamp(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}${m}${day}`;
}

export function ExportPanel({
  detail,
  onDone,
  serializeRIS: serializeRISProp,
  serializeBibTeX: serializeBibTeXProp,
  exportPRISMA: exportPRISMAProp,
  serializeCSV: serializeCSVProp,
  serializeJSONL: serializeJSONLProp,
  onRisExport,
  onBibTeXExport,
  onPRISMAExport,
  onCsvExport,
  onJsonlExport,
  children,
  onExportEvidenceCsv,
  onExportForestSvg,
}: ExportPanelProps) {
  const run = detail?.run ?? {};
  const records: any[] = (detail as any).records ?? [];
  const status = run.status ?? 'pending';
  const runId = run.id ?? null;
  const countN = records.length;

  const isExportable = EXPORTABLE_STATUSES.has(status);
  const isEmpty = countN === 0;

  const baseFilename = (ext: string) =>
    sanitizeFilename(`meda_run${runId}_${makeDateStamp()}_n${countN}.${ext}`);

  const risSerializer = serializeRISProp ?? defaultSerializeRIS;
  const bibSerializer = serializeBibTeXProp ?? defaultSerializeBibTeX;
  const prismaExporter = exportPRISMAProp ?? defaultExportPRISMA;
  const csvSerializer = serializeCSVProp ?? defaultSerializeCSV;
  const jsonlSerializer = serializeJSONLProp ?? defaultSerializeJSONL;

  const panelClass = [
    'export-panel',
    isEmpty ? 'export-panel-empty' : '',
  ].filter(Boolean).join(' ').trim();

  const handleRis = () => {
    if (onRisExport) {
      onRisExport();
      return;
    }
    try {
      const content = risSerializer(records);
      const fn = baseFilename('ris');
      downloadBlob(fn, new Blob([content], { type: 'application/x-research-info-systems;charset=utf-8' }));
      onDone?.('ris', { filename: fn, count: countN });
    } catch (err) {
      downloadDiagnosticText('RIS', err, runId, { countN, status });
      console.log('[ExportPanel] RIS export error:', err instanceof Error ? err.message : String(err));
      onDone?.('ris_error', { error: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleBib = () => {
    if (onBibTeXExport) {
      onBibTeXExport();
      return;
    }
    try {
      const content = bibSerializer(records);
      const fn = baseFilename('bib');
      downloadBlob(fn, new Blob([content], { type: 'application/x-bibtex;charset=utf-8' }));
      onDone?.('bibtex', { filename: fn, count: countN });
    } catch (err) {
      downloadDiagnosticText('BIBTEX', err, runId, { countN, status });
      console.log('[ExportPanel] BibTeX export error:', err instanceof Error ? err.message : String(err));
      onDone?.('bibtex_error', { error: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleCsv = () => {
    if (onCsvExport) {
      onCsvExport();
      return;
    }
    try {
      const content = csvSerializer(records);
      const fn = baseFilename('csv');
      downloadBlob(fn, new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' }));
      onDone?.('csv', { filename: fn, count: countN });
    } catch (err) {
      downloadDiagnosticText('CSV', err, runId, { countN, status });
      console.log('[ExportPanel] CSV export error:', err instanceof Error ? err.message : String(err));
      onDone?.('csv_error', { error: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleJsonl = () => {
    if (onJsonlExport) {
      onJsonlExport();
      return;
    }
    try {
      const content = jsonlSerializer(records);
      const fn = baseFilename('jsonl');
      downloadBlob(fn, new Blob([content], { type: 'application/x-ndjson;charset=utf-8' }));
      onDone?.('jsonl', { filename: fn, count: countN });
    } catch (err) {
      downloadDiagnosticText('JSONL', err, runId, { countN, status });
      console.log('[ExportPanel] JSONL export error:', err instanceof Error ? err.message : String(err));
      onDone?.('jsonl_error', { error: err instanceof Error ? err.message : String(err) });
    }
  };

  const handlePrisma = () => {
    if (onPRISMAExport) {
      onPRISMAExport();
      return;
    }
    (async () => {
      try {
        const { svgBlob, pngDataUrl } = await prismaExporter();
        const svgFn = baseFilename('svg');
        downloadBlob(svgFn, svgBlob);
        if (pngDataUrl) {
          const pngFn = baseFilename('png');
          downloadDataUrl(pngFn, pngDataUrl);
        }
        onDone?.('prisma', { svgFilename: svgFn, hasPng: !!pngDataUrl });
      } catch (err) {
        downloadDiagnosticText('PRISMA', err, runId, { countN, status });
        console.log('[ExportPanel] PRISMA export error:', err instanceof Error ? err.message : String(err));
        onDone?.('prisma_error', { error: err instanceof Error ? err.message : String(err) });
      }
    })();
  };

  const handleEvidenceCsv = () => {
    if (!isExportable || !onExportEvidenceCsv) return;
    onExportEvidenceCsv();
  };

  const handleForestSvg = () => {
    if (!isExportable || !onExportForestSvg) return;
    onExportForestSvg();
  };

  const emptyStyle: React.CSSProperties = isEmpty
    ? { border: '2px dashed #f59e0b', background: '#fffbeb', borderRadius: '12px', padding: '6px' }
    : {};

  const btnBase: React.CSSProperties = {
    border: '1px solid #d0d7e2',
    background: '#ffffff',
    color: '#374151',
    borderRadius: '999px',
    padding: '8px 14px',
    cursor: isExportable ? 'pointer' : 'not-allowed',
    fontSize: '13px',
    fontWeight: 600,
    opacity: isExportable ? 1 : 0.5,
  };

  return (
    <div
      data-testid="export-panel"
      className={panelClass}
      style={{ display: 'flex', gap: '6px', alignItems: 'center', ...emptyStyle }}
    >
      {children}
      <button
        data-testid="export-ris-btn"
        style={btnBase}
        disabled={!isExportable}
        onClick={handleRis}
      >
        RIS
      </button>
      <button
        data-testid="export-bibtex-btn"
        style={btnBase}
        disabled={!isExportable}
        onClick={handleBib}
      >
        BibTeX
      </button>
      <button
        data-testid="export-csv-btn"
        style={btnBase}
        disabled={!isExportable}
        onClick={handleCsv}
      >
        CSV
      </button>
      <button
        data-testid="btn-export-evidence-csv"
        style={btnBase}
        disabled={!isExportable || !onExportEvidenceCsv}
        onClick={handleEvidenceCsv}
      >
        Evidence CSV
      </button>
      <button
        data-testid="export-prisma-btn"
        style={btnBase}
        disabled={!isExportable}
        onClick={handlePrisma}
      >
        PRISMA
      </button>
      <button
        data-testid="btn-export-forest-svg"
        style={btnBase}
        disabled={!isExportable || !onExportForestSvg}
        onClick={handleForestSvg}
      >
        Forest SVG
      </button>
    </div>
  );
}

export type { ExportPanelProps };
