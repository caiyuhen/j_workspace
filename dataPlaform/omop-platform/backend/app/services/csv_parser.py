import csv
import chardet
from typing import Dict, Any, Generator

class CSVParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.encoding = self._detect_encoding()
        self.delimiter = self._detect_delimiter()

    def _detect_encoding(self) -> str:
        """Detect the encoding of the CSV file, with BOM awareness."""
        with open(self.file_path, 'rb') as f:
            raw_data = f.read(100000)
            
            # Fast check for UTF-8 BOM
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
                
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'utf-8'
            
            if encoding and encoding.lower() in ('gb2312', 'gbk', 'gb18030'):
                encoding = 'gb18030' # gb18030 is the superset
            return encoding

    def _detect_delimiter(self) -> str:
        """Detect the delimiter used in the CSV file with robust fallback."""
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                sample = f.read(4096)
                if not sample.strip():
                    return ','
                dialect = csv.Sniffer().sniff(sample, delimiters=[',', '\t', '|', ';', '^'])
                return dialect.delimiter
        except Exception:
            return ','  # Fallback to default comma

    def _normalize_headers(self, headers: list) -> list:
        """Clean headers by stripping whitespace and removing invisible chars."""
        return [str(h).strip().replace('\ufeff', '') for h in headers]

    def parse_chunks(self, chunk_size: int = 10000) -> Generator[Dict[str, Any], None, None]:
        """
        Parse the CSV file in chunks.
        Yields a dictionary containing 'valid_rows' and 'error_rows'.
        """
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            
            try:
                raw_headers = next(reader)
                headers = self._normalize_headers(raw_headers)
            except StopIteration:
                return  # Empty file
                
            expected_cols = len(headers)
            current_chunk_valid = []
            current_chunk_errors = []
            
            for row_idx, row in enumerate(reader, start=2):
                # Ignore completely empty rows
                if not row or (len(row) == 1 and row[0].strip() == ''):
                    continue

                if len(row) != expected_cols:
                    current_chunk_errors.append({
                        "line_number": row_idx,
                        "raw_data": row,
                        "error": f"列数不匹配：期望 {expected_cols} 列，实际读取到 {len(row)} 列"
                    })
                else:
                    # Additional Type Inference/Validation could happen here before saving
                    # For now, just save as string mappings
                    current_chunk_valid.append(dict(zip(headers, row)))
                
                # Yield when we hit the chunk size
                if (len(current_chunk_valid) + len(current_chunk_errors)) >= chunk_size:
                    yield {
                        "valid_rows": current_chunk_valid,
                        "error_rows": current_chunk_errors
                    }
                    current_chunk_valid = []
                    current_chunk_errors = []
                    
            # Yield any remaining rows
            if current_chunk_valid or current_chunk_errors:
                yield {
                    "valid_rows": current_chunk_valid,
                    "error_rows": current_chunk_errors
                }
