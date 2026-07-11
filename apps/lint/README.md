# layerlens-lint

Static Dockerfile analysis, installable as a Python package. Two features, no
Docker daemon required for either — everything works purely from Dockerfile
*text*, which is what lets it run before an image is ever built:

1. **Repo scanner** — find every Dockerfile in a repo and print a score +
   concrete suggested fixes, before build.
2. **CI/CD PR assistant** — compare a Dockerfile's PR base vs. head and
   (optionally) post a GitHub PR comment when it got worse.

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
layerlens scan . --json               # machine-readable output
```

Example output:

```
apps/api/Dockerfile  —  score 62/100
  [HIGH    ] Base image 'node:20' doesn't look like a slim/alpine/distroless variant.
             → Consider a smaller base, e.g. an '-alpine' or '-slim' tag for 'node', or a distroless runtime image.
  [MEDIUM  ] Found 'COPY . .' (or 'ADD . .') copying the entire build context into the image.
             → Copy only what's needed (e.g. package manifests first, then source), and add a .dockerignore...
  [HIGH    ] No USER instruction switches the container away from root.
             → Create a dedicated non-root user and switch to it with a USER instruction...
```

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
      - run: layerlens pr-check --dockerfile Dockerfile --post --fail-on-worse
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

`pr-check` auto-detects the base ref, repo, and PR number from the GitHub
Actions event payload — you only need `--repo`/`--pr-number`/`--base-ref` when
running it outside that context (e.g. locally, for testing).

## As a library

```python
from layerlens_lint import analyze, compare

result = analyze(open("Dockerfile").read())
print(result.score, [f.message for f in result.findings])

comparison = compare(base_text, head_text)
print(comparison.verdict)  # 'better' | 'worse' | 'unchanged'
```
