# Project handoff — news-api

## Start here

This repository publishes static country/category news JSON for the News Reader.
Read `README.md`, `main.py`, and `tests/test_main.py` before changing ingestion.

## Stack and flow

- Python scraper with RSS and NewsAPI-compatible providers.
- Root files preserve the Flask/NewsAPI response shape: `{ status, totalResults, articles }`.
- Rich files live under `data/{country}/` and `data/status.json`.
- Refreshes write atomically. A failed provider refresh retains the last successful feed.
- `data/status.json` includes freshness, provider, attempted/succeeded, updated/retained,
  and failure metadata. A successful empty feed is still a real successful refresh.
- GitHub Actions performs scheduled refreshes; secrets are only configured in GitHub/local env.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Current verification: 10 tests passed. Do not run live ingestion unless API/RSS access
and the request budget are intentionally available.

## Next-maintainer rules

- Preserve the root response contract and existing static data paths.
- Never print, commit, or invent API keys.
- Do not replace retained feeds with empty data after a failed refresh.
- Treat tracked `data/` files as generated outputs; change them only as part of an
  intentional refresh or fixture update.
- Inspect the current remote before pushing because scheduled data commits may advance
  `main` independently.

## Last shipped state

- Main branch is pushed and clean.
- Freshness/preservation implementation and documentation are in the history.
- Live deployment and scheduled-action behavior still require configured GitHub secrets.
