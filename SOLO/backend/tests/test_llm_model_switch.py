import json
from pathlib import Path

import pytest

from app.api.v1.conversations import ChatRequest
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_openai_model_config_routes_to_chat_completions(tmp_path, monkeypatch):
    config_path = tmp_path / "model_configs.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "cherryin-qwen3.6-plus",
                    "display_name": "CherryIn Qwen3.6 Plus",
                    "type": "openai",
                    "endpoint": "https://open.cherryin.cc/v1",
                    "api_key": "test-key",
                    "model": "agent/qwen3.6-plus",
                    "default": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {"message": {"content": "模型响应"}}
                    ],
                    "usage": {"total_tokens": 12},
                }
            ).encode("utf-8")

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    service = LLMService(config_path=config_path, timeout=300000)
    result = await service.chat(
        [{"role": "user", "content": "你好"}],
        model="cherryin-qwen3.6-plus",
    )

    assert captured["url"] == "https://open.cherryin.cc/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "agent/qwen3.6-plus"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "你好"}]
    assert result["content"] == "模型响应"
    assert result["model"] == "cherryin-qwen3.6-plus"
    assert result["raw_model"] == "agent/qwen3.6-plus"


@pytest.mark.asyncio
async def test_medical_rag_model_config_routes_to_configured_chat_endpoint(tmp_path, monkeypatch):
    config_path = tmp_path / "model_configs.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "name": "medical-rag-198",
                    "display_name": "198.168.0.214 医疗RAG",
                    "type": "medical_rag",
                    "endpoint": "http://198.168.0.214:8802",
                    "model": "medical-large",
                    "default": False,
                }
            ]
        ),
        encoding="utf-8",
    )

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "response": "医疗RAG响应",
                    "retrieved_knowledge": [{"source_type": "Milvus"}],
                    "analysis": {"ok": True},
                }
            ).encode("utf-8")

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    service = LLMService(config_path=config_path, timeout=300000)
    result = await service.chat(
        [{"role": "user", "content": "检查肝功能"}],
        model="medical-rag-198",
    )

    assert captured["url"] == "http://198.168.0.214:8802/chat"
    assert captured["payload"]["prompt"] == "检查肝功能"
    assert result["content"] == "医疗RAG响应"
    assert result["model"] == "medical-rag-198"
    assert result["raw_model"] == "medical-large"
    assert result["sources"] == [{"source_type": "Milvus"}]


def test_chat_request_accepts_optional_model():
    request = ChatRequest(message="你好", model="cherryin-qwen3.6-plus")

    assert request.model == "cherryin-qwen3.6-plus"


def test_main_chat_endpoint_directly_calls_selected_llm_without_orchestrator():
    source = Path("app/api/v1/conversations.py").read_text(encoding="utf-8")
    chat_block = source.split('@router.post("/chat", response_model=ChatResponse)', 1)[1]
    chat_block = chat_block.split('@router.post("/chat/stream")', 1)[0]

    assert "orchestrator.execute" not in chat_block
    assert "agent.execute" not in chat_block
    assert "llm_service.chat" in chat_block
    assert "model=request.model" in chat_block
