"""Collect and summarize a small Apple App Store customer-review sample.

The collector uses the active legacy iTunes customer-reviews JSON feed and
stores reviewer-free normalized records locally. Apple does not currently
document this feed as part of the App Store Connect API, so production use
requires a separate governance decision.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "apple-app-store"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

COUNTRY = "us"
PAGE = 1
SORT_ORDER = "mostrecent"
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "Siqi-Live-Source-Evaluation/0.1 (small feasibility sample)"

TARGETS = [
    {
        "app_id": "570060128",
        "app_name": "Duolingo: Language Lessons",
        "category": "Education",
    },
    {
        "app_id": "324684580",
        "app_name": "Spotify: Music and Podcasts",
        "category": "Music",
    },
    {
        "app_id": "368677368",
        "app_name": "Uber - Request a ride",
        "category": "Travel",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def feed_url(app_id: str, page: int = PAGE) -> str:
    return (
        f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/"
        f"page={page}/id={app_id}/sortby={SORT_ORDER}/json"
    )


def label(entry: dict, key: str) -> str | None:
    value = entry.get(key)
    if not isinstance(value, dict):
        return None
    result = value.get("label")
    return result if isinstance(result, str) and result else None


def integer_label(entry: dict, key: str) -> int | None:
    value = label(entry, key)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def available_pages(feed: dict) -> int | None:
    for item in feed.get("link", []):
        attributes = item.get("attributes", {})
        if attributes.get("rel") != "last":
            continue
        match = re.search(r"/page=(\d+)/", attributes.get("href", ""))
        return int(match.group(1)) if match else None
    return None


def summarize_target(records: list[dict]) -> dict:
    ratings = [
        record["star_rating"]
        for record in records
        if isinstance(record.get("star_rating"), int)
    ]
    text_lengths = [len(record.get("review_text") or "") for record in records]
    timestamps = sorted(
        record["updated_at"] for record in records if record.get("updated_at")
    )
    observed_order = [
        record["updated_at"] for record in records if record.get("updated_at")
    ]
    return {
        "average_star_rating": round(mean(ratings), 2) if ratings else None,
        "average_text_length_characters": (
            round(mean(text_lengths), 2) if text_lengths else None
        ),
        "distinct_app_versions": len(
            {
                record["app_version"]
                for record in records
                if record.get("app_version")
            }
        ),
        "oldest_review_timestamp": timestamps[0] if timestamps else None,
        "newest_review_timestamp": timestamps[-1] if timestamps else None,
        "newest_first_order_observed": observed_order == sorted(
            observed_order, reverse=True
        ),
    }


def fetch_target(target: dict, ingested_at: str) -> tuple[list[dict], dict]:
    response = requests.get(
        feed_url(target["app_id"]),
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    feed = payload.get("feed") or {}

    records = []
    for entry in feed.get("entry", []):
        review_id = label(entry, "id")
        review_text = label(entry, "content")
        if not review_id or review_text is None:
            continue
        records.append(
            {
                "source": "apple_app_store_customer_reviews_feed",
                "app_id": target["app_id"],
                "app_name": target["app_name"],
                "category": target["category"],
                "storefront": COUNTRY,
                "review_id": review_id,
                "review_title": label(entry, "title"),
                "review_text": review_text,
                "star_rating": integer_label(entry, "im:rating"),
                "app_version": label(entry, "im:version"),
                "updated_at": label(entry, "updated"),
                "vote_sum": integer_label(entry, "im:voteSum"),
                "vote_count": integer_label(entry, "im:voteCount"),
                "ingested_at": ingested_at,
            }
        )

    return records, {
        **target,
        "status": "success" if records else "no_reviews_found",
        "http_status": response.status_code,
        "records_collected": len(records),
        "page_fetched": PAGE,
        "pages_advertised_by_feed": available_pages(feed),
        "feed_url": response.url,
        "quality": summarize_target(records),
    }


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def compare_with_previous(records: list[dict], previous_file: Path | None) -> dict:
    if previous_file is None:
        return {
            "status": "not_available_first_run",
            "previous_file": None,
            "shared_records": None,
            "new_records": None,
            "not_in_current_recent_page": None,
            "changed_records": None,
        }

    previous = {
        item["review_id"]: item
        for item in load_jsonl(previous_file)
        if item.get("review_id")
    }
    current = {
        item["review_id"]: item for item in records if item.get("review_id")
    }
    shared = set(previous) & set(current)
    changed = {
        review_id
        for review_id in shared
        if any(
            previous[review_id].get(field) != current[review_id].get(field)
            for field in (
                "review_title",
                "review_text",
                "star_rating",
                "app_version",
                "updated_at",
                "vote_sum",
                "vote_count",
            )
        )
    }
    return {
        "status": "completed",
        "previous_file": str(previous_file.relative_to(PROJECT_ROOT)),
        "shared_records": len(shared),
        "new_records": len(set(current) - set(previous)),
        "not_in_current_recent_page": len(set(previous) - set(current)),
        "changed_records": len(changed),
    }


def build_quality_summary(records: list[dict]) -> dict:
    review_ids = [record.get("review_id") for record in records]
    unique_ids = {review_id for review_id in review_ids if review_id}
    text_lengths = [len(record.get("review_text") or "") for record in records]
    ratings = [
        record["star_rating"]
        for record in records
        if isinstance(record.get("star_rating"), int)
    ]
    fields = (
        "review_id",
        "review_title",
        "review_text",
        "star_rating",
        "app_version",
        "updated_at",
        "vote_sum",
        "vote_count",
    )
    distribution = Counter(str(value) for value in ratings)
    return {
        "total_records": len(records),
        "unique_review_ids": len(unique_ids),
        "duplicate_review_ids": len(review_ids) - len(unique_ids),
        "missing_by_field": {
            field: sum(
                record.get(field) is None or record.get(field) == ""
                for record in records
            )
            for field in fields
        },
        "rating_distribution": {
            rating: distribution.get(str(rating), 0) for rating in range(1, 6)
        },
        "average_star_rating": round(mean(ratings), 2) if ratings else None,
        "average_text_length_characters": (
            round(mean(text_lengths), 2) if text_lengths else None
        ),
        "median_text_length_characters": (
            round(median(text_lengths), 2) if text_lengths else None
        ),
    }


def main() -> None:
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    previous_files = sorted(
        NORMALIZED_DIR.glob("apple_app_store_reviews_*.jsonl")
    )
    previous_file = previous_files[-1] if previous_files else None
    run_time = utc_now()
    run_id = run_time.strftime("%Y%m%dT%H%M%SZ")
    ingested_at = run_time.isoformat()
    records = []
    target_summaries = []
    errors = []

    for target in TARGETS:
        try:
            target_records, target_summary = fetch_target(target, ingested_at)
            records.extend(target_records)
            target_summaries.append(target_summary)
        except (requests.RequestException, ValueError) as error:
            errors.append({"app_id": target["app_id"], "error": str(error)})
            target_summaries.append(
                {
                    **target,
                    "status": "failed",
                    "records_collected": 0,
                }
            )

    output_file = (
        NORMALIZED_DIR / f"apple_app_store_reviews_{run_id}.jsonl"
    )
    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "apple_app_store",
        "status": "completed" if records and not errors else (
            "partial" if records else "failed"
        ),
        "evidence_status": "observed" if records else "unverified",
        "run_id": run_id,
        "run_started_at": ingested_at,
        "collection_configuration": {
            "surface": "legacy iTunes customer-reviews JSON feed",
            "storefront": COUNTRY,
            "sort_order": SORT_ORDER,
            "page_fetched_per_app": PAGE,
            "target_count": len(TARGETS),
            "requested_records_per_app": 50,
        },
        "targets": target_summaries,
        "quality": build_quality_summary(records),
        "run_comparison": compare_with_previous(records, previous_file),
        "access": {
            "legacy_feed_authentication": "none observed",
            "official_app_store_connect_api": (
                "JWT authorization from an App Store Connect organization; "
                "customer reviews are scoped to apps available to that account"
            ),
        },
        "limitations": [
            (
                "The active legacy feed is not part of current App Store "
                "Connect API documentation."
            ),
            (
                "itunes.apple.com robots.txt disallows RSS paths for "
                "automated agents."
            ),
            (
                "The sample covers only the US storefront and one recent "
                "page per app."
            ),
            (
                "Storefront identifies the market feed, not the reviewer's "
                "current location."
            ),
            "The feed contains no developer-response field.",
        ],
        "errors": errors,
        "normalized_output": str(output_file.relative_to(PROJECT_ROOT)),
        "privacy_note": (
            "Reviewer nicknames and profile URIs are neither retained nor committed. "
            "Review titles and text remain local and are ignored by Git."
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
