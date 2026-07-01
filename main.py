import os
import json
import time
from datetime import datetime, timezone
from newsapi import NewsApiClient

# ── Configuration ────────────────────────────────────────────────────────────
# Sources grouped by country — used as fallback when `country` param fails
# and as filters for the /everything endpoint.
COUNTRY_SOURCES = {
    "in": "the-times-of-india,the-hindu,ndtv,india-today,business-standard",
    "us": "cnn,fox-news,nbc-news,abc-news,cbs-news,usa-today,the-washington-post",
    "gb": "bbc-news,the-guardian,independent,telegraph,daily-mail,reuters",
}

CATEGORIES = [
    "general",
    "business",
    "health",
    "science",
    "sports",
    "technology",
    "entertainment",
]

# Categories to deep-search via /everything (skip general & entertainment — too broad)
EVERYTHING_CATEGORIES = ["business", "health", "science", "sports", "technology"]

EVERYTHING_QUERIES = {
    "business": "market economy finance stock",
    "health": "medical health research wellness",
    "science": "science research discovery space",
    "sports": "sports match score tournament cricket football",
    "technology": "technology AI software startup",
}

HEADLINE_PAGES = 2  # how many pages to paginate for top headlines
PAGE_SIZE = 100
MAX_RETRIES = 2     # retry a failed call on a DIFFERENT key

# ── API Key Pool (round-robin) ───────────────────────────────────────────────
API_KEYS = [
    os.environ.get("FIRSTAPI"),
    os.environ.get("SECONDAPI"),
    os.environ.get("THIRDAPI"),
    os.environ.get("FOURTHAPI"),
    os.environ.get("FIFTHAPI"),
    os.environ.get("SIXTHAPI"),
    os.environ.get("SEVENTHAPI"),
]
API_KEYS = [k for k in API_KEYS if k]  # drop any unset keys

_call_idx = 0  # global counter for round-robin


def get_next_client():
    """Return (NewsApiClient, key_number) using round-robin rotation."""
    global _call_idx
    idx = _call_idx % len(API_KEYS)
    _call_idx += 1
    return NewsApiClient(api_key=API_KEYS[idx]), idx + 1


def fetch_with_retry(fetch_fn, label):
    """
    Call fetch_fn(api_client) -> dict.
    On failure, retry up to MAX_RETRIES times on DIFFERENT keys.
    """
    for attempt in range(1, MAX_RETRIES + 2):
        api, key_num = get_next_client()
        try:
            result = fetch_fn(api)
            if result and result.get("status") == "ok":
                return result
            # API returned an error payload (e.g. rate-limited, invalid params)
            msg = result.get("message", "unknown error") if result else "empty response"
            print(f"    key#{key_num} attempt {attempt}: {msg}", end=" -> ")
        except Exception as exc:
            print(f"    key#{key_num} attempt {attempt}: {exc}", end=" -> ")

        if attempt <= MAX_RETRIES:
            time.sleep(1)  # brief pause before trying next key
        else:
            print("GAVE UP")
            return None
    return None


