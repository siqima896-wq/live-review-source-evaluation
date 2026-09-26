"""Collect a bounded, diverse Google Play review sample for exploratory analysis.

The collector uses the unofficial ``google-play-scraper`` package. Reviewer
names and profile images are deliberately excluded. Review text is written to
the ignored ``data/normalized`` directory; only aggregate outputs belong in
version control.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from google_play_scraper import Sort, app, reviews


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play-eda"

TARGETS = [
    ("com.duolingo", "Duolingo", "Education"),
    ("org.khanacademy.android", "Khan Academy", "Education"),
    ("com.spotify.music", "Spotify", "Music & Audio"),
    ("com.google.android.apps.youtube.music", "YouTube Music", "Music & Audio"),
    ("com.ubercab", "Uber", "Maps & Navigation"),
    ("com.google.android.apps.maps", "Google Maps", "Maps & Navigation"),
    ("com.discord", "Discord", "Communication"),
    ("com.whatsapp", "WhatsApp", "Communication"),
    ("com.venmo", "Venmo", "Finance"),
    ("com.squareup.cash", "Cash App", "Finance"),
    ("com.myfitnesspal.android", "MyFitnessPal", "Health & Fitness"),
    ("com.strava", "Strava", "Health & Fitness"),
    ("com.king.candycrushsaga", "Candy Crush Saga", "Games"),
    ("com.supercell.clashofclans", "Clash of Clans", "Games"),
    ("com.amazon.mShop.android.shopping", "Amazon Shopping", "Shopping"),
    ("com.etsy.android", "Etsy", "Shopping"),
    ("com.todoist", "Todoist", "Productivity"),
    ("com.evernote", "Evernote", "Productivity"),
    ("com.netflix.mediaclient", "Netflix", "Entertainment"),
    ("com.disney.disneyplus", "Disney+", "Entertainment"),
]


def iso_datetime(value: object) -> str | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.astimezone()
    return value.astimezone(timezone.utc).isoformat()


def normalize_review(item: dict, package_name: str, app_name: str, category: str,
                     ingested_at: str) -> dict:
    return {
        "source": "google_play_third_party_google_play_scraper",
        "package_name": package_name,
        "app_name": app_name,
        "category": category,
        "review_id": item.get("reviewId"),
        "review_text": item.get("content"),
        "star_rating": item.get("score"),
        "helpful_count": item.get("thumbsUpCount"),
        "review_created_version": item.get("reviewCreatedVersion"),
        "app_version": item.get("appVersion"),
        "review_timestamp": iso_datetime(item.get("at")),
        "developer_reply_present": item.get("replyContent") is not None,
        "developer_reply_text": item.get("replyContent"),
        "developer_reply_timestamp": iso_datetime(item.get("repliedAt")),
        "ingested_at": ingested_at,
    }


def selected_app_metadata(details: dict) -> dict:
    fields = (
        "title", "genre", "genreId", "score", "ratings", "reviews",
        "installs", "minInstalls", "realInstalls", "price", "free",
        "currency", "developer", "released", "updated", "version",
        "contentRating", "adSupported", "containsAds", "offersIAP",
    )
    return {field: details.get(field) for field in fields}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews-per-app", type=int, default=300)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    args = parser.parse_args()
    if not 50 <= args.reviews_per_app <= 1000:
        parser.error("--reviews-per-app must be between 50 and 1000")
    if not 0 <= args.delay_seconds <= 30:
        parser.error("--delay-seconds must be between 0 and 30")
    return args


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    ingested_at = started.isoformat()
    all_records: list[dict] = []
    target_results: list[dict] = []

    for package_name, app_name, category in TARGETS:
        target_started = time.monotonic()
        try:
            details = app(package_name, lang="en", country="us")
            items, continuation_token = reviews(
                package_name,
                lang="en",
                country="us",
                sort=Sort.NEWEST,
                count=args.reviews_per_app,
            )
            normalized = [
                normalize_review(item, package_name, app_name, category, ingested_at)
                for item in items
            ]
            all_records.extend(normalized)
            ids = [record["review_id"] for record in normalized]
            target_results.append({
                "package_name": package_name,
                "app_name": app_name,
                "category": category,
                "status": "success" if normalized else "no_records_returned",
                "records": len(normalized),
                "unique_review_ids": len({value for value in ids if value}),
                "continuation_available": continuation_token is not None,
                "elapsed_seconds": round(time.monotonic() - target_started, 3),
                "app_metadata": selected_app_metadata(details),
            })
        except Exception as error:
            target_results.append({
                "package_name": package_name,
                "app_name": app_name,
                "category": category,
                "status": "failed",
                "records": 0,
                "elapsed_seconds": round(time.monotonic() - target_started, 3),
                "error_type": type(error).__name__,
                "error": str(error),
            })
        time.sleep(args.delay_seconds)

    data_path = DATA_DIR / f"google_play_eda_{run_id}.jsonl"
    with data_path.open("w", encoding="utf-8") as file:
        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    finished = datetime.now(timezone.utc)
    summary = {
        "source": "google_play",
        "method": "third_party_open_source_scraper",
        "official_google_api": False,
        "run_id": run_id,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "configuration": {
            "language": "en",
            "country": "us",
            "sort": "newest",
            "target_count": len(TARGETS),
            "reviews_requested_per_app": args.reviews_per_app,
            "delay_seconds": args.delay_seconds,
        },
        "records_collected": len(all_records),
        "successful_targets": sum(item["status"] == "success" for item in target_results),
        "failed_targets": sum(item["status"] == "failed" for item in target_results),
        "targets": target_results,
        "local_normalized_output": str(data_path.relative_to(PROJECT_ROOT)),
        "privacy_note": "Reviewer names and profile images were not retained; review text remains in an ignored local file.",
        "sampling_note": "Newest English-language reviews returned for the US storefront form a bounded convenience sample, not a representative population sample.",
    }
    summary_path = RESULTS_DIR / "collection-summary.json"
    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Local review data: {data_path}")
    print(f"Aggregate collection summary: {summary_path}")


if __name__ == "__main__":
    main()
