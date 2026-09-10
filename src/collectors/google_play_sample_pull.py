"""Collect a privacy-minimized sample from public Google Play app pages.

This collector deliberately uses only the review cards rendered on each public
app-details page. It does not call Google Play's undocumented review endpoints.
For complete/recent reviews of an app you own, use the authenticated Google
Play Developer Reviews API instead.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

BASE_URL = "https://play.google.com/store/apps/details"
LANGUAGE = "en_US"
COUNTRY = "US"
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "Siqi-Live-Source-Evaluation/0.1 (small feasibility sample)"

TARGETS = [
    {
        "package_name": "com.duolingo",
        "app_name": "Duolingo: Language Lessons",
        "category": "Education",
    },
    {
        "package_name": "com.spotify.music",
        "app_name": "Spotify: Music and Podcasts",
        "category": "Music & Audio",
    },
    {
        "package_name": "com.ubercab",
        "app_name": "Uber - Request a ride",
        "category": "Maps & Navigation",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_star_rating(card) -> int | None:
    rating = card.select_one('[aria-label^="Rated "][aria-label*="stars"]')
    if not rating:
        return None
    match = re.search(r"Rated\s+(\d+)\s+stars?", rating.get("aria-label", ""))
    return int(match.group(1)) if match else None


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def fetch_target(target: dict, ingested_at: str) -> tuple[list[dict], dict]:
    response = requests.get(
        BASE_URL,
        params={
            "id": target["package_name"],
            "hl": LANGUAGE,
            "gl": COUNTRY,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    for card in soup.select("div.EGFGHd"):
        header = card.select_one("header[data-review-id]")
        text = card.select_one("div.h3YV2d")
        if not header or not text:
            continue

        date = card.select_one("span.bp9Aid")
        helpful = card.select_one("[data-original-thumbs-up-count]")
        reply = card.select_one("div.ocpBU")
        reply_text = reply.select_one("div.ras4vb") if reply else None
        reply_date = reply.select_one("div.I9Jtec") if reply else None
        records.append(
            {
                "source": "google_play_public_app_page",
                "package_name": target["package_name"],
                "app_name": target["app_name"],
                "category": target["category"],
                "review_id": header.get("data-review-id"),
                "review_text": text.get_text(" ", strip=True),
                "star_rating": parse_star_rating(card),
                "review_date": parse_date(date.get_text(strip=True) if date else None),
                "helpful_count": (
                    int(helpful.get("data-original-thumbs-up-count", "0"))
                    if helpful
                    else None
                ),
                "developer_reply_present": reply_text is not None,
                "developer_reply_text": (
                    reply_text.get_text(" ", strip=True) if reply_text else None
                ),
                "developer_reply_date": parse_date(
                    reply_date.get_text(strip=True) if reply_date else None
                ),
                "ingested_at": ingested_at,
            }
        )

    return records, {
        **target,
        "status": "success" if records else "no_review_cards_found",
        "http_status": response.status_code,
        "review_cards_collected": len(records),
        "page_url": response.url,
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
            "not_in_current_page_sample": None,
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
                "review_text",
                "star_rating",
                "helpful_count",
                "developer_reply_text",
            )
        )
    }
    return {
        "status": "completed",
        "previous_file": str(previous_file.relative_to(PROJECT_ROOT)),
        "shared_records": len(shared),
        "new_records": len(set(current) - set(previous)),
        "not_in_current_page_sample": len(set(previous) - set(current)),
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
        "review_text",
        "star_rating",
        "review_date",
        "helpful_count",
    )
    return {
        "total_records": len(records),
        "unique_review_ids": len(unique_ids),
        "duplicate_review_ids": len(review_ids) - len(unique_ids),
        "missing_by_field": {
            field: sum(record.get(field) is None or record.get(field) == "" for record in records)
            for field in fields
        },
        "records_with_developer_reply": sum(
            bool(record.get("developer_reply_present")) for record in records
        ),
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

    previous_files = sorted(NORMALIZED_DIR.glob("google_play_reviews_*.jsonl"))
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
        except requests.RequestException as error:
            errors.append(
                {"package_name": target["package_name"], "error": str(error)}
            )
            target_summaries.append(
                {
                    **target,
                    "status": "failed",
                    "review_cards_collected": 0,
                }
            )

    output_file = NORMALIZED_DIR / f"google_play_reviews_{run_id}.jsonl"
    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "source": "google_play",
        "status": "completed" if records and not errors else (
            "partial" if records else "failed"
        ),
        "evidence_status": "observed" if records else "unverified",
        "run_id": run_id,
        "run_started_at": ingested_at,
        "collection_configuration": {
            "surface": "public app-details HTML only",
            "language": LANGUAGE,
            "country": COUNTRY,
            "target_count": len(TARGETS),
            "review_limit": "review cards rendered on the initial app page",
            "undocumented_review_endpoints_used": False,
        },
        "targets": target_summaries,
        "quality": build_quality_summary(records),
        "run_comparison": compare_with_previous(records, previous_file),
        "access": {
            "public_page_authentication": "none",
            "official_reviews_api": (
                "OAuth or service account with Reply to reviews permission; "
                "limited to production apps controlled by the authenticated developer"
            ),
        },
        "limitations": [
            "The initial app page exposes only a small curated set of review cards.",
            "The public HTML structure is undocumented and may change without notice.",
            "This route does not support dependable pagination or completeness claims.",
            "Locale parameters do not prove reviewer location or population coverage.",
        ],
        "errors": errors,
        "normalized_output": str(output_file.relative_to(PROJECT_ROOT)),
        "privacy_note": (
            "Reviewer names and profile images are neither retained nor committed. "
            "Review and developer-reply text remains local and is ignored by Git."
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
