from __future__ import annotations

from typing import Final

from .protocol import SourceAdapter
from .pubmed_adapter import PubMedAdapter, _load_preset_50k
from .cnki_adapter import CnkiAdapter
from .wanfang_adapter import WanfangAdapter


_REGISTRY: Final[dict[str, SourceAdapter]] = {
    "pubmed": PubMedAdapter(),
    "cnki": CnkiAdapter(),
    "wanfang": WanfangAdapter(),
}


def get_source_adapter(source_key: str) -> SourceAdapter:
    if source_key not in _REGISTRY:
        raise KeyError(f"adapter for source_key={source_key!r} not registered")
    return _REGISTRY[source_key]
