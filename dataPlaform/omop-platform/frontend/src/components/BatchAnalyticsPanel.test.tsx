import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import BatchAnalyticsPanel from './BatchAnalyticsPanel';

describe('BatchAnalyticsPanel', () => {
  it('renders incremental counters and filter controls', () => {
    render(
      <BatchAnalyticsPanel
        batches={[
          {
            id: 'batch_1',
            filename: 'delta.csv',
            total_rows: 10,
            error_rows: 1,
            status: 'completed',
            batch_type: 'incremental',
            inserted_rows: 3,
            updated_rows: 2,
            deleted_rows: 1,
            unchanged_rows: 4,
            created_at: '2026-07-15T10:00:00',
          },
        ]}
      />
    );

    expect(screen.getByText('批次分析')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('批次号')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('开始时间')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('结束时间')).toBeInTheDocument();
    expect(screen.getByText('增量批次')).toBeInTheDocument();
    expect(screen.getByText('新增 3')).toBeInTheDocument();
    expect(screen.getByText('更新 2')).toBeInTheDocument();
    expect(screen.getByText('删除 1')).toBeInTheDocument();
    expect(screen.getByText('未变化 4')).toBeInTheDocument();
  });

  it('supports export and selecting a batch for details', () => {
    const onExport = vi.fn();
    const onSelectBatch = vi.fn();

    render(
      <BatchAnalyticsPanel
        batches={[
          {
            id: 'batch_1',
            filename: 'delta.csv',
            total_rows: 10,
            error_rows: 1,
            status: 'completed',
            batch_type: 'incremental',
            inserted_rows: 3,
            updated_rows: 2,
            deleted_rows: 1,
            unchanged_rows: 4,
            created_at: '2026-07-15T10:00:00',
          },
        ]}
        onExport={onExport}
        onSelectBatch={onSelectBatch}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: '导出当前筛选' }));
    fireEvent.click(screen.getByRole('button', { name: '查看详情' }));

    expect(onExport).toHaveBeenCalledTimes(1);
    expect(onSelectBatch).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'batch_1',
        filename: 'delta.csv',
      })
    );
  });
});
