"""Turn static findings into developer-facing explanations: what's wrong, why
it matters, the exact fix, and a patched Dockerfile example. This is the "LLM
rewrite suggestions" layer on top of the rule engine — entirely optional, and
never required for `scan`/`pr-check` to work (those stay static-only).

Talks to any OpenAI-compatible chat-completions endpoint over plain HTTP
(no `openai` SDK dependency) — the same pattern the main LayerLens backend
uses against Featherless.ai, but configurable to point at OpenAI or anything
else that speaks the same API shape.
"""

from __future__ import annotations

import os

import requests

DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a senior engineer specializing in Docker image optimization and container "
    "security. You turn a list of static-analysis findings for a Dockerfile into a clear, "
    "actionable explanation for another developer."
)


class ExplainConfig:
    """Resolves API key/base/model from explicit args, falling back to env vars
    (OPENAI_API_KEY / LLM_API_BASE / LLM_MODEL) so it composes with however the
    rest of LayerLens is already configured."""

    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_base = api_base or os.environ.get("LLM_API_BASE", DEFAULT_API_BASE)
        self.model = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


def _build_user_prompt(dockerfile_text: str, findings) -> str:
    findings_block = "\n".join(
        f"- [{f.severity.upper()}] {f.message} (suggestion: {f.suggestion})" for f in findings
    ) or "- (no findings — the Dockerfile already looks solid)"

    return (
        "A static analysis tool found the following issues in this Dockerfile:\n\n"
        f"{findings_block}\n\n"
        "Dockerfile:\n"
        f"```dockerfile\n{dockerfile_text}\n```\n\n"
        "For each issue (most impactful first), explain: what the issue is, why it matters "
        "in practice, and the exact fix. Then give one complete, patched Dockerfile that "
        "applies all the fixes together. If you can estimate the impact (e.g. rough image "
        "size reduction, build time, or attack-surface reduction), include it briefly. "
        "Be concrete and concise — no filler."
    )


def generate_fix_explanation(dockerfile_text: str, findings, config: ExplainConfig, *, timeout: int = 60) -> str:
    if not config.is_configured:
        raise RuntimeError(
            "No API key configured for explanations. Set OPENAI_API_KEY (and optionally "
            "LLM_API_BASE/LLM_MODEL for a non-OpenAI provider), or pass --explain-key."
        )

    response = requests.post(
        f"{config.api_base.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(dockerfile_text, findings)},
            ],
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]
