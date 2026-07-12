# layerlens-lint

**Product vision:** lint + optimize Dockerfiles across a repo, explain fixes clearly, and
enforce container best practices before builds ship — not another paste-your-Dockerfile
web form. A developer points this at a repo; it says "I found 3 container builds, here's
what's risky or wasteful, here's the exact fix, here's a patched Dockerfile."

Static analysis is the foundation (no Docker daemon, no image pull, no build — works on a
bare Dockerfile diff in CI), with two optional deeper layers on top:

1. **Repo scanner** — find every Dockerfile in a repo, score each one, prioritize findings
   (top-impact issues, quick wins vs. advanced improvements), before anything builds.
2. **CI/CD PR assistant** — compare a Dockerfile's PR base vs. head and (optionally) post a
   GitHub PR comment when it got worse, failing the build if you want.
3. **AI rewrite suggestions** (`--explain`) — turn findings into "what's wrong / why it
   matters / exact fix / patched Dockerfile" using any OpenAI-compatible LLM. Opt-in; never
   required for scanning or CI gating.
4. **Deep analysis** (`--deep`) — if Docker + `dive` are available, actually build the image
   and run `dive` against it for real layer-efficiency numbers, layered on top of (not
   instead of) the static findings.

One engine, four surfaces: CLI output, CI logs, GitHub PR comments, and JSON for automation.

## Install

```bash
pip install .           # from this directory
# or, once published:
pip install layerlens-lint
```

## 1. Scan a repo before building

```bash
layerlens scan .                      # scan every Dockerfile under the cwd
layerlens scan path/to/Dockerfile     # scan a single file
layerlens scan . --fail-under 60      # exit 1 if any file scores below 60
layerlens scan . --top-n 3            # how many top-impact issues to call out (default 3)
layerlens scan . --json               # machine-readable output
```

Example output:

```
apps/api/Dockerfile  —  score 62/100
  Top issues:
    [HIGH    ] Base image 'node:20' doesn't look like a slim/alpine/distroless variant.
               → Consider a smaller base, e.g. an '-alpine' or '-slim' tag for 'node', or a distroless runtime image.
    [HIGH    ] No USER instruction switches the container away from root.
               → Create a dedicated non-root user and switch to it with a USER instruction...
    [MEDIUM  ] Found 'COPY . .' (or 'ADD . .') copying the entire build context into the image.
               → Copy only what's needed (e.g. package manifests first, then source)...
  Other quick wins:
    [LOW     ] npm install/ci runs without clearing the npm cache or excluding dev dependencies.
```

`--json` includes a `prioritization` object per file: `top_issues`, `quick_wins`, and
`advanced_improvements` — the same split, structured for tooling.

### Turn findings into an AI-written fix (`--explain`)

```bash
export OPENAI_API_KEY=...            # or any OpenAI-compatible provider
export LLM_API_BASE=https://api.featherless.ai/v1   # optional, defaults to OpenAI
export LLM_MODEL=deepseek-ai/DeepSeek-V3-0324        # optional

layerlens scan . --explain
```

For each finding, the LLM explains what's wrong, why it matters, the exact fix, and returns
one complete patched Dockerfile applying all the fixes together. This never runs unless you
pass `--explain` and a key is configured — `scan` and `pr-check` stay fully static (and free)
by default.

### Real build-time stats (`--deep`)

```bash
layerlens scan . --deep    # needs `docker` and `dive` on PATH
```

Builds the image from each Dockerfile and runs `dive` against it, merging real efficiency/
wasted-bytes numbers into the report. Skips gracefully (with a clear message, not an error)
when Docker/dive aren't available — most CI runners and most repo scans won't have them, and
that's fine; the static findings already cover most of what matters before a build even runs.

## 2. Comment on PRs when a Dockerfile gets worse

Two ways to use it:

**Directly, with two files** (works anywhere, no GitHub/git needed):

```bash
layerlens diff --base old/Dockerfile --head new/Dockerfile --fail-on-worse
```

**Inside GitHub Actions**, on a `pull_request` trigger:

```yaml
# .github/workflows/dockerfile-check.yml
name: Dockerfile check
on: pull_request

jobs:
  layerlens:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # need base branch history for `git show`
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install layerlens-lint
      - run: layerlens pr-check --dockerfile Dockerfile --post --fail-on-worse --explain
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

`pr-check` auto-detects the base ref, repo, and PR number from the GitHub Actions event
payload — you only need `--repo`/`--pr-number`/`--base-ref` when running it outside that
context (e.g. locally, for testing). Add `--explain` to have the PR comment include an
AI-written fix for whatever regressed, not just the static finding.

## 3. Shift-left: pre-commit / pre-push

`layerlens scan` is a plain CLI with a meaningful exit code, so it drops into any git hook:

```bash
#!/bin/sh
# .git/hooks/pre-push
layerlens scan . --fail-under 50 || exit 1
```

## As a library

```python
from layerlens_lint import analyze, compare, prioritize

result = analyze(open("Dockerfile").read())
print(result.score, [f.message for f in result.findings])

prio = prioritize(result, top_n=3)
print(prio.top_issues, prio.quick_wins, prio.advanced_improvements)

comparison = compare(base_text, head_text)
print(comparison.verdict)  # 'better' | 'worse' | 'unchanged'
```
