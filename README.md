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
│   └── web/   React frontend — form, charts, animated results dashboard
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

## Deployment

- **Frontend** → Vercel (`apps/web`, set `REACT_APP_API_BASE_URL` to the deployed backend URL)
- **Backend** → Hugging Face Spaces (Docker SDK, `apps/api`)

> **Known limitation:** the backend's `/analyze` endpoint shells out to `docker` and `dive`
> against a real Docker daemon (the original Dockerfile runs `dockerd` inside a
> `docker:dind` container in privileged mode). Hugging Face Spaces does not support
> privileged containers or docker-in-docker, so the health check (`GET /`) will work there
> but `/analyze` will fail until the backend is hosted somewhere that allows a real Docker
> daemon (e.g. a VPS, Fly.io, Render with Docker-in-Docker, or similar).
