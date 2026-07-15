import { render, screen } from '@testing-library/react';
import BatchHistory from './BatchHistory';
import { vi } from 'vitest';

describe('BatchHistory', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading state initially', () => {
    render(<BatchHistory batches={[]} loading={true} error={null} />);
    expect(screen.getByText('正在加载历史记录...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<BatchHistory batches={[]} loading={false} error="Failed to load" />);
    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
  });

  it('renders batch data correctly', () => {
    const mockBatches = [
      {
        id: '1',
        filename: 'hospital_a.csv',
        total_rows: 100,
        error_rows: 2,
        status: 'completed',
        created_at: '2026-06-23T10:00:00Z'
      }
    ];

    render(<BatchHistory batches={mockBatches} loading={false} error={null} />);
    
    expect(screen.getByText('hospital_a.csv')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /数据分布探查/i })).toBeInTheDocument();
  });

  it('keeps rendering history rows when incremental metadata is present', () => {
    const mockBatches = [
      {
        id: 'batch_1',
        filename: 'delta.csv',
        total_rows: 10,
        error_rows: 1,
        status: 'completed',
        created_at: '2026-07-15T10:00:00Z',
        batch_type: 'incremental',
        inserted_rows: 3,
        updated_rows: 2,
        deleted_rows: 1,
        unchanged_rows: 4,
      }
    ];

    render(<BatchHistory batches={mockBatches} loading={false} error={null} />);

    expect(screen.getByText('delta.csv')).toBeInTheDocument();
    expect(screen.getByText('接入历史批次')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /数据分布探查/i })).toBeInTheDocument();
  });
});
