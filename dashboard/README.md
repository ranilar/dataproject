# Health dashboard

The scoring dashboard from `website/health_score_website_v4.html`, split into a static frontend and a FastAPI backend. All scoring logic (sub-scores, weights, alerts, cohort statistics, ROI, endurance estimate) runs on the server; the browser only sends inputs and renders the response.

```
dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app: routes, CORS, serves ../frontend
│   │   ├── scoring.py      # scoring engine (port of the v4 JS)
│   │   ├── reference.py    # cohort stats, slider specs, presets
│   │   └── schemas.py      # request / response models
│   ├── tests/
│   ├── requirements.txt
│   └── requirements-dev.txt
└── frontend/
    ├── index.html          # v4 markup
    ├── app.js              # UI state, API calls, rendering
    └── config.js           # API base URL
```

## Run locally

```bash
cd dashboard/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload
```

Open http://localhost:8000. The backend serves the frontend from the same origin, so no further configuration is needed. Interactive API docs are at http://localhost:8000/docs.

Tests:

```bash
.venv/bin/python -m pytest
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness check |
| GET | `/api/config` | Slider specs, cohort names / counts / means, profile names |
| GET | `/api/profiles/{name}?sex=ALL\|M\|F` | Preset values |
| POST | `/api/score` | Composite score, sub-scores, alerts, percentiles, ROI, effective inputs |

Example:

```bash
curl -s localhost:8000/api/score -H 'Content-Type: application/json' -d '{
  "values": {"sleep_hours": 5.2, "stress_level": 8.5, "daily_steps": 4200, "heart_rate": 84,
             "endurance_level": 6.8, "bmi": 27.5, "hydration_level": 1.6},
  "sex": "ALL", "cohort": "HARMONIZED", "age": 38,
  "active_minutes": 15, "auto_endurance": true
}'
```

## Deploy

**Single host (simplest).** Deploy `dashboard/backend` to any Python host (Render, Railway, Fly.io, a VM) with the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, from a checkout that includes `dashboard/frontend`. The frontend is served at `/`.

**Frontend on Cloudflare Pages, backend elsewhere.**

1. Deploy the backend as above and note its URL, e.g. `https://health-api.onrender.com`.
2. Set `window.API_BASE` in `frontend/config.js` to that URL.
3. Cloudflare dashboard → Workers & Pages → Create → Pages → Connect to Git → this repo. Framework preset *None*, build command empty, output directory `dashboard/frontend`.
4. On the backend, set `ALLOWED_ORIGINS` to the Pages URL (comma-separated for several, e.g. `https://dashboard.pages.dev,http://localhost:8000`).

## What is visible to users

The browser receives the markup, `app.js`, slider ranges, cohort means and every API response. Scoring weights, cohort SDs, curve shapes, alert thresholds and the endurance formula stay on the server. If this GitHub repository is public, the backend source is still readable there.

## Data caveats

- The CLINICAL cohort statistics come from `data/health_fitness_dataset.csv`, which our EDA found to be synthetic (see `exploratory-analysis/`).
- The HARMONIZED and WEARABLE statistics were hard-coded in the original dashboard; the wearable dataset itself is not in this repository.
