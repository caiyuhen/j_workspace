
import os
import pytest
import time
from unittest.mock import MagicMock, patch
from pubmed_interface.pubmed_client import PubMedClient

# Mock .env for tests if not present, but we have it.
# However, for CI/CD or clean tests, we might want to mock env vars.
# But here we test with real key if available or mock.
# User requirement: "Test API Key works... rate limit <= 10 req/s".

@pytest.fixture
def client():
    return PubMedClient()

def test_api_key_loaded(client):
    assert client.api_key is not None

def test_rate_limit(client):
    start = time.time()
    for _ in range(5):
        client._rate_limit()
    end = time.time()
    # 5 calls * 0.11s = 0.55s minimum
    assert (end - start) >= 0.4 # Allow some buffer

@patch('pubmed_interface.pubmed_client.PubMedLoader')
def test_search_empty(mock_loader, client):
    mock_instance = MagicMock()
    mock_instance.load.return_value = []
    mock_loader.return_value = mock_instance
    
    results = client.search("nonexistentquery12345")
    assert results == []

@patch('pubmed_interface.pubmed_client.PubMedLoader')
def test_search_success(mock_loader, client):
    mock_instance = MagicMock()
    # Mock document
    doc = MagicMock()
    doc.page_content = "Abstract text"
    doc.metadata = {
        "uid": "12345",
        "Title": "Test Title",
        "Published": "2023-01-01",
        "DOI": "10.1000/test",
        "Authors": ["Author A", "Author B"] # LangChain might return list or string
    }
    mock_instance.load.return_value = [doc]
    mock_loader.return_value = mock_instance
    
    results = client.search("test query")
    assert len(results) == 1
    assert results[0]['PMID'] == "12345"
    assert results[0]['Title'] == "Test Title"

def test_fetch_details_mock(client):
    # We mock requests.Session.get for fetch_details
    with patch.object(client.session, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Minimal XML response
        mock_response.content = b"""
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345</PMID>
                    <Article>
                        <Journal>
                            <Title>Test Journal</Title>
                        </Journal>
                    </Article>
                    <MeshHeadingList>
                        <MeshHeading>
                            <DescriptorName>Lung Neoplasms</DescriptorName>
                        </MeshHeading>
                    </MeshHeadingList>
                </MedlineCitation>
                <PubmedData>
                    <ArticleIdList>
                        <ArticleId IdType="pmc">PMC12345</ArticleId>
                    </ArticleIdList>
                </PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>
        """
        mock_get.return_value = mock_response
        
        results = client.fetch_details(["12345"])
        assert len(results) == 1
        assert results[0]['PMID'] == "12345"
        assert "Lung Neoplasms" in results[0]['MeSH']
        assert results[0]['PMC_ID'] == "PMC12345"

def test_fetch_details_empty(client):
    assert client.fetch_details([]) == []

def test_fetch_details_error(client):
    with patch.object(client.session, 'get') as mock_get:
        mock_get.side_effect = Exception("Network Error")
        results = client.fetch_details(["12345"])
        # Should return empty list or partial results?
        # My implementation logs error and continues/returns what it has.
        # Since loop is per batch, if one batch fails, it returns what it has.
        # In this case, 0 results.
        assert results == []

def test_save_to_jsonl(client, tmp_path):
    data = [{"key": "value"}]
    p = tmp_path / "test.jsonl"
    client.save_to_jsonl(data, str(p))
    assert p.exists()
    with open(p, 'r') as f:
        content = f.read()
        assert '{"key": "value"}' in content

def test_save_to_jsonl_error(client):
    # Pass invalid path
    client.save_to_jsonl([], "/invalid/path/test.jsonl")
    # Should log error and not crash

