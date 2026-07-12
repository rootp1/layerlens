# LayerLens — 5–7 Minute Demo Script

Live app: https://layerlens-web.vercel.app
Repo: https://github.com/rootp1/layerlens

Two things to have open before you start:
- A browser tab on **https://layerlens-web.vercel.app**
- A terminal, `cd`'d into the `layerlens` repo, with `apps/lint/.venv` activated
  (`source apps/lint/.venv/bin/activate`) so the `layerlens` CLI is on PATH

Total runtime: ~6 minutes. Timestamps are cumulative, not per-section.

---

## 0:00 – 0:30 · Cold open (hook)

**[Show: your face / a blank terminal — no app yet]**

**SAY:**
> "Every team has a Dockerfile nobody's looked at in eight months. It's slow to build, the
> image is way bigger than it needs to be, and it's probably running as root. Nobody notices
> until a deploy takes forever or a security scan flags it.
>
> I built LayerLens to catch that stuff automatically — both as a website you can point at a
> running image, and as a dev tool that lints every Dockerfile in your repo before you even
> build, and comments on your PRs when a change makes things worse. Let me show you both."

---

## 0:30 – 2:30 · The web app (live image analysis)

**[Show: browser, https://layerlens-web.vercel.app — the home page]**

**SAY:**
> "This is the web side. You give it an image name and its Dockerfile, and it actually runs
> Dive — a real layer-analysis tool — against the image, then hands that report to an AI
> model to explain what's wrong and rewrite the Dockerfile."

**[Click "Launch Optimizer" → lands on /console]**

**SAY:**
> "Let's use something real — the actual backend Dockerfile from this project."

**[Type into "Image Name": `node:20`]**
**[Click "insert example" to fill the Dockerfile field, or paste a small real Dockerfile]**

**SAY (while it's typed in):**
> "This is deliberately a bit sloppy — full `node:20` base image, `COPY . .`, no non-root
> user. Let's see what it finds."

**[Click "Run Analysis ▸"]**

**[While loading — ~15-20s real wait]**

**SAY:**
> "While that's running: under the hood, this hits a Flask backend that shells out to Dive
> to inspect the image's layers, then sends that report to Featherless.ai — that's the LLM
> provider — to generate the actual advice. It's not fabricated; that's a live model call
> happening right now."

**[Results appear — point at the stat tiles]**

**SAY:**
> "Efficiency score, wasted bytes, and here's the AI's actual write-up."

**[Click "View Full Analysis"]**

**SAY:**
> "Issue, why it matters, and a rewritten Dockerfile you can paste straight back in. This
> is the human-facing side of the product."

**[Optional, if time allows: click "Lint" in the nav → paste a Dockerfile → instant score,
no Docker needed]**

**SAY:**
> "There's also a Lint tab that runs pure static analysis — no image, no Docker daemon,
> instant. That's actually the same engine I want to show you next, because that's where I
> think the real value is."

---

## 2:30 – 5:30 · The real product: `layerlens-lint` (CLI + CI)

**[Show: terminal]**

**SAY:**
> "Here's my honest take: a web form you paste a Dockerfile into is a nice demo, but it's
> not how engineers actually work. So I built the same rule engine as a standalone Python
> package — `layerlens-lint` — that fits into how a repo actually gets built."

**[Run:]**
```bash
layerlens scan apps/api/Dockerfile
```

**SAY (while it runs — this is instant):**
> "No image build. No Docker daemon. It just reads the Dockerfile text and runs about a
> dozen static rules — fat base images, missing multi-stage builds, root user, unclean
> package caches, secrets copied into the image, and so on."

**[Point at output on screen: score 87/100, Top issues: root user, no healthcheck]**

**SAY:**
> "It gives a score, and — this is the part I care about — it doesn't just dump every
> finding on you. It ranks the top 3 highest-impact issues first, and splits the rest into
> quick wins versus advanced improvements. That's the difference between a linter and a
> tool a team will actually use."

**[Run:]**
```bash
layerlens scan . 
```

**SAY:**
> "Point it at the whole repo and it finds every Dockerfile automatically — no manual
> pointing at files. That's the 'repo tool' half of the vision: it scans a codebase and
> tells you what's risky before anything ships."

**[Now show the AI layer — run:]**
```bash
layerlens scan apps/api/Dockerfile --explain
```

**SAY (while waiting ~15-20s):**
> "Same static findings, but now add `--explain` and it calls an LLM — same Featherless
> integration as the website — to turn each finding into: what's wrong, why it matters, the
> exact fix, and one complete patched Dockerfile. This is opt-in — scanning and CI gating
> never require an API key or cost anything by default. The AI is a layer on top, not a
> dependency."

**[Let the explanation print — point at the patched Dockerfile in the output]**

**SAY:**
> "That's a real Featherless call happening live, not canned text."

**[Show the GitHub Actions workflow file:]**
```bash
cat .github/workflows/dockerfile-check.yml
```

**SAY:**
> "And this is the CI/CD assistant piece — on every pull request, it diffs the Dockerfile
> against the PR's base branch. If a change makes it worse — say someone adds `COPY .env`
> or drops the non-root user — it posts a comment on the PR explaining exactly what
> regressed, and fails the build. It's a real GitHub PR comment via the API, not a
> notification — it shows up right in the review, where the fix actually needs to happen."

**[Optional — if you have a real PR to show, open it. Otherwise, narrate:]**

**SAY:**
> "I tested this against this repo's actual backend Dockerfile — added a hardcoded secret
> copy to simulate a bad PR, and it caught the score drop from 87 to 67 and flagged the
> exact line, then I reverted it. That's the loop: catch it before merge, not after
> deploy."

---

## 5:30 – 6:00 · Close

**[Show: either app back on screen, or terminal]**

**SAY:**
> "So the full picture: one static rule engine, four surfaces — a website for quick,
> human-facing checks; a CLI you can run locally or in a pre-commit hook; CI integration
> that comments on PRs and fails builds on regressions; and JSON output for anything else
> you want to automate. The AI layer is there when you want a written explanation and a
> rewritten Dockerfile, but the core tool never depends on it, never needs Docker, and runs
> before a single image gets built.
>
> That's LayerLens."

**[End]**

---

## Fallback / if something breaks live

- **Web app won't load `/analyze` results:** the backend runs on a Cloudflare quick tunnel
  from a personal machine — if it's down, fall back to the `layerlens scan --explain` CLI
  demo instead (self-contained, no tunnel dependency) and skip the live image analysis.
- **`--explain` times out:** Featherless can occasionally be slow (15–30s, sometimes more).
  If it hangs past ~45s, kill it and say "this can take a bit longer under load — I've got a
  captured example" and paste a pre-saved output instead (see `demo-explain-sample.txt` if
  you choose to prepare one ahead of time).
- **No internet for the LLM calls at all:** skip `--explain` entirely and lean on
  `layerlens scan .` (fully offline, instant) plus the GitHub Actions YAML — the static
  scanning and CI-gating story doesn't need any network call.
