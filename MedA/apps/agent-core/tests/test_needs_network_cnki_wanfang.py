import pytest

from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
from app.services.sources.cnki_adapter import CnkiAdapter
from app.services.sources.wanfang_adapter import WanfangAdapter

pytestmark = pytest.mark.needs_network


@pytest.fixture()
def run_ctx():
    return SearchRunContext(
        search_run_id=9999,
        project_id=42,
    )


class TestRealCNKI3Queries:
    @pytest.fixture
    def adapter(self, monkeypatch):
        monkeypatch.setenv("MEDA_PUBMED_MODE", "force_real")
        monkeypatch.setenv("MEDA_CNKI_MODE", "force_real")
        return CnkiAdapter()

    @pytest.mark.parametrize(
        "bt",
        [
            "SGLT2i+CKD+RCT",
            "dapagliflozin+HFrEF",
            "metformin+prediabetes+lifestyle",
        ],
    )
    async def test_cnki_query_hits_ge_1(self, adapter, run_ctx, bt):
        run_ctx.search_query = NormalizedSearchQuery(
            boolean_text=bt,
            max_pages_cn=1,
            filters={},
            source_key="cnki",
        )
        result = await adapter.run_search(run_ctx.search_query, run_ctx)
        assert result.hits_on_source >= 1
        assert len(result.records) >= 1


class TestRealWanFang3Queries:
    @pytest.fixture
    def adapter(self, monkeypatch):
        monkeypatch.setenv("MEDA_PUBMED_MODE", "force_real")
        monkeypatch.setenv("MEDA_WANFANG_MODE", "force_real")
        return WanfangAdapter()

    @pytest.mark.parametrize(
        "bt",
        [
            "SGLT2i+CKD+RCT",
            "dapagliflozin+HFrEF",
            "metformin+prediabetes+lifestyle",
        ],
    )
    async def test_wanfang_query_hits_ge_1(self, adapter, run_ctx, bt):
        run_ctx.search_query = NormalizedSearchQuery(
            boolean_text=bt,
            max_pages_cn=1,
            filters={},
            source_key="wanfang",
        )
        result = await adapter.run_search(run_ctx.search_query, run_ctx)
        assert result.hits_on_source >= 1
        assert len(result.records) >= 1