def save_json(data, filepath):
    """Write JSON, creating parent dirs automatically."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def deduplicate(articles):
    """Remove duplicate articles by URL (keep first seen)."""
    seen = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
    return unique


# ── Country-aware top-headlines fetch ────────────────────────────────────────
# If a country fails with `country=` param, fall back to `sources=` for
# ALL subsequent calls to that country.  This fixes the India/UK free-tier issue.
_country_uses_sources = set()  # populated at runtime


def fetch_top_headlines(country, category, page=1):
    """Fetch top headlines, auto-falling back to sources-based query."""
    if country in _country_uses_sources:
        # We already know `country=` doesn't work — go straight to sources
        return _fetch_headlines_by_sources(country, category, page)

    # First try: use country parameter
    def _by_country(api):
        return api.get_top_headlines(
            category=category,
            country=country,
            page_size=PAGE_SIZE,
            page=page,
        )

    result = fetch_with_retry(_by_country, f"{country}/{category}/p{page}")

    if result is None:
        print(f"    [!] country= failed for '{country}', switching to sources mode")
        _country_uses_sources.add(country)
        return _fetch_headlines_by_sources(country, category, page)

    return result


def _fetch_headlines_by_sources(country, category, page=1):
    """Fallback: fetch top headlines using source IDs instead of country code."""
    sources = COUNTRY_SOURCES.get(country, "")

    def _by_sources(api):
        return api.get_top_headlines(
            category=category,
            sources=sources,
            page_size=PAGE_SIZE,
            page=page,
        )

    return fetch_with_retry(_by_sources, f"{country}/{category}/sources/p{page}")


def fetch_everything(country, category, query, page=1):
    """Deep search via /everything, filtered to country-specific sources."""
    sources = COUNTRY_SOURCES.get(country, "")

    def _fetch(api):
        return api.get_everything(
            q=query,
            sources=sources,
            language="en",
            page_size=PAGE_SIZE,
            page=page,
            sort_by="publishedAt",
        )

    return fetch_with_retry(_fetch, f"{country}/{category}/everything/p{page}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not API_KEYS:
        print("ERROR: No API keys found. Set FIRSTAPI..SEVENTHAPI env vars.")
        return

    runs_per_day = 12          # cron every 2 hours
    daily_budget = len(API_KEYS) * 100
    budget_per_run = daily_budget // runs_per_day

    estimated_calls = (
        len(COUNTRY_SOURCES) * len(CATEGORIES) * HEADLINE_PAGES   # Phase 1
        + len(COUNTRY_SOURCES) * len(EVERYTHING_CATEGORIES)        # Phase 2
    )

    print("=" * 58)
    print("  NEWS SCRAPER — MAX POWER MODE")
    print("=" * 58)
    print(f"  API keys       : {len(API_KEYS)}")
    print(f"  Daily budget   : {daily_budget} calls ({len(API_KEYS)} x 100)")
    print(f"  Runs per day   : {runs_per_day} (every 2h)")
    print(f"  Budget per run : ~{budget_per_run} calls")
    print(f"  Estimated use  : {estimated_calls} calls/run "
          f"({estimated_calls * runs_per_day}/day)")
    print(f"  Countries      : {list(COUNTRY_SOURCES.keys())}")
    print(f"  Headline pages : {HEADLINE_PAGES}")
    print(f"  Everything cats: {EVERYTHING_CATEGORIES}")
    print("=" * 58, "\n")

    total_calls = 0
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Phase 1: Top Headlines (paginated) ────────────────────────────────
    print("PHASE 1: Top Headlines (country-based, with pagination)")
    print("-" * 58)

    for country in COUNTRY_SOURCES:
        for category in CATEGORIES:
            all_articles = []

            for page in range(1, HEADLINE_PAGES + 1):
                label = f"{country}/{category} p{page}"
                print(f"  [{label}]", end="", flush=True)

                result = fetch_top_headlines(country, category, page)
                total_calls += 1

                if result:
                    articles = result.get("articles", []) or []
                    all_articles.extend(articles)
                    total_available = result.get("totalResults", 0)
                    mode = "sources" if country in _country_uses_sources else "country"
                    print(f"  OK  [{mode}] {len(articles)} articles "
                          f"(total available: {total_available})")

                    if len(articles) < PAGE_SIZE:
                        break  # no more pages
                else:
                    print("  FAILED")

            # Deduplicate across pages and save
            all_articles = deduplicate(all_articles)

            if all_articles:
                save_json({
                    "source": "top_headlines",
                    "country": country,
                    "category": category,
                    "mode": "sources" if country in _country_uses_sources else "country",
                    "fetched_at": timestamp,
                    "articles_count": len(all_articles),
                    "articles": all_articles,
                }, f"data/{country}/{category}_headlines.json")
            else:
                print(f"    [!] No articles for {country}/{category}")

    # ── Phase 2: Everything Search (deeper, source-filtered) ──────────────
    print(f"\nPHASE 2: Everything Search ({len(EVERYTHING_CATEGORIES)} categories)")
    print("-" * 58)

    for country in COUNTRY_SOURCES:
        for category in EVERYTHING_CATEGORIES:
            query = EVERYTHING_QUERIES.get(category, category)
            label = f"{country}/{category}"
            print(f"  [{label}] q='{query}'", end="", flush=True)

            result = fetch_everything(country, category, query)
            total_calls += 1

            if result:
                articles = result.get("articles", []) or []
                total_available = result.get("totalResults", 0)
                print(f"  OK  {len(articles)} articles "
                      f"(total available: {total_available})")

                if articles:
                    save_json({
                        "source": "everything",
                        "country": country,
                        "category": category,
                        "query": query,
                        "fetched_at": timestamp,
                        "articles_count": len(articles),
                        "articles": articles,
                    }, f"data/{country}/{category}_everything.json")
            else:
                print("  FAILED")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print(f"  DONE — {total_calls} API calls used")
    print(f"  Daily projection: {total_calls * runs_per_day} / {daily_budget}")
    per_key = total_calls * runs_per_day // len(API_KEYS)
    print(f"  Per key average:  ~{per_key} / 100 daily")
    if _country_uses_sources:
        print(f"  Fallback mode:   sources (not country) for {_country_uses_sources}")
    print("=" * 58)


if __name__ == "__main__":
    main()