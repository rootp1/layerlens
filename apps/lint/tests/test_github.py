import json
import os
import subprocess

import pytest

from layerlens_lint.diff import compare
from layerlens_lint.github import (
    GitHubContextError,
    build_comment_body,
    get_event_context,
    post_pr_comment,
    read_file_at_ref,
)


def test_build_comment_body_worse_includes_findings(bad_dockerfile, good_dockerfile):
    comparison = compare(good_dockerfile, bad_dockerfile)
    body = build_comment_body(comparison, "Dockerfile")
    assert "less efficient" in body
    assert "Score:" in body
    assert str(comparison.head_score) in body


def test_build_comment_body_unchanged(bad_dockerfile):
    comparison = compare(bad_dockerfile, bad_dockerfile)
    body = build_comment_body(comparison, "Dockerfile")
    assert "No change in findings." in body


def test_post_pr_comment_calls_expected_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"id": 123}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("layerlens_lint.github.requests.post", fake_post)

    result = post_pr_comment("owner/repo", 42, "hello", "tok_123")

    assert result == {"id": 123}
    assert captured["url"] == "https://api.github.com/repos/owner/repo/issues/42/comments"
    assert captured["headers"]["Authorization"] == "Bearer tok_123"
    assert captured["json"] == {"body": "hello"}


def test_get_event_context_missing_env_raises(monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    with pytest.raises(GitHubContextError):
        get_event_context()


def test_get_event_context_reads_pr_event(tmp_path, monkeypatch):
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({
        "pull_request": {
            "number": 7,
            "base": {"ref": "main"},
            "head": {"ref": "feature/x"},
        }
    }))
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    ctx = get_event_context()
    assert ctx == {
        "repo": "owner/repo",
        "pr_number": 7,
        "base_ref": "main",
        "head_ref": "feature/x",
    }


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def test_read_file_at_ref_reads_historical_content(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)

    (repo / "Dockerfile").write_text("FROM alpine:3.18\n")
    _run_git(["add", "Dockerfile"], cwd=repo)
    _run_git(["commit", "-q", "-m", "base"], cwd=repo)

    (repo / "Dockerfile").write_text("FROM alpine:3.19\n")
    _run_git(["commit", "-q", "-am", "head"], cwd=repo)

    base_content = read_file_at_ref("HEAD~1", "Dockerfile", cwd=str(repo))
    assert base_content == "FROM alpine:3.18\n"

    with pytest.raises(FileNotFoundError):
        read_file_at_ref("HEAD", "does-not-exist", cwd=str(repo))
