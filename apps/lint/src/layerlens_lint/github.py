"""GitHub-specific plumbing: reading CI context (which PR is this?), fetching
a file's content at a given git ref, formatting a Markdown PR comment, and
posting it via the REST API. Kept separate from diff.py so the comparison
logic itself has no GitHub/network dependency and is trivially testable.
"""

from __future__ import annotations

import json
import os
import subprocess

import requests

from .diff import ComparisonResult

GITHUB_API_URL = "https://api.github.com"


class GitHubContextError(RuntimeError):
    """Raised when the GitHub Actions event context can't be resolved."""


def get_event_context() -> dict:
    """Read GITHUB_REPOSITORY / GITHUB_EVENT_PATH (as set by GitHub Actions)
    and return {'repo': 'owner/name', 'pr_number': int, 'base_ref': str,
    'head_ref': str}. Raises GitHubContextError if run outside that context
    or the event isn't a pull_request event.
    """
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not repo or not event_path or not os.path.exists(event_path):
        raise GitHubContextError(
            "Not running inside a GitHub Actions pull_request event "
            "(GITHUB_REPOSITORY/GITHUB_EVENT_PATH not set or missing)."
        )

    with open(event_path, "r", encoding="utf-8") as fh:
        event = json.load(fh)

    pr = event.get("pull_request")
    if not pr:
        raise GitHubContextError("GitHub event payload has no 'pull_request' section.")

    return {
        "repo": repo,
        "pr_number": pr["number"],
        "base_ref": pr["base"]["ref"],
        "head_ref": pr["head"]["ref"],
    }


def read_file_at_ref(ref: str, path: str, *, cwd: str = ".") -> str:
    """Return a file's content as it existed at a given git ref, e.g.
    read_file_at_ref('origin/main', 'Dockerfile'). Raises FileNotFoundError
    if the path didn't exist at that ref."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise FileNotFoundError(f"'{path}' not found at ref '{ref}': {result.stderr.strip()}")
    return result.stdout


def build_comment_body(comparison: ComparisonResult, dockerfile_path: str) -> str:
    arrow = "📉" if comparison.verdict == "worse" else "📈" if comparison.verdict == "better" else "➡️"
    lines = [
        f"### {arrow} LayerLens Dockerfile check — `{dockerfile_path}`",
        "",
        f"**Score:** {comparison.base_score} → {comparison.head_score} "
        f"({comparison.delta:+d})",
        "",
    ]

    if comparison.verdict == "worse":
        lines.append("This change makes the Dockerfile **less efficient/secure**. New findings:")
        lines.append("")
        for f in comparison.new_findings:
            lines.append(f"- **[{f.severity.upper()}] {f.message}**\n  - _Suggestion:_ {f.suggestion}")
    elif comparison.new_findings:
        lines.append("New findings introduced in this change:")
        lines.append("")
        for f in comparison.new_findings:
            lines.append(f"- **[{f.severity.upper()}] {f.message}**\n  - _Suggestion:_ {f.suggestion}")

    if comparison.resolved_findings:
        lines.append("")
        lines.append("Findings resolved by this change:")
        lines.append("")
        for f in comparison.resolved_findings:
            lines.append(f"- ~~[{f.severity.upper()}] {f.message}~~")

    if not comparison.new_findings and not comparison.resolved_findings:
        lines.append("No change in findings.")

    lines.append("")
    lines.append("<sub>Posted automatically by layerlens-lint.</sub>")
    return "\n".join(lines)


def post_pr_comment(repo: str, pr_number: int, body: str, token: str) -> dict:
    url = f"{GITHUB_API_URL}/repos/{repo}/issues/{pr_number}/comments"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"body": body},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
