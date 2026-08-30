"""Collect and summarize a small, cross-topic YouTube comment sample."""

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
RESULTS_DIR = PROJECT_ROOT / "results" / "youtube"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
MAX_RESULTS_PER_PAGE = 100
MAX_PAGES_PER_VIDEO = 2
REQUEST_TIMEOUT_SECONDS = 30

# The sample deliberately spans several kinds of public content. The IDs and
# titles were checked through YouTube's public oEmbed endpoint on 2026-08-30.
TARGETS = [
    {
        "video_id": "TitZV6k8zfA",
        "topic": "technology_product_review",
        "title": "The Worst Product I've Ever Reviewed... For Now",
        "channel": "Marques Brownlee",
    },
    {
        "video_id": "094y1Z2wpJg",
        "topic": "science_mathematics",
        "title": "The Simplest Math Problem No One Can Solve - Collatz Conjecture",
        "channel": "Veritasium",
    },
    {
        "video_id": "R0JKCYZ8hng",
        "topic": "education_music_neuroscience",
        "title": "How playing an instrument benefits your brain - Anita Collins",
        "channel": "TED-Ed",
    },
    {
        "video_id": "jNQXAC9IVRw",
        "topic": "platform_culture",
        "title": "Me at the zoo",
        "channel": "jawed",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_api_key() -> str:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                name, separator, value = line.partition("=")
                if separator and name.strip() == "YOUTUBE_API_KEY":
                    api_key = value.strip().strip('"').strip("'")
                    break
    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is not set. Enable YouTube Data API v3 in a "
            "Google Cloud project, create an API key, and place it in the "
            "local .env file or export it in the shell."
        )
    return api_key


def fetch_page(
    api_key: str,
    video_id: str,
    page_token: str | None = None,
) -> dict:
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": MAX_RESULTS_PER_PAGE,
        "order": "time",
        "textFormat": "plainText",
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token

    response = requests.get(
        API_URL,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "Siqi-Live-Source-Evaluation/0.1"},
    )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            f"YouTube returned HTTP {response.status_code} with invalid JSON"
        ) from error

    if response.status_code >= 400:
        api_error = payload.get("error", {})
        reasons = [
            item.get("reason")
            for item in api_error.get("errors", [])
            if item.get("reason")
        ]
        message = api_error.get("message", "YouTube API request failed")
        reason_text = ", ".join(reasons) if reasons else "unknown"
        raise RuntimeError(
            f"YouTube returned HTTP {response.status_code}: "
            f"{message} (reason: {reason_text})"
        )

    return payload


def normalize_comment(target: dict, thread: dict, ingested_at: str) -> dict:
    thread_snippet = thread.get("snippet", {})
    top_level = thread_snippet.get("topLevelComment", {})
    comment_snippet = top_level.get("snippet", {})

    return {
        "source": "youtube",
        "video_id": target["video_id"],
        "video_title": target["title"],
        "topic": target["topic"],
        "thread_id": thread.get("id"),
        "comment_id": top_level.get("id"),
        "comment_text": comment_snippet.get("textDisplay"),
        "published_at": comment_snippet.get("publishedAt"),
        "updated_at": comment_snippet.get("updatedAt"),
        "like_count": comment_snippet.get("likeCount"),
        "reply_count": thread_snippet.get("totalReplyCount"),
        "ingested_at": ingested_at,
    }


