import { render, screen, waitFor } from '@testing-library/react';
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
    expect(screen.getByText(/Loading batches.../i)).toBeInTheDocument();
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
    expect(screen.getByText('completed')).toBeInTheDocument();
  });
});
