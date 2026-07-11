"""Command-line entry point for layerlens-lint.

Two features, one package:
  - `layerlens scan`      repo tool: scan Dockerfile(s), print findings + score,
                          optionally fail CI when a file is below --fail-under.
  - `layerlens pr-check`  CI/CD assistant: compare a Dockerfile's base ref vs.
                          its current (head) content and, on GitHub Actions,
                          post a PR comment when it got worse.
  - `layerlens diff`      the same comparison as pr-check, but against two
                          plain files — useful outside GitHub Actions/for testing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .diff import compare
from .github import (
    GitHubContextError,
    build_comment_body,
    get_event_context,
    post_pr_comment,
    read_file_at_ref,
)
from .scanner import scan_path

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _print_file_report(report, use_json: bool) -> None:
    if use_json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    findings = sorted(report.result.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
    print(f"\n{report.path}  —  score {report.result.score}/100")
    if not report.dockerignore_present:
        print("  (no sibling .dockerignore found)")
    if not findings:
        print("  No issues found.")
        return
    for f in findings:
        print(f"  [{f.severity.upper():8s}] {f.message}")
        print(f"             → {f.suggestion}")


def cmd_scan(args) -> int:
    report = scan_path(args.path)
    if not report.files:
        print(f"No Dockerfiles found under '{args.path}'.")
        return 0

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for file_report in report.files:
            _print_file_report(file_report, use_json=False)
        print(f"\nLowest score: {report.lowest_score}/100 across {len(report.files)} file(s).")

    if args.fail_under is not None and report.lowest_score < args.fail_under:
        if not args.json:
            print(f"\nFAILED: lowest score {report.lowest_score} is below --fail-under {args.fail_under}.")
        return 1
    return 0


def cmd_diff(args) -> int:
    with open(args.base, "r", encoding="utf-8") as fh:
        base_text = fh.read()
    with open(args.head, "r", encoding="utf-8") as fh:
        head_text = fh.read()

    comparison = compare(base_text, head_text, tolerance=args.tolerance)

    if args.json:
        print(json.dumps(comparison.to_dict(), indent=2))
    else:
        print(build_comment_body(comparison, dockerfile_path=args.head))

    if args.fail_on_worse and comparison.verdict == "worse":
        return 1
    return 0


def cmd_pr_check(args) -> int:
    dockerfile_path = args.dockerfile
    dockerfile_full_path = os.path.join(args.cwd, dockerfile_path)
    if not os.path.exists(dockerfile_full_path):
        print(f"'{dockerfile_path}' doesn't exist in this checkout — nothing to check.")
        return 0

    with open(dockerfile_full_path, "r", encoding="utf-8") as fh:
        head_text = fh.read()

    base_ref = args.base_ref
    repo = args.repo
    pr_number = args.pr_number

    if base_ref is None or (args.post and (repo is None or pr_number is None)):
        try:
            ctx = get_event_context()
        except GitHubContextError as exc:
            print(f"error: {exc}", file=sys.stderr)
            print(
                "Pass --base-ref explicitly (and --repo/--pr-number if using --post) "
                "when not running inside a GitHub Actions pull_request event.",
                file=sys.stderr,
            )
            return 2
        base_ref = base_ref or f"origin/{ctx['base_ref']}"
        repo = repo or ctx["repo"]
        pr_number = pr_number or ctx["pr_number"]

    try:
        base_text = read_file_at_ref(base_ref, dockerfile_path, cwd=args.cwd)
    except FileNotFoundError:
        print(f"'{dockerfile_path}' didn't exist at '{base_ref}' — treating as a new file (no comparison).")
        return 0

    comparison = compare(base_text, head_text, tolerance=args.tolerance)
    body = build_comment_body(comparison, dockerfile_path=dockerfile_path)
    print(body)

    if args.post and comparison.verdict == "worse":
        token = args.token or os.environ.get("GITHUB_TOKEN")
        if not token:
            print("error: --post requires a token (--token or $GITHUB_TOKEN).", file=sys.stderr)
            return 2
        post_pr_comment(repo, pr_number, body, token)
        print(f"\nPosted comment to {repo}#{pr_number}.")

    if args.fail_on_worse and comparison.verdict == "worse":
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="layerlens", description="Static Dockerfile linting and CI checks.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a Dockerfile or a directory tree for issues before building.")
    scan_p.add_argument("path", nargs="?", default=".", help="Dockerfile or directory to scan (default: cwd).")
    scan_p.add_argument("--fail-under", type=int, default=None, help="Exit non-zero if any file scores below this.")
    scan_p.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    scan_p.set_defaults(func=cmd_scan)

    diff_p = sub.add_parser("diff", help="Compare two Dockerfile files directly (no git/GitHub needed).")
    diff_p.add_argument("--base", required=True, help="Path to the 'before' Dockerfile.")
    diff_p.add_argument("--head", required=True, help="Path to the 'after' Dockerfile.")
    diff_p.add_argument("--tolerance", type=int, default=0, help="Score-point tolerance before calling it 'worse'.")
    diff_p.add_argument("--fail-on-worse", action="store_true", help="Exit non-zero if the head is worse.")
    diff_p.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    diff_p.set_defaults(func=cmd_diff)

    pr_p = sub.add_parser("pr-check", help="Compare a Dockerfile's PR base vs. head; optionally comment on the PR.")
    pr_p.add_argument("--dockerfile", default="Dockerfile", help="Path to the Dockerfile in this checkout.")
    pr_p.add_argument("--base-ref", default=None, help="Git ref to diff against (default: resolved from GH Actions event).")
    pr_p.add_argument("--repo", default=None, help="owner/repo (default: resolved from GH Actions event).")
    pr_p.add_argument("--pr-number", type=int, default=None, help="PR number (default: resolved from GH Actions event).")
    pr_p.add_argument("--token", default=None, help="GitHub token for posting (default: $GITHUB_TOKEN).")
    pr_p.add_argument("--tolerance", type=int, default=0, help="Score-point tolerance before calling it 'worse'.")
    pr_p.add_argument("--post", action="store_true", help="Actually post a PR comment when it got worse.")
    pr_p.add_argument("--fail-on-worse", action="store_true", help="Exit non-zero if the Dockerfile got worse.")
    pr_p.add_argument("--cwd", default=".", help="Git repo root to run 'git show' from (default: cwd).")
    pr_p.set_defaults(func=cmd_pr_check)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
