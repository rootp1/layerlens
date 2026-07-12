import json
import os
import subprocess

from layerlens_lint.cli import main


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def test_scan_command_exit_code_and_json(tmp_path, bad_dockerfile, capsys):
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    exit_code = main(["scan", str(tmp_path), "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0  # no --fail-under passed
    assert len(payload["files"]) == 1
    assert payload["files"][0]["score"] < 100


def test_scan_command_fail_under(tmp_path, bad_dockerfile, capsys):
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    exit_code = main(["scan", str(tmp_path), "--fail-under", "95"])
    assert exit_code == 1

    exit_code_ok = main(["scan", str(tmp_path), "--fail-under", "0"])
    assert exit_code_ok == 0


def test_scan_command_no_dockerfiles_found(tmp_path, capsys):
    exit_code = main(["scan", str(tmp_path)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "No Dockerfiles found" in out


def test_diff_command_fail_on_worse(tmp_path, good_dockerfile, bad_dockerfile, capsys):
    base_path = tmp_path / "base.Dockerfile"
    head_path = tmp_path / "head.Dockerfile"
    _write(str(base_path), good_dockerfile)
    _write(str(head_path), bad_dockerfile)

    exit_code = main(["diff", "--base", str(base_path), "--head", str(head_path), "--fail-on-worse"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "less efficient" in out


def test_diff_command_passes_when_improved(tmp_path, bad_dockerfile, good_dockerfile):
    base_path = tmp_path / "base.Dockerfile"
    head_path = tmp_path / "head.Dockerfile"
    _write(str(base_path), bad_dockerfile)
    _write(str(head_path), good_dockerfile)

    exit_code = main(["diff", "--base", str(base_path), "--head", str(head_path), "--fail-on-worse"])
    assert exit_code == 0


def test_pr_check_with_explicit_base_ref_no_post(tmp_path, good_dockerfile, bad_dockerfile, capsys):
    repo = tmp_path
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)

    _write(str(repo / "Dockerfile"), good_dockerfile)
    _run_git(["add", "Dockerfile"], cwd=repo)
    _run_git(["commit", "-q", "-m", "base"], cwd=repo)

    _write(str(repo / "Dockerfile"), bad_dockerfile)

    exit_code = main([
        "pr-check",
        "--dockerfile", "Dockerfile",
        "--base-ref", "HEAD",
        "--fail-on-worse",
        "--cwd", str(repo),
    ])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "less efficient" in out


def test_pr_check_new_dockerfile_not_at_base_ref(tmp_path, good_dockerfile, capsys):
    repo = tmp_path
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    _write(str(repo / "README.md"), "hi\n")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-q", "-m", "init"], cwd=repo)

    _write(str(repo / "Dockerfile"), good_dockerfile)

    exit_code = main([
        "pr-check",
        "--dockerfile", "Dockerfile",
        "--base-ref", "HEAD",
        "--fail-on-worse",
        "--cwd", str(repo),
    ])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "treating as a new file" in out


def test_pr_check_posts_comment_when_worse(tmp_path, good_dockerfile, bad_dockerfile, monkeypatch, capsys):
    repo = tmp_path
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    _write(str(repo / "Dockerfile"), good_dockerfile)
    _run_git(["add", "Dockerfile"], cwd=repo)
    _run_git(["commit", "-q", "-m", "base"], cwd=repo)
    _write(str(repo / "Dockerfile"), bad_dockerfile)

    captured = {}

    def fake_post_pr_comment(repo_name, pr_number, body, token):
        captured["repo"] = repo_name
        captured["pr_number"] = pr_number
        captured["body"] = body
        captured["token"] = token
        return {"id": 1}

    monkeypatch.setattr("layerlens_lint.cli.post_pr_comment", fake_post_pr_comment)

    exit_code = main([
        "pr-check",
        "--dockerfile", "Dockerfile",
        "--base-ref", "HEAD",
        "--repo", "owner/repo",
        "--pr-number", "9",
        "--token", "tok_abc",
        "--post",
        "--fail-on-worse",
        "--cwd", str(repo),
    ])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert captured["repo"] == "owner/repo"
    assert captured["pr_number"] == 9
    assert captured["token"] == "tok_abc"
    assert "Posted comment to owner/repo#9." in out


def test_scan_command_top_n_and_categorization_in_json(tmp_path, bad_dockerfile, capsys):
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    exit_code = main(["scan", str(tmp_path), "--json", "--top-n", "2"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    prio = payload["files"][0]["prioritization"]
    assert len(prio["top_issues"]) == 2
    assert "quick_wins" in prio
    assert "advanced_improvements" in prio


def test_scan_command_explain_without_key_reports_error(tmp_path, bad_dockerfile, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    exit_code = main(["scan", str(tmp_path), "--json", "--explain"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "ai_explanation_error" in payload["files"][0]
    assert "ai_explanation" not in payload["files"][0]


def test_scan_command_explain_calls_llm_when_configured(tmp_path, bad_dockerfile, monkeypatch, capsys):
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    monkeypatch.setattr(
        "layerlens_lint.cli.generate_fix_explanation",
        lambda dockerfile_text, findings, config: "Switch to node:20-alpine and add a USER instruction.",
    )

    exit_code = main([
        "scan", str(tmp_path), "--json", "--explain", "--explain-key", "sk-test",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["files"][0]["ai_explanation"] == "Switch to node:20-alpine and add a USER instruction."


def test_scan_command_deep_reports_tool_unavailable(tmp_path, bad_dockerfile, monkeypatch, capsys):
    _write(str(tmp_path / "Dockerfile"), bad_dockerfile)

    monkeypatch.setattr(
        "layerlens_lint.cli.run_deep_analysis",
        lambda dockerfile_path, context_dir=None: {"error": "'docker' and/or 'dive' aren't available on PATH — skipping deep analysis."},
    )

    exit_code = main(["scan", str(tmp_path), "--json", "--deep"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "error" in payload["files"][0]["deep"]

