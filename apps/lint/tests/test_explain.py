import pytest

from layerlens_lint.explain import ExplainConfig, generate_fix_explanation
from layerlens_lint.rules import analyze


def test_explain_config_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    monkeypatch.setenv("LLM_API_BASE", "https://api.featherless.ai/v1")
    monkeypatch.setenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3-0324")

    config = ExplainConfig()
    assert config.api_key == "sk-env-key"
    assert config.api_base == "https://api.featherless.ai/v1"
    assert config.model == "deepseek-ai/DeepSeek-V3-0324"
    assert config.is_configured


def test_explain_config_explicit_args_override_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    config = ExplainConfig(api_key="sk-explicit")
    assert config.api_key == "sk-explicit"


def test_explain_config_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ExplainConfig()
    assert not config.is_configured


def test_generate_fix_explanation_raises_without_key():
    config = ExplainConfig(api_key=None)
    with pytest.raises(RuntimeError):
        generate_fix_explanation("FROM alpine\n", [], config)


def test_generate_fix_explanation_calls_chat_completions(monkeypatch, bad_dockerfile):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "Use a smaller base image."}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("layerlens_lint.explain.requests.post", fake_post)

    result = analyze(bad_dockerfile)
    config = ExplainConfig(api_key="sk-test", api_base="https://api.example.com/v1", model="test-model")

    text = generate_fix_explanation(bad_dockerfile, result.findings, config)

    assert text == "Use a smaller base image."
    assert captured["url"] == "https://api.example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["json"]["model"] == "test-model"
    prompt = captured["json"]["messages"][1]["content"]
    assert "FROM node:20" in prompt
    assert result.findings[0].message in prompt
