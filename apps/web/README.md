# LayerLens Web

React frontend for LayerLens — image/Dockerfile submission form, animated scan/loading state,
and a results dashboard with charts and AI-generated optimization advice.

## Run locally

```bash
npm install
cp .env.example .env   # REACT_APP_API_BASE_URL, defaults to http://localhost:5001
npm start               # http://localhost:3000
```

## Deploy

Deployed as a static build on Vercel. Set `REACT_APP_API_BASE_URL` in the Vercel project's
environment variables to point at the deployed backend.
