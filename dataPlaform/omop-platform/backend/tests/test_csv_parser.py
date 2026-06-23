import pytest
import os
import tempfile
from app.services.csv_parser import CSVParser

@pytest.fixture
def create_temp_csv():
    """Helper to create a temporary CSV file and return its path."""
    paths = []
    def _create(content: bytes):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
        paths.append(path)
        return path
        
    yield _create
    
    # Cleanup
    for p in paths:
        if os.path.exists(p):
            os.remove(p)

def test_detect_encoding_utf8_bom(create_temp_csv):
    # CSV with UTF-8 BOM
    content = b'\xef\xbb\xbfname,age\nAlice,30\n'
    path = create_temp_csv(content)
    parser = CSVParser(path)
    assert parser.encoding == 'utf-8-sig'

def test_detect_encoding_gbk(create_temp_csv):
    # CSV with GBK encoding
    content = '姓名,年龄\n张三,30\n'.encode('gbk')
    path = create_temp_csv(content)
    parser = CSVParser(path)
    assert parser.encoding == 'gb18030'

def test_normalize_headers(create_temp_csv):
    content = b' id , name \n1,Alice\n'
    path = create_temp_csv(content)
    parser = CSVParser(path)
    chunks = list(parser.parse_chunks())
    
    assert len(chunks) == 1
    assert len(chunks[0]['valid_rows']) == 1
    # Headers should be stripped of spaces
    assert 'id' in chunks[0]['valid_rows'][0]
    assert 'name' in chunks[0]['valid_rows'][0]
    assert ' id ' not in chunks[0]['valid_rows'][0]

def test_missing_columns(create_temp_csv):
    content = b'id,name,age\n1,Alice,30\n2,Bob\n3,Charlie,25\n'
    path = create_temp_csv(content)
    parser = CSVParser(path)
    chunks = list(parser.parse_chunks())
    
    assert len(chunks) == 1
    assert len(chunks[0]['valid_rows']) == 2
    assert len(chunks[0]['error_rows']) == 1
    assert chunks[0]['error_rows'][0]['line_number'] == 3
    assert '列数不匹配' in chunks[0]['error_rows'][0]['error']
