from app.services.transformers_ner import TransformersNERMapper


def test_extract_with_llm_batch_preserves_job_order_for_sparse_indices():
    mapper = object.__new__(TransformersNERMapper)

    def fake_extract_with_llm(text, client=None, original_text=None):
        return {
            "conditions": [text],
            "medications": [],
            "procedures": [],
            "measurements": [],
            "symptoms_with_values": [],
            "times": [],
            "observations": [],
            "negations": [],
            "devices": [],
            "specimens": [],
            "death": [],
            "providers": [],
            "care_sites": [],
            "note_nlp_items": [],
        }

    mapper._extract_with_llm = fake_extract_with_llm

    jobs = [(2, "文本C", "原文C"), (0, "文本A", "原文A"), (1, "文本B", "原文B")]
    results = mapper._extract_with_llm_batch(jobs, max_workers=3)

    assert results[0]["conditions"] == ["文本C"]
    assert results[1]["conditions"] == ["文本A"]
    assert results[2]["conditions"] == ["文本B"]


def test_extract_with_llm_reuses_shared_client_without_closing_it():
    mapper = object.__new__(TransformersNERMapper)
    mapper.LLM_TIMEOUT = 40.0
    mapper.LLM_URL = "http://unit-test.local/v1/chat/completions"
    mapper.LLM_MODEL = "unit-test-model"
    mapper.LLM_AUTHORIZATION = "Bearer test"
    mapper._looks_like_meaningful_residual = lambda text: True
    mapper._llm_headers = lambda: {}
    mapper._llm_payload = lambda text: {"input": text}
    mapper._parse_llm_content = lambda content, original_text=None: {
        "conditions": ["冠心病"],
        "medications": [],
        "procedures": [],
        "measurements": [],
        "symptoms_with_values": [],
        "times": [],
        "observations": [],
        "negations": [],
        "devices": [],
        "specimens": [],
        "death": [],
        "providers": [],
        "care_sites": [],
        "note_nlp_items": [],
    }

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"ok":true}'
                        }
                    }
                ]
            }

    class DummyClient:
        def __init__(self):
            self.closed = False
            self.calls = 0

        def post(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("client already closed")
            self.calls += 1
            return DummyResponse()

        def close(self):
            self.closed = True

    mapper._llm_client = DummyClient()

    first = mapper._extract_with_llm("冠心病", original_text="冠心病")
    second = mapper._extract_with_llm("冠心病", original_text="冠心病")

    assert isinstance(first, dict)
    assert isinstance(second, dict)
    assert mapper._llm_client.calls == 2
    assert mapper._llm_client.closed is False
