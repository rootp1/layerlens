# LayerLens

LayerLens analyzes a Docker image with [Dive](https://github.com/wagoodman/dive) and asks an
LLM to turn the layer-efficiency report — plus your Dockerfile — into plain-English
optimization advice and a rewritten Dockerfile example.

Renamed/restructured from the original hackathon project (previously "DIA / ContainerSlim").
See [product.md](../containerslim/product.md) in the sibling `containerslim` folder for the
full feature scope; this repo is the same functionality under a new name and layout.

## Structure

```
layerlens/
├── apps/
│   ├── api/   Flask backend — runs Dive against an image, calls an LLM for advice
│   ├── web/   React frontend — form, charts, animated results dashboard
│   └── lint/  layerlens-lint — installable Python package, static Dockerfile analysis
```

## Running locally

### Backend (`apps/api`)

```bash
cd apps/api
python3 -m venv flaskenv
source flaskenv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY (or an OpenAI-compatible provider)
python server.py        # serves on http://localhost:5001
```

Requires Docker running and the `dive` CLI on `PATH`.

### Frontend (`apps/web`)

```bash
cd apps/web
npm install
cp .env.example .env   # points at the local backend by default
npm start               # serves on http://localhost:3000
```

### Dockerfile linting/CI package (`apps/lint`)

`layerlens-lint` is a separate, standalone Python package (its own `pyproject.toml`) with no
dependency on the API/web apps or on Docker/Dive being installed — it works purely from
Dockerfile *text*. Two features:

1. **Repo scanner** — `layerlens scan .` finds every Dockerfile in a tree and prints a score
   plus concrete fixes, before anything gets built.
2. **CI/CD PR assistant** — `layerlens pr-check --dockerfile <path> --post --fail-on-worse`
   compares a Dockerfile's PR base vs. head and posts a GitHub PR comment (and fails CI) when it
   got worse. See `.github/workflows/dockerfile-check.yml` for a working example, and
   `apps/lint/README.md` for full usage and the library API.

```bash
cd apps/lint
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # 29 tests
layerlens scan ../..         # scan this whole repo
```

## Deployment

- **Frontend** → [Vercel](https://layerlens-web.vercel.app), built from `apps/web` with
  `REACT_APP_API_BASE_URL` set at build time to the backend's public URL.
- **Backend** → runs locally (`apps/api`, with a real Docker daemon + `dive` available) and is
  exposed to the internet via a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
  (`cloudflared tunnel --url http://localhost:5001`).

Why not a managed host for the backend: it shells out to `docker`/`dive` against a real Docker
daemon (the original Dockerfile even runs `dockerd` inside a `docker:dind` container in
privileged mode). Hugging Face Spaces doesn't support privileged/Docker-in-Docker containers,
and its Docker-SDK Spaces additionally require a PRO subscription — so instead the backend runs
on a machine that already has Docker, and Cloudflare Tunnel punches a public HTTPS URL through
to it without needing router/port-forwarding setup. The tunnel URL from a quick tunnel
(`cloudflared tunnel --url ...`) is ephemeral — it changes every time the tunnel restarts, so
after a restart, re-run the Vercel build with the new URL:

```bash
cd apps/web
vercel --prod --yes -b REACT_APP_API_BASE_URL=https://<new-tunnel-subdomain>.trycloudflare.com
```

For a stable, permanent URL instead, authenticate `cloudflared` to a Cloudflare account
(`cloudflared tunnel login`) and create a named tunnel bound to a real domain.
