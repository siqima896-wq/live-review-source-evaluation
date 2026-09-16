"""Run a bounded, repeatable Google Play review test with a third-party tool.

This script uses the open-source ``google-play-scraper`` package. It is not a
Google API, is not supported by Google, and relies on undocumented Google Play
interfaces. The test is intentionally bounded to two pages for each target and
two immediate runs. Review text is written only to the ignored local data
directory; the committed result contains aggregate metrics only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from statistics import mean, median

from google_play_scraper import Sort, reviews


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play-third-party"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

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


def iso_datetime(value: object) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.astimezone()
        return value.astimezone(timezone.utc).isoformat()
    return None


def normalize_review(item: dict, target: dict, ingested_at: str) -> dict:
    """Keep analytical fields while dropping reviewer names and profile images."""
    return {
        "source": "google_play_third_party_google_play_scraper",
        "package_name": target["package_name"],
        "app_name": target["app_name"],
        "category": target["category"],
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


def collect_target(target: dict, page_size: int, pages: int, ingested_at: str):
    records: list[dict] = []
    page_metrics: list[dict] = []
    token = None

    for page_number in range(1, pages + 1):
        started = time.monotonic()
        if token is None and page_number == 1:
            items, next_token = reviews(
                target["package_name"],
                lang="en",
                country="us",
                sort=Sort.NEWEST,
                count=page_size,
            )
        else:
            items, next_token = reviews(
                target["package_name"], continuation_token=token
            )

        normalized = [normalize_review(item, target, ingested_at) for item in items]
        records.extend(normalized)
        has_continuation = bool(
            next_token is not None and getattr(next_token, "token", None)
        )
        page_metrics.append(
            {
                "page": page_number,
                "records": len(normalized),
                "continuation_available": has_continuation,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        )
        token = next_token
        if not has_continuation:
            break

    ids = [record.get("review_id") for record in records]
    unique_ids = {review_id for review_id in ids if review_id}
    return records, {
        **target,
        "status": "success" if records else "no_records_returned",
        "pages_requested": pages,
        "pages_returned": len(page_metrics),
        "records": len(records),
        "unique_review_ids": len(unique_ids),
        "duplicate_review_ids": len(ids) - len(unique_ids),
        "page_metrics": page_metrics,
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def stable_record_hash(record: dict) -> str:
    fields = {
        key: record.get(key)
        for key in (
            "review_text",
            "star_rating",
            "helpful_count",
            "review_created_version",
            "app_version",
            "review_timestamp",
            "developer_reply_text",
            "developer_reply_timestamp",
        )
    }
    payload = json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def record_map(records: list[dict]) -> dict[tuple[str, str], dict]:
    return {
        (record["package_name"], record["review_id"]): record
        for record in records
        if record.get("review_id")
    }


def compare_runs(run_1: list[dict], run_2: list[dict]) -> dict:
    first = record_map(run_1)
    second = record_map(run_2)
    shared = set(first) & set(second)
    changed = {
        key
        for key in shared
        if stable_record_hash(first[key]) != stable_record_hash(second[key])
    }
    target_comparisons = []
    for target in TARGETS:
        package_name = target["package_name"]
        first_target = {key for key in first if key[0] == package_name}
        second_target = {key for key in second if key[0] == package_name}
        shared_target = first_target & second_target
        changed_target = {key for key in changed if key[0] == package_name}
        target_comparisons.append(
            {
                "package_name": package_name,
                "app_name": target["app_name"],
                "run_1_records": len(first_target),
                "run_2_records": len(second_target),
                "shared_records": len(shared_target),
                "new_in_run_2": len(second_target - first_target),
                "absent_from_run_2": len(first_target - second_target),
                "changed_shared_records": len(changed_target),
            }
        )

    return {
        "shared_records": len(shared),
        "new_in_run_2": len(set(second) - set(first)),
        "absent_from_run_2": len(set(first) - set(second)),
        "changed_shared_records": len(changed),
        "run_1_overlap_rate": round(len(shared) / len(first), 4) if first else None,
        "run_2_overlap_rate": round(len(shared) / len(second), 4) if second else None,
        "by_target": target_comparisons,
    }


def quality_summary(records: list[dict]) -> dict:
    ids = [record.get("review_id") for record in records]
    unique_ids = {review_id for review_id in ids if review_id}
    ratings = [
        record["star_rating"]
        for record in records
        if isinstance(record.get("star_rating"), int)
    ]
    text_lengths = [len(record.get("review_text") or "") for record in records]
    timestamps = [
        record["review_timestamp"]
        for record in records
        if record.get("review_timestamp")
    ]
    fields = (
        "review_id",
        "review_text",
        "star_rating",
        "review_timestamp",
        "helpful_count",
    )
    return {
        "total_records": len(records),
        "unique_review_ids": len(unique_ids),
        "duplicate_review_ids": len(ids) - len(unique_ids),
        "missing_by_field": {
            field: sum(record.get(field) is None or record.get(field) == "" for record in records)
            for field in fields
        },
        "records_with_developer_reply": sum(
            bool(record.get("developer_reply_present")) for record in records
        ),
        "average_star_rating": round(mean(ratings), 2) if ratings else None,
        "average_text_length_characters": round(mean(text_lengths), 2) if text_lengths else None,
        "median_text_length_characters": round(median(text_lengths), 2) if text_lengths else None,
        "newest_review_timestamp": max(timestamps) if timestamps else None,
        "oldest_review_timestamp": min(timestamps) if timestamps else None,
    }


def run_collection(run_number: int, page_size: int, pages: int) -> tuple[list[dict], dict]:
    started_at = utc_now()
    ingested_at = started_at.isoformat()
    records: list[dict] = []
    targets: list[dict] = []
    errors: list[dict] = []

    for target in TARGETS:
        try:
            target_records, target_summary = collect_target(
                target, page_size, pages, ingested_at
            )
            records.extend(target_records)
            targets.append(target_summary)
        except Exception as error:  # Surface failures not swallowed by the library.
            errors.append(
                {
                    "package_name": target["package_name"],
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            targets.append(
                {**target, "status": "failed", "records": 0, "page_metrics": []}
            )

    finished_at = utc_now()
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ") + f"-run{run_number}"
    output_file = NORMALIZED_DIR / f"google_play_third_party_{run_id}.jsonl"
    write_jsonl(output_file, records)
    return records, {
        "run_number": run_number,
        "started_at": ingested_at,
        "finished_at": finished_at.isoformat(),
        "elapsed_seconds": round((finished_at - started_at).total_seconds(), 3),
        "status": "completed" if records and not errors else ("partial" if records else "failed"),
        "targets": targets,
        "quality": quality_summary(records),
        "errors": errors,
        "local_normalized_output": str(output_file.relative_to(PROJECT_ROOT)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--repeat-delay-seconds", type=float, default=2.0)
    args = parser.parse_args()
    if not 1 <= args.page_size <= 200:
        parser.error("--page-size must be between 1 and 200")
    if not 1 <= args.pages <= 5:
        parser.error("--pages must be between 1 and 5")
    if not 0 <= args.repeat_delay_seconds <= 300:
        parser.error("--repeat-delay-seconds must be between 0 and 300")
    return args


def main() -> None:
    args = parse_args()
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    run_1_records, run_1 = run_collection(1, args.page_size, args.pages)
    time.sleep(args.repeat_delay_seconds)
    run_2_records, run_2 = run_collection(2, args.page_size, args.pages)

    summary = {
        "source": "google_play",
        "method": "third_party_open_source_scraper",
        "official_google_api": False,
        "tool": {
            "name": "google-play-scraper",
            "version": version("google-play-scraper"),
            "project_url": "https://github.com/JoMingyu/google-play-scraper",
            "license": "MIT",
        },
        "evidence_status": "observed",
        "test_configuration": {
            "language": "en",
            "country": "us",
            "sort": "newest",
            "target_count": len(TARGETS),
            "page_size": args.page_size,
            "pages_per_target": args.pages,
            "maximum_records_per_target_per_run": args.page_size * args.pages,
            "repeat_delay_seconds": args.repeat_delay_seconds,
        },
        "runs": [run_1, run_2],
        "repeat_comparison": compare_runs(run_1_records, run_2_records),
        "limitations": [
            "This method uses a third-party open-source package, not an official Google API.",
            "The package depends on undocumented Google Play interfaces that can change without notice.",
            "The latest PyPI release tested is from 2024, increasing maintenance and breakage risk.",
            "The package catches some internal request or parsing exceptions and may return partial results without a detailed error.",
            "Continuation tokens demonstrate bounded pagination only; they do not prove historical completeness.",
            "Newest sorting, locale parameters, and returned timestamps do not prove reviewer location or representative sampling.",
            "An immediate repeat measures short-term reproducibility, not long-term production reliability.",
            "Successful technical access does not establish permission for recurring collection or downstream use.",
        ],
        "privacy_note": (
            "Reviewer names and profile images are discarded. Review and reply text is written "
            "only to ignored local JSONL files and is not committed."
        ),
    }
    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Aggregate summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
