import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UploadForm from './UploadForm';
import { vi } from 'vitest';

describe('UploadForm', () => {
  beforeEach(() => {
    // Mock the global fetch
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders upload form', () => {
    render(<UploadForm onUploadSuccess={vi.fn()} />);
    expect(screen.getByText(/Upload CSV File/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
  });

  it('shows error if uploading without file', async () => {
    render(<UploadForm onUploadSuccess={vi.fn()} />);
    const button = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(button);
    // Button should be disabled now when files length is 0, so click shouldn't trigger toast.
    // We can just assert the button is disabled.
    expect(button).toBeDisabled();
  });

  it('handles successful upload', async () => {
    const mockSuccessFn = vi.fn();
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        batch_id: '123',
        filename: 'test.csv',
        total_valid_rows: 10,
        total_error_rows: 0
      }),
    });

    render(<UploadForm onUploadSuccess={mockSuccessFn} />);
    
    // Create a mock file
    const file = new File(['hello'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/Select CSV/i);
    
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));

    expect(await screen.findByText(/Upload successful/i)).toBeInTheDocument();
    expect(mockSuccessFn).toHaveBeenCalled();
  });
});
