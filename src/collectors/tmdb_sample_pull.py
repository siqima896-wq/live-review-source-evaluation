"""Collect and summarize a small, cross-genre TMDB movie-review sample."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "tmdb"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

API_BASE_URL = "https://api.themoviedb.org/3"
MAX_PAGES_PER_MOVIE = 2
REQUEST_TIMEOUT_SECONDS = 30

# The sample spans different genres, release periods, and production regions.
TARGETS = [
    {
        "movie_id": 346698,
        "topic": "contemporary_popular_culture",
        "title": "Barbie",
    },
    {
        "movie_id": 872585,
        "topic": "historical_drama",
        "title": "Oppenheimer",
    },
    {
        "movie_id": 496243,
        "topic": "international_thriller_drama",
        "title": "Parasite",
    },
    {
        "movie_id": 129,
        "topic": "animation_fantasy",
        "title": "Spirited Away",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_local_env_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return ""

    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, separator, candidate = line.partition("=")
        if separator and key.strip() == name:
            return candidate.strip().strip('"').strip("'")
    return ""


def require_api_key() -> str:
    api_key = load_local_env_value("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TMDB_API_KEY is not set. Add TMDB_API_KEY=your_key_here to "
            "the local .env file, then rerun this collector."
        )
    return api_key


def fetch_page(api_key: str, movie_id: int, page: int) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/movie/{movie_id}/reviews",
        params={"api_key": api_key, "language": "en-US", "page": page},
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "Siqi-Live-Source-Evaluation/0.1"},
    )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            f"TMDB returned HTTP {response.status_code} with invalid JSON"
        ) from error

    if response.status_code >= 400 or payload.get("success") is False:
        message = payload.get("status_message", "TMDB API request failed")
        code = payload.get("status_code", "unknown")
        raise RuntimeError(
            f"TMDB returned HTTP {response.status_code}: {message} "
            f"(status_code: {code})"
        )
    return payload


def normalize_review(target: dict, review: dict, ingested_at: str) -> dict:
    author_details = review.get("author_details") or {}
    return {
        "source": "tmdb",
        "movie_id": target["movie_id"],
        "movie_title": target["title"],
        "topic": target["topic"],
        "review_id": review.get("id"),
        "review_text": review.get("content"),
        "rating": author_details.get("rating"),
        "created_at": review.get("created_at"),
        "updated_at": review.get("updated_at"),
        "ingested_at": ingested_at,
    }


def collect_target(api_key: str, target: dict, ingested_at: str) -> tuple[list, dict]:
    records = []
    seen_review_ids = set()
    pages_fetched = 0
    documented_total_pages = None
    documented_total_results = None

    for page in range(1, MAX_PAGES_PER_MOVIE + 1):
        payload = fetch_page(api_key, target["movie_id"], page)
        pages_fetched += 1
        documented_total_pages = payload.get("total_pages")
        documented_total_results = payload.get("total_results")

        for review in payload.get("results", []):
            record = normalize_review(target, review, ingested_at)
            review_id = record.get("review_id")
            if not review_id or review_id in seen_review_ids:
                continue
            seen_review_ids.add(review_id)
            records.append(record)

        if not payload.get("results") or page >= (documented_total_pages or 0):
            break

    return records, {
        **target,
        "status": "success",
        "pages_fetched": pages_fetched,
        "records_collected": len(records),
        "api_total_pages": documented_total_pages,
        "api_total_results": documented_total_results,
        "more_pages_available_after_test_window": bool(
            documented_total_pages
            and documented_total_pages > pages_fetched
        ),
    }


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def compare_with_previous(current_records: list[dict], previous_file: Path | None) -> dict:
    if previous_file is None:
        return {
            "status": "not_available_first_run",
            "previous_file": None,
            "shared_records": None,
            "new_records": None,
            "not_in_current_fixed_window": None,
            "changed_records": None,
        }

    previous_records = load_jsonl(previous_file)
    previous_map = {
        record.get("review_id"): record
        for record in previous_records
        if record.get("review_id")
    }
    current_map = {
        record.get("review_id"): record
        for record in current_records
        if record.get("review_id")
    }
    shared_ids = set(previous_map) & set(current_map)
    changed_ids = {
        review_id
        for review_id in shared_ids
        if (
            previous_map[review_id].get("review_text")
            != current_map[review_id].get("review_text")
            or previous_map[review_id].get("rating")
            != current_map[review_id].get("rating")
            or previous_map[review_id].get("updated_at")
            != current_map[review_id].get("updated_at")
        )
    }
    return {
        "status": "completed",
        "previous_file": str(previous_file.relative_to(PROJECT_ROOT)),
        "shared_records": len(shared_ids),
        "new_records": len(set(current_map) - set(previous_map)),
        "not_in_current_fixed_window": len(set(previous_map) - set(current_map)),
        "changed_records": len(changed_ids),
    }


def build_quality_summary(records: list[dict]) -> dict:
    review_ids = [record.get("review_id") for record in records]
    unique_ids = {item for item in review_ids if item}
    text_lengths = [
        len(str(record.get("review_text") or "").strip())
        for record in records
    ]
    ratings = [
        record.get("rating")
        for record in records
        if isinstance(record.get("rating"), (int, float))
    ]
    return {
        "total_records": len(records),
        "unique_review_ids": len(unique_ids),
        "duplicate_review_ids": len(review_ids) - len(unique_ids),
        "missing_review_id": sum(not item for item in review_ids),
        "missing_review_text": sum(length == 0 for length in text_lengths),
        "records_with_rating": len(ratings),
        "records_without_rating": len(records) - len(ratings),
        "average_rating_when_present": round(mean(ratings), 2) if ratings else None,
        "average_text_length_characters": (
            round(mean(text_lengths), 2) if text_lengths else None
        ),
        "median_text_length_characters": (
            round(median(text_lengths), 2) if text_lengths else None
        ),
    }


def main() -> None:
    api_key = require_api_key()
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    previous_files = sorted(NORMALIZED_DIR.glob("tmdb_reviews_*.jsonl"))
    previous_file = previous_files[-1] if previous_files else None
    run_time = utc_now()
    run_id = run_time.strftime("%Y%m%dT%H%M%SZ")
    ingested_at = run_time.isoformat()
    records = []
    target_summaries = []
    errors = []

    for target in TARGETS:
        try:
            target_records, target_summary = collect_target(
                api_key, target, ingested_at
            )
            records.extend(target_records)
            target_summaries.append(target_summary)
        except (requests.RequestException, RuntimeError) as error:
            errors.append({"movie_id": target["movie_id"], "error": str(error)})
            target_summaries.append(
                {
                    **target,
                    "status": "failed",
                    "pages_fetched": 0,
                    "records_collected": 0,
                }
            )

    output_file = NORMALIZED_DIR / f"tmdb_reviews_{run_id}.jsonl"
    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "tmdb",
        "status": "completed" if records and not errors else (
            "partial" if records else "failed"
        ),
        "evidence_status": "observed" if records else "unverified",
        "run_id": run_id,
        "run_started_at": ingested_at,
        "collection_configuration": {
            "endpoint": "/movie/{movie_id}/reviews",
            "language": "en-US",
            "max_pages_per_movie": MAX_PAGES_PER_MOVIE,
            "target_count": len(TARGETS),
        },
        "targets": target_summaries,
        "quality": build_quality_summary(records),
        "run_comparison": compare_with_previous(records, previous_file),
        "access": {"authentication": "API key"},
        "errors": errors,
        "normalized_output": str(output_file.relative_to(PROJECT_ROOT)),
        "privacy_note": (
            "TMDB author names and usernames are not retained. Normalized "
            "review text remains local and is ignored by Git."
        ),
    }

    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
