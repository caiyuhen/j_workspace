import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';

vi.mock('./components/DataSourceList', () => ({
  default: () => <div>数据源列表</div>,
}));

vi.mock('./components/UploadForm', () => ({
  default: () => <div>上传表单</div>,
}));

vi.mock('./components/BatchHistory', () => ({
  default: () => <div>批次历史</div>,
}));

vi.mock('./components/BatchAnalyticsPanel', () => ({
  default: () => <div>批次分析</div>,
}));

vi.mock('./components/PipelineMonitor', () => ({
  PipelineMonitor: () => <div>管线监控</div>,
}));

vi.mock('./components/QualityReport', () => ({
  QualityReport: () => <div>质量报告</div>,
}));

vi.mock('./components/ProfilingReport', () => ({
  ProfilingReport: () => <div>画像报告</div>,
}));

vi.mock('@/components/ui/sonner', () => ({
  Toaster: () => null,
}));

describe('App', () => {
  it('does not render batch analytics panel in ingestion workspace', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('上传表单')).toBeInTheDocument();
    });

    expect(screen.getByText('批次历史')).toBeInTheDocument();
    expect(screen.queryByText('批次分析')).not.toBeInTheDocument();

    vi.restoreAllMocks();
  });
});
