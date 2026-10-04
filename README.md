# news-api

[![Scrape latest data](https://github.com/pranavpk404/news-api/actions/workflows/main.yml/badge.svg)](https://github.com/pranavpk404/news-api/actions/workflows/main.yml)

This repository publishes static news JSON files for a Flask application. The
GitHub Actions workflow refreshes them every two hours and commits only when
the generated data changes.

## Public API

The original Flask-compatible paths are preserved:

```text
https://raw.githubusercontent.com/pranavpk404/news-api/main/{country}/{category}.json
```

Countries:

| Country | Code |
| --- | --- |
| India | `in` |
| United States | `us` |
| United Kingdom | `gb` |

Categories:

```text
general
business
health
science
sports
technology
entertainment
```

Example:

```text
https://raw.githubusercontent.com/pranavpk404/news-api/main/us/general.json
```

The root files keep a NewsAPI-compatible response shape:

```json
{
  "status": "ok",
  "totalResults": 32,
  "articles": []
}
```

## Rich data files

The `data/` directory includes provider and timestamp metadata:

```text
data/{country}/{category}_headlines.json
data/{country}/{category}_everything.json
data/status.json
```

The headline files combine NewsAPI and RSS articles. NewsAPI is used for US
headline queries and deeper searches when the request budget allows it. RSS
feeds provide coverage for all countries and categories, including India and
the UK where NewsAPI can return an empty successful response.

The `everything` files contain NewsAPI deep-search results when available and
fall back to the relevant RSS category feed when they are not.

## API keys

The scraper automatically detects any non-empty unique keys from:

```text
NEWSAPI_KEYS       # optional comma- or whitespace-separated list
FIRSTAPI
SECONDAPI
THIRDAPI
FOURTHAPI
FIFTHAPI
SIXTHAPI
SEVENTHAPI
```

The GitHub Actions workflow passes the legacy secret names for compatibility.
Only configured keys are used. NewsAPI requests are capped per run using the
100-requests-per-day Developer-plan budget and a safety reserve. RSS requests
do not consume the NewsAPI budget.

## Run locally

Install the pinned dependency:

```bash
python -m pip install -r requirements.txt
```

Run with the configured NewsAPI keys:

```bash
python main.py
```

Run without NewsAPI, using only RSS feeds:

```bash
python main.py --rss-only
```

Fetch and print results without writing files:

```bash
python main.py --dry-run
```

## Data behavior

- Articles are deduplicated by URL.
- Files are written atomically.
- A provider failure does not erase the last successful file.
- API keys are rotated between retries without printing their values.
- `data/status.json` records request usage and provider failures.
