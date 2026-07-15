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
    expect(screen.getByText('多模态数据上传')).toBeInTheDocument();
    expect(screen.getByLabelText('选择 CSV / DICOM 文件')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '上传并自动处理' })).toBeInTheDocument();
  });

  it('shows error if uploading without file', async () => {
    render(<UploadForm onUploadSuccess={vi.fn()} />);
    const button = screen.getByRole('button', { name: '上传并自动处理' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
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
    
    const file = new File(['hello'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText('选择 CSV / DICOM 文件');
    
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: '上传并自动处理' }));

    await waitFor(() => {
      expect(mockSuccessFn).toHaveBeenCalledWith('123');
    });
  });
});
