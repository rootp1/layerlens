# LayerLens API

Flask backend: runs `dive` against a Docker image, sends the report + submitted Dockerfile to
an LLM, and returns optimization advice plus efficiency stats.

## Run locally

```bash
python3 -m venv flaskenv
source flaskenv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY (works with OpenAI or any OpenAI-compatible provider)
python server.py        # http://localhost:5001
```

Requires a running Docker daemon and the `dive` CLI on `PATH`.

## Endpoints

- `GET /` — health check
- `POST /analyze` — body `{ "image_name": "...", "dockerfile": "..." }`

## Docker

The bundled `Dockerfile` runs Docker-in-Docker (`docker:dind` base, `dockerd` started inside
the container) so `dive` can inspect images without depending on the host's Docker socket.
This requires the container to run with `--privileged`:

```bash
docker build -t layerlens-api .
docker run -d --privileged -p 5000:5000 --env-file .env layerlens-api
```

Because of the `--privileged`/docker-in-docker requirement, this image will **not** function
correctly on hosting platforms that sandbox containers without privileged mode (e.g. Hugging
Face Spaces) — the process will start and the health check will respond, but `/analyze` will
fail since no Docker daemon is reachable there.
