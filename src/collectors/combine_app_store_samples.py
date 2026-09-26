"""Combine the latest Google Play and Apple App Store samples.

The record-level CSV contains user-generated review text and stays local under
data/normalized. Aggregate source- and app-level CSV tables are safe to commit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "app-stores"
COMBINED_DATA_FILE = NORMALIZED_DIR / "app_store_reviews_combined.csv"
SOURCE_SUMMARY_FILE = RESULTS_DIR / "combined-source-summary.csv"
APP_SUMMARY_FILE = RESULTS_DIR / "combined-app-summary.csv"

RECORD_FIELDS = [
    "source",
    "store_app_id",
    "app_name",
    "category",
    "storefront",
    "review_id",
    "review_title",
    "review_text",
    "star_rating",
    "app_version",
    "review_timestamp",
    "engagement_positive",
    "engagement_total",
    "developer_reply_present",
    "developer_reply_text",
    "developer_reply_timestamp",
    "ingested_at",
    "source_file",
]


def latest_file(pattern: str) -> Path:
    candidates = sorted(NORMALIZED_DIR.glob(pattern))
    if not candidates:
        raise RuntimeError(f"No normalized sample found for {pattern}")
    return candidates[-1]


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def normalize_google(record: dict, source_file: Path) -> dict:
    return {
        "source": "google_play",
        "store_app_id": record.get("package_name"),
        "app_name": record.get("app_name"),
        "category": record.get("category"),
        "storefront": "US/en_US",
        "review_id": record.get("review_id"),
        "review_title": None,
        "review_text": record.get("review_text"),
        "star_rating": record.get("star_rating"),
        "app_version": None,
        "review_timestamp": record.get("review_date"),
        "engagement_positive": record.get("helpful_count"),
        "engagement_total": None,
        "developer_reply_present": record.get("developer_reply_present"),
        "developer_reply_text": record.get("developer_reply_text"),
        "developer_reply_timestamp": record.get("developer_reply_date"),
        "ingested_at": record.get("ingested_at"),
        "source_file": str(source_file.relative_to(PROJECT_ROOT)),
    }


def normalize_apple(record: dict, source_file: Path) -> dict:
    return {
        "source": "apple_app_store",
        "store_app_id": record.get("app_id"),
        "app_name": record.get("app_name"),
        "category": record.get("category"),
        "storefront": record.get("storefront"),
        "review_id": record.get("review_id"),
        "review_title": record.get("review_title"),
        "review_text": record.get("review_text"),
        "star_rating": record.get("star_rating"),
        "app_version": record.get("app_version"),
        "review_timestamp": record.get("updated_at"),
        "engagement_positive": record.get("vote_sum"),
        "engagement_total": record.get("vote_count"),
        "developer_reply_present": False,
        "developer_reply_text": None,
        "developer_reply_timestamp": None,
        "ingested_at": record.get("ingested_at"),
        "source_file": str(source_file.relative_to(PROJECT_ROOT)),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_summary(records: list[dict], run_summaries: dict[str, dict]) -> list[dict]:
    rows = []
    for source in ("google_play", "apple_app_store"):
        selected = [record for record in records if record["source"] == source]
        run = run_summaries[source]
        target_apps = len({record["store_app_id"] for record in selected})
        ratings = [
            record["star_rating"]
            for record in selected
            if isinstance(record.get("star_rating"), int)
        ]
        text_lengths = [len(record.get("review_text") or "") for record in selected]
        ids = [record.get("review_id") for record in selected]
        comparison = run["run_comparison"]
        rows.append(
            {
                "source": source,
                "sample_surface": run["collection_configuration"]["surface"],
                "target_apps": target_apps,
                "records": len(selected),
                "records_per_target": round(len(selected) / target_apps, 2),
                "unique_review_ids": len({review_id for review_id in ids if review_id}),
                "duplicate_review_ids": len(ids) - len(set(ids)),
                "missing_review_text": sum(not record.get("review_text") for record in selected),
                "missing_star_rating": sum(record.get("star_rating") is None for record in selected),
                "missing_review_timestamp": sum(not record.get("review_timestamp") for record in selected),
                "records_with_title": sum(bool(record.get("review_title")) for record in selected),
                "records_with_app_version": sum(bool(record.get("app_version")) for record in selected),
                "records_with_developer_reply": sum(
                    bool(record.get("developer_reply_present")) for record in selected
                ),
                "average_star_rating": round(mean(ratings), 2) if ratings else None,
                "average_text_length_characters": round(mean(text_lengths), 2),
                "median_text_length_characters": round(median(text_lengths), 2),
                "repeat_shared_records": comparison.get("shared_records"),
                "repeat_new_records": comparison.get("new_records"),
                "repeat_absent_records": comparison.get(
                    "not_in_current_recent_page",
                    comparison.get("not_in_current_page_sample"),
                ),
                "repeat_changed_records": comparison.get("changed_records"),
                "ordering": (
                    "curated public-page cards"
                    if source == "google_play"
                    else "newest-first observed"
                ),
                "pagination": (
                    "no supported public pagination"
                    if source == "google_play"
                    else "10 pages advertised; page 1 tested"
                ),
                "authentication": (
                    "none for tested public surface; official API requires "
                    "developer authorization"
                ),
                "governance_status": (
                    "public HTML is undocumented; no supported cross-app pagination"
                    if source == "google_play"
                    else "legacy feed is not approved for recurring use without clearance"
                ),
            }
        )
    return rows


def app_summary(records: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        key = (record["source"], record["store_app_id"])
        grouped.setdefault(key, []).append(record)

    rows = []
    for (source, app_id), selected in sorted(grouped.items()):
        ratings = [
            record["star_rating"]
            for record in selected
            if isinstance(record.get("star_rating"), int)
        ]
        lengths = [len(record.get("review_text") or "") for record in selected]
        timestamps = sorted(
            record["review_timestamp"]
            for record in selected
            if record.get("review_timestamp")
        )
        distribution = Counter(ratings)
        rows.append(
            {
                "source": source,
                "store_app_id": app_id,
                "app_name": selected[0]["app_name"],
                "category": selected[0]["category"],
                "records": len(selected),
                "unique_review_ids": len(
                    {record["review_id"] for record in selected if record.get("review_id")}
                ),
                "average_star_rating": round(mean(ratings), 2) if ratings else None,
                "average_text_length_characters": round(mean(lengths), 2),
                "one_star_records": distribution[1],
                "two_star_records": distribution[2],
                "three_star_records": distribution[3],
                "four_star_records": distribution[4],
                "five_star_records": distribution[5],
                "oldest_review_timestamp": timestamps[0] if timestamps else None,
                "newest_review_timestamp": timestamps[-1] if timestamps else None,
            }
        )
    return rows


def main() -> None:
    google_file = latest_file("google_play_reviews_*.jsonl")
    apple_file = latest_file("apple_app_store_reviews_*.jsonl")
    google_records = [
        normalize_google(record, google_file) for record in load_jsonl(google_file)
    ]
    apple_records = [
        normalize_apple(record, apple_file) for record in load_jsonl(apple_file)
    ]
    records = google_records + apple_records

    run_summaries = {
        "google_play": json.loads(
            (PROJECT_ROOT / "results/google-play-01-public-page-test/run-summary.json").read_text()
        ),
        "apple_app_store": json.loads(
            (PROJECT_ROOT / "results/apple-app-store/run-summary.json").read_text()
        ),
    }

    write_csv(COMBINED_DATA_FILE, RECORD_FIELDS, records)
    source_rows = source_summary(records, run_summaries)
    write_csv(SOURCE_SUMMARY_FILE, list(source_rows[0]), source_rows)
    app_rows = app_summary(records)
    write_csv(APP_SUMMARY_FILE, list(app_rows[0]), app_rows)

    print(f"Combined records: {len(records)}")
    print(f"Local record table: {COMBINED_DATA_FILE}")
    print(f"Source summary: {SOURCE_SUMMARY_FILE}")
    print(f"App summary: {APP_SUMMARY_FILE}")


if __name__ == "__main__":
    main()