def collect_target(api_key: str, target: dict, ingested_at: str) -> tuple[list, dict]:
    records = []
    seen_comment_ids = set()
    page_token = None
    pages_fetched = 0
    final_next_page_token_present = False

    for _ in range(MAX_PAGES_PER_VIDEO):
        payload = fetch_page(api_key, target["video_id"], page_token)
        pages_fetched += 1

        for thread in payload.get("items", []):
            record = normalize_comment(target, thread, ingested_at)
            comment_id = record.get("comment_id")
            if not comment_id or comment_id in seen_comment_ids:
                continue
            seen_comment_ids.add(comment_id)
            records.append(record)

        page_token = payload.get("nextPageToken")
        final_next_page_token_present = bool(page_token)
        if not page_token:
            break

    target_summary = {
        **target,
        "status": "success",
        "pages_fetched": pages_fetched,
        "records_collected": len(records),
        "next_page_token_present_after_final_page": (
            final_next_page_token_present
        ),
    }
    return records, target_summary


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def compare_with_previous(
    current_records: list[dict],
    previous_file: Path | None,
) -> dict:
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
        record.get("comment_id"): record
        for record in previous_records
        if record.get("comment_id")
    }
    current_map = {
        record.get("comment_id"): record
        for record in current_records
        if record.get("comment_id")
    }

    shared_ids = set(previous_map) & set(current_map)
    changed_ids = {
        comment_id
        for comment_id in shared_ids
        if (
            previous_map[comment_id].get("comment_text")
            != current_map[comment_id].get("comment_text")
            or previous_map[comment_id].get("updated_at")
            != current_map[comment_id].get("updated_at")
        )
    }

    return {
        "status": "completed",
        "previous_file": str(previous_file.relative_to(PROJECT_ROOT)),
        "shared_records": len(shared_ids),
        "new_records": len(set(current_map) - set(previous_map)),
        "not_in_current_fixed_window": len(
            set(previous_map) - set(current_map)
        ),
        "changed_records": len(changed_ids),
    }


def build_quality_summary(records: list[dict]) -> dict:
    comment_ids = [record.get("comment_id") for record in records]
    text_lengths = [
        len(str(record.get("comment_text") or "").strip())
        for record in records
    ]
    edited_records = sum(
        record.get("published_at") != record.get("updated_at")
        for record in records
        if record.get("published_at") and record.get("updated_at")
    )

    return {
        "total_records": len(records),
        "unique_comment_ids": len({item for item in comment_ids if item}),
        "duplicate_comment_ids": len(comment_ids)
        - len({item for item in comment_ids if item}),
        "missing_comment_id": sum(not item for item in comment_ids),
        "missing_comment_text": sum(length == 0 for length in text_lengths),
        "average_text_length_characters": (
            round(mean(text_lengths), 2) if text_lengths else None
        ),
        "median_text_length_characters": (
            round(median(text_lengths), 2) if text_lengths else None
        ),
        "comments_with_different_published_and_updated_times": edited_records,
    }


def main() -> None:
    api_key = require_api_key()
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    previous_files = sorted(NORMALIZED_DIR.glob("youtube_comments_*.jsonl"))
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
            errors.append(
                {"video_id": target["video_id"], "error": str(error)}
            )
            target_summaries.append(
                {
                    **target,
                    "status": "failed",
                    "pages_fetched": 0,
                    "records_collected": 0,
                }
            )

    output_file = NORMALIZED_DIR / f"youtube_comments_{run_id}.jsonl"
    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    quality = build_quality_summary(records)
    comparison = compare_with_previous(records, previous_file)
    pages_fetched = sum(item.get("pages_fetched", 0) for item in target_summaries)

    summary = {
        "source": "youtube",
        "status": "completed" if records and not errors else (
            "partial" if records else "failed"
        ),
        "evidence_status": "observed" if records else "unverified",
        "run_id": run_id,
        "run_started_at": ingested_at,
        "collection_configuration": {
            "endpoint": "commentThreads.list",
            "order": "time",
            "text_format": "plainText",
            "max_results_per_page": MAX_RESULTS_PER_PAGE,
            "max_pages_per_video": MAX_PAGES_PER_VIDEO,
            "target_count": len(TARGETS),
            "top_level_comments_only": True,
        },
        "targets": target_summaries,
        "quality": quality,
        "run_comparison": comparison,
        "access": {
            "authentication": "API key",
            "quota_units_used_estimate": pages_fetched,
            "documented_quota_cost_per_page": 1,
        },
        "errors": errors,
        "normalized_output": str(output_file.relative_to(PROJECT_ROOT)),
        "privacy_note": (
            "Author display names and channel identifiers are not retained. "
            "Normalized comment text remains local and is ignored by Git."
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
