"""Command-line entry point for layerlens-lint.

  - `layerlens scan`      repo tool: find every Dockerfile, score it, print
                          prioritized findings (top issues / quick wins /
                          advanced), optionally deepen with an LLM rewrite
                          (--explain) or a real docker build + dive pass
                          (--deep). Fails CI when a file is below --fail-under.
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

from .categorize import prioritize
from .deep import run_deep_analysis
from .diff import compare
from .explain import ExplainConfig, generate_fix_explanation
from .github import (
    GitHubContextError,
    build_comment_body,
    get_event_context,
    post_pr_comment,
    read_file_at_ref,
)
from .scanner import scan_path

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _build_file_payload(report, args) -> dict:
    payload = report.to_dict()
    payload["prioritization"] = prioritize(report.result, top_n=args.top_n).to_dict()

    if getattr(args, "deep", False):
        context_dir = args.context or os.path.dirname(os.path.abspath(report.path)) or "."
        payload["deep"] = run_deep_analysis(report.path, context_dir=context_dir)

    if getattr(args, "explain", False):
        config = ExplainConfig(api_key=args.explain_key, api_base=args.explain_base, model=args.explain_model)
        if not config.is_configured:
            payload["ai_explanation_error"] = (
                "No API key configured — set OPENAI_API_KEY or pass --explain-key."
            )
        else:
            try:
                dockerfile_text = _read_text(report.path)
                payload["ai_explanation"] = generate_fix_explanation(
                    dockerfile_text, report.result.findings, config
                )
            except Exception as exc:  # noqa: BLE001 - surface any provider/network error, don't crash the scan
                payload["ai_explanation_error"] = str(exc)

    return payload


def _print_file_report(payload: dict) -> None:
    findings = sorted(payload["findings"], key=lambda f: SEVERITY_ORDER.get(f["severity"], 9))
    print(f"\n{payload['path']}  —  score {payload['score']}/100")
    if not payload["dockerignore_present"]:
        print("  (no sibling .dockerignore found)")

    if not findings:
        print("  No issues found.")
    else:
        prio = payload["prioritization"]
        top_ids = {f["rule_id"] for f in prio["top_issues"]}

        print("  Top issues:")
        for f in prio["top_issues"]:
            print(f"    [{f['severity'].upper():8s}] {f['message']}")
            print(f"               → {f['suggestion']}")

        remaining = [f for f in findings if f["rule_id"] not in top_ids]
        if remaining:
            quick_ids = {f["rule_id"] for f in prio["quick_wins"]}
            quick_remaining = [f for f in remaining if f["rule_id"] in quick_ids]
            advanced_remaining = [f for f in remaining if f["rule_id"] not in quick_ids]

            if quick_remaining:
                print("  Other quick wins:")
                for f in quick_remaining:
                    print(f"    [{f['severity'].upper():8s}] {f['message']}")
            if advanced_remaining:
                print("  Other advanced improvements:")
                for f in advanced_remaining:
                    print(f"    [{f['severity'].upper():8s}] {f['message']}")

    if payload.get("deep"):
        deep = payload["deep"]
        if "error" in deep:
            print(f"  Deep analysis skipped: {deep['error']}")
        else:
            print(f"  Deep analysis (dive): {deep['stats']}")

    if payload.get("ai_explanation"):
        print("\n  --- AI explanation & rewrite ---")
        print("  " + payload["ai_explanation"].replace("\n", "\n  "))
    elif payload.get("ai_explanation_error"):
        print(f"  AI explanation skipped: {payload['ai_explanation_error']}")


def cmd_scan(args) -> int:
    report = scan_path(args.path)
    if not report.files:
        print(f"No Dockerfiles found under '{args.path}'.")
        return 0

    payloads = [_build_file_payload(f, args) for f in report.files]

    if args.json:
        print(json.dumps({"files": payloads}, indent=2))
    else:
        for payload in payloads:
            _print_file_report(payload)
        print(f"\nLowest score: {report.lowest_score}/100 across {len(report.files)} file(s).")

    if args.fail_under is not None and report.lowest_score < args.fail_under:
        if not args.json:
            print(f"\nFAILED: lowest score {report.lowest_score} is below --fail-under {args.fail_under}.")
        return 1
    return 0


def cmd_diff(args) -> int:
    base_text = _read_text(args.base)
    head_text = _read_text(args.head)

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

    head_text = _read_text(dockerfile_full_path)

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

    if args.explain and comparison.verdict == "worse":
        config = ExplainConfig(api_key=args.explain_key, api_base=args.explain_base, model=args.explain_model)
        if config.is_configured:
            try:
                explanation = generate_fix_explanation(head_text, comparison.new_findings, config)
                body += "\n\n---\n\n### AI-suggested fix\n\n" + explanation
            except Exception as exc:  # noqa: BLE001
                body += f"\n\n<sub>(AI explanation unavailable: {exc})</sub>"

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


def _add_explain_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--explain", action="store_true",
        help="Ask an LLM to turn findings into an explanation + patched Dockerfile (needs an API key).",
    )
    parser.add_argument("--explain-key", default=None, help="API key for --explain (default: $OPENAI_API_KEY).")
    parser.add_argument(
        "--explain-base", default=None,
        help="OpenAI-compatible API base URL for --explain (default: $LLM_API_BASE or OpenAI's).",
    )
    parser.add_argument(
        "--explain-model", default=None,
        help="Model name for --explain (default: $LLM_MODEL or 'gpt-4o-mini').",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="layerlens", description="Static Dockerfile linting and CI checks.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a Dockerfile or a directory tree for issues before building.")
    scan_p.add_argument("path", nargs="?", default=".", help="Dockerfile or directory to scan (default: cwd).")
    scan_p.add_argument("--fail-under", type=int, default=None, help="Exit non-zero if any file scores below this.")
    scan_p.add_argument("--top-n", type=int, default=3, help="How many top-impact issues to highlight (default: 3).")
    scan_p.add_argument(
        "--deep", action="store_true",
        help="Also build the image and run 'dive' against it for real layer stats (needs docker + dive).",
    )
    scan_p.add_argument("--context", default=None, help="Build context dir for --deep (default: the Dockerfile's own directory).")
    scan_p.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    _add_explain_args(scan_p)
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
    _add_explain_args(pr_p)
    pr_p.set_defaults(func=cmd_pr_check)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
