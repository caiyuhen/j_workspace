import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import React from 'react';
import { ExportPanel } from '../export/ExportPanel';

function makeDetail(overrides: any = {}) {
  const base = {
    run: {
      id: 123,
      status: 'completed',
      total_hits_raw: 100,
      total_after_dedupe: 80,
      prisma: {
        identification: 80,
        screening: 60,
        eligibility: 40,
        included: 20,
        by_source: [],
      },
      created_at: '2026-08-14T10:00:00Z',
    },
    sources: [
      {
        source_key: 'pubmed',
        source_label: 'PubMed',
        records_retrieved: 50,
        records_imported: 40,
        status: 'completed',
      },
      {
        source_key: 'cnki',
        source_label: 'CNKI',
        records_retrieved: 50,
        records_imported: 40,
        status: 'completed',
      },
    ],
    records: [
      {
        id: '1',
        title: 'Test Paper 1',
        authors: ['Alice', 'Bob'],
        journal: 'Nature',
        year: 2024,
        source: 'pubmed',
      },
      {
        id: '2',
        title: 'Test Paper 2',
        authors: ['Charlie'],
        journal: 'Science',
        year: 2023,
        source: 'cnki',
      },
    ],
  };
  return { ...base, ...overrides, run: { ...base.run, ...(overrides.run ?? {}) } };
}

const realDateNow = Date.now;
const realToISO = Date.prototype.toISOString;

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-08-14T12:00:00Z'));
});
afterEach(() => {
  vi.useRealTimers();
  Date.now = realDateNow;
  Date.prototype.toISOString = realToISO;
});

describe('ExportPanel L3 4 smoke tests', () => {
  it('T4.1 disabled 规则: status=pending 时 3 按钮全部 disabled 属性=true', () => {
    const detail = makeDetail({ run: { status: 'pending' } });
    render(<ExportPanel detail={detail} />);
    const risBtn = screen.getByTestId('export-ris-btn');
    const bibBtn = screen.getByTestId('export-bibtex-btn');
    const prismaBtn = screen.getByTestId('export-prisma-btn');
    expect(risBtn).toBeDisabled();
    expect(bibBtn).toBeDisabled();
    expect(prismaBtn).toBeDisabled();
  });

  it('T4.2 records=0 时外框 export-panel-empty className 存在但按钮仍可点击', () => {
    const detail = makeDetail({ records: [] });
    const { container } = render(<ExportPanel detail={detail} />);
    const panel = container.firstChild as HTMLElement;
    expect(panel.className).toContain('export-panel-empty');
    const risBtn = screen.getByTestId('export-ris-btn');
    const bibBtn = screen.getByTestId('export-bibtex-btn');
    const prismaBtn = screen.getByTestId('export-prisma-btn');
    expect(risBtn).not.toBeDisabled();
    expect(bibBtn).not.toBeDisabled();
    expect(prismaBtn).not.toBeDisabled();
  });

  it('T4.3 click RIS 按钮调 props.serializeRIS 恰好 1 次, 传 records 数组', () => {
    const serializeRIS = vi.fn().mockReturnValue('RIS DATA');
    const detail = makeDetail();
    render(<ExportPanel detail={detail} serializeRIS={serializeRIS} />);
    const risBtn = screen.getByTestId('export-ris-btn');
    fireEvent.click(risBtn);
    expect(serializeRIS).toHaveBeenCalledTimes(1);
    expect(serializeRIS).toHaveBeenCalledWith(detail.records);
  });

  it('T4.4 throw 走 E6 兜底: serializeRIS throw 时 window.onerror 触发 0 次 (被 try/catch 吞掉)', () => {
    const serializeRIS = vi.fn().mockImplementation(() => {
      throw new Error('BOOM RIS');
    });
    const onerror = vi.fn();
    const prevOnError = window.onerror;
    window.onerror = onerror;
    try {
      const detail = makeDetail();
      render(<ExportPanel detail={detail} serializeRIS={serializeRIS} />);
      const risBtn = screen.getByTestId('export-ris-btn');
      fireEvent.click(risBtn);
      expect(onerror).toHaveBeenCalledTimes(0);
    } finally {
      window.onerror = prevOnError;
    }
  });
});
