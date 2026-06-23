import { render, screen } from '@testing-library/react';
import DataSourceList from './DataSourceList';

describe('DataSourceList', () => {
  it('renders loading state initially', () => {
    render(<DataSourceList />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders data sources when provided', async () => {
    const mockSources = [
      { id: '1', name: 'Hospital A API', type: 'api', frequency: 'daily' },
      { id: '2', name: 'Hospital B CSV', type: 'csv', frequency: 'manual' }
    ];
    
    // We will pass them as props for the sake of simple testing, or mock fetch.
    render(<DataSourceList initialData={mockSources} isLoading={false} />);
    expect(screen.getByText(/Hospital A API/i)).toBeInTheDocument();
    expect(screen.getByText(/Hospital B CSV/i)).toBeInTheDocument();
  });
});
