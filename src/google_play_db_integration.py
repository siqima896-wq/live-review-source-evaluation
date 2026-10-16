"""Collect a bounded live Google Play sample and load it into PostgreSQL.

The source is the unofficial ``google-play-scraper`` package. Reviewer names
and profile images are never retained. Aggregate run evidence is safe to keep
in Git; review text remains only in the local database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from typing import Any

import psycopg
from google_play_scraper import Sort, app, reviews


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play-04-db-integration"
SUMMARY_FILE = RESULTS_DIR / "run-summary.json"

BASELINE_TARGETS = (
    {
        "package_name": "com.duolingo",
        "display_name": "Duolingo: Language Lessons",
        "category_name": "Education",
    },
    {
        "package_name": "com.spotify.music",
        "display_name": "Spotify: Music and Podcasts",
        "category_name": "Music & Audio",
    },
)

RECURRING_TARGETS = (
    *BASELINE_TARGETS,
    {
        "package_name": "com.zhiliaoapp.musically",
        "display_name": "TikTok",
        "category_name": "Social",
    },
    {
        "package_name": "com.discord",
        "display_name": "Discord: Talk, Play, Hang Out",
        "category_name": "Communication",
    },
    {
        "package_name": "com.dd.doordash",
        "display_name": "DoorDash: Food, Grocery, More",
        "category_name": "Food & Drink",
    },
)

TARGET_PROFILES = {
    "baseline": BASELINE_TARGETS,
    "recurring": RECURRING_TARGETS,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def parse_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    for pattern in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None


def parse_store_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return None


def normalize_review(item: dict[str, Any], observed_at: datetime) -> dict[str, Any]:
    review_id = item.get("reviewId")
    review_text = item.get("content")
    rating = item.get("score")
    reviewed_at = item.get("at")
    helpful_count = item.get("thumbsUpCount")

    if not isinstance(review_id, str) or not review_id.strip():
        raise ValueError("reviewId is missing")
    if not isinstance(review_text, str):
        raise ValueError("content is missing or is not text")
    if not isinstance(rating, int) or isinstance(rating, bool) or not 1 <= rating <= 5:
        raise ValueError("score is not an integer from 1 through 5")
    if not isinstance(reviewed_at, datetime):
        raise ValueError("review timestamp is missing or invalid")
    if reviewed_at.tzinfo is None:
        reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)
    else:
        reviewed_at = reviewed_at.astimezone(timezone.utc)
    if helpful_count is None:
        helpful_count = 0
    if not isinstance(helpful_count, int) or isinstance(helpful_count, bool) or helpful_count < 0:
        raise ValueError("thumbsUpCount is not a nonnegative integer")

    created_version = item.get("reviewCreatedVersion")
    app_version = item.get("appVersion")
    version_mismatch = bool(
        created_version and app_version and created_version != app_version
    )
    reply_text = item.get("replyContent")
    replied_at = item.get("repliedAt")
    if isinstance(replied_at, datetime):
        if replied_at.tzinfo is None:
            replied_at = replied_at.replace(tzinfo=timezone.utc)
        else:
            replied_at = replied_at.astimezone(timezone.utc)
    else:
        replied_at = None

    record = {
        "source_review_id": review_id,
        "review_text": review_text,
        "star_rating": rating,
        "review_version": created_version or app_version,
        "reviewed_at": reviewed_at,
        "observed_at": observed_at,
        "helpful_count": helpful_count,
        "developer_reply_present": isinstance(reply_text, str),
        "reply_text": reply_text if isinstance(reply_text, str) else None,
        "replied_at": replied_at,
        "version_mismatch": version_mismatch,
    }
    hash_payload = {
        key: json_value(record[key])
        for key in (
            "review_text",
            "star_rating",
            "review_version",
            "reviewed_at",
            "helpful_count",
            "reply_text",
            "replied_at",
        )
    }
    record["content_hash"] = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return record


def upsert_app(cursor: psycopg.Cursor[Any], target: dict[str, str]) -> int:
    cursor.execute(
        """
        INSERT INTO apps (source, package_name, display_name, category_name)
        VALUES ('google_play', %s, %s, %s)
        ON CONFLICT (source, package_name) DO UPDATE
        SET display_name = EXCLUDED.display_name,
            category_name = EXCLUDED.category_name
        RETURNING app_id
        """,
        (
            target["package_name"],
            target["display_name"],
            target["category_name"],
        ),
    )
    return int(cursor.fetchone()[0])


def insert_snapshot(
    cursor: psycopg.Cursor[Any], run_id: str, app_id: int, details: dict[str, Any],
    captured_at: datetime,
) -> None:
    currency = details.get("currency")
    if isinstance(currency, str):
        currency = currency.upper()[:3]
    else:
        currency = None
    cursor.execute(
        """
        INSERT INTO app_snapshots (
            collection_run_id, app_id, captured_at, store_title, store_genre,
            store_genre_id, store_score, ratings_count, reviews_count,
            installs_label, minimum_installs, real_installs, price_amount,
            is_free, currency_code, developer_name, released_on,
            store_updated_at, version_name, content_rating, ad_supported,
            contains_ads, offers_iap
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            run_id, app_id, captured_at, details.get("title"),
            details.get("genre"), details.get("genreId"), details.get("score"),
            details.get("ratings"), details.get("reviews"), details.get("installs"),
            details.get("minInstalls"), details.get("realInstalls"),
            details.get("price"), details.get("free"), currency,
            details.get("developer"), parse_date(details.get("released")),
            parse_store_timestamp(details.get("updated")), details.get("version"),
            details.get("contentRating"), details.get("adSupported"),
            details.get("containsAds"), details.get("offersIAP"),
        ),
    )


def upsert_review(
    cursor: psycopg.Cursor[Any], app_id: int, record: dict[str, Any]
) -> tuple[int, bool]:
    cursor.execute(
        """
        INSERT INTO reviews (
            app_id, source_review_id, review_text, star_rating, review_version,
            reviewed_at, first_seen_at, last_seen_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (app_id, source_review_id) DO UPDATE
        SET review_text = EXCLUDED.review_text,
            star_rating = EXCLUDED.star_rating,
            review_version = EXCLUDED.review_version,
            reviewed_at = EXCLUDED.reviewed_at,
            last_seen_at = EXCLUDED.last_seen_at,
            updated_at = now()
        RETURNING review_pk, (xmax = 0) AS inserted
        """,
        (
            app_id, record["source_review_id"], record["review_text"],
            record["star_rating"], record["review_version"],
            record["reviewed_at"], record["observed_at"], record["observed_at"],
        ),
    )
    review_pk, inserted = cursor.fetchone()
    return int(review_pk), bool(inserted)


def load_target(
    connection: psycopg.Connection[Any], run_id: str, target: dict[str, str],
    review_count: int,
) -> dict[str, Any]:
    started = time.monotonic()
    observed_at = utc_now()
    details = app(target["package_name"], lang="en", country="us")
    items, continuation_token = reviews(
        target["package_name"], lang="en", country="us", sort=Sort.NEWEST,
        count=review_count,
    )

    failures: list[dict[str, Any]] = []
    normalized_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        try:
            record = normalize_review(item, observed_at)
            normalized_by_id[record["source_review_id"]] = record
        except (TypeError, ValueError) as error:
            failures.append(
                {
                    "record_index": index,
                    "source_review_id": item.get("reviewId"),
                    "stage": "mapping",
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            )

    timestamps = [record["reviewed_at"] for record in normalized_by_id.values()]
    oldest = min(timestamps) if timestamps else None
    newest = max(timestamps) if timestamps else None
    window_days = (
        Decimal(str(round((newest - oldest).total_seconds() / 86400, 4)))
        if oldest and newest else None
    )
    inserted_new = 0
    updated_existing = 0
    changed_existing = 0
    unchanged_existing = 0
    change_status_unknown = 0
    replies_stored = 0
    version_mismatches = 0

    with connection.transaction():
        with connection.cursor() as cursor:
            app_id = upsert_app(cursor, target)
            cursor.execute(
                """
                INSERT INTO collection_targets (
                    collection_run_id, app_id, status, records_collected,
                    unique_review_ids, continuation_available, elapsed_seconds,
                    oldest_review_at, newest_review_at, observed_window_days
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id, app_id, "success" if items else "no_records_returned",
                    len(items), len({item.get("reviewId") for item in items if item.get("reviewId")}),
                    continuation_token is not None,
                    Decimal(str(round(time.monotonic() - started, 3))),
                    oldest, newest, window_days,
                ),
            )
            insert_snapshot(cursor, run_id, app_id, details, observed_at)

            for record in normalized_by_id.values():
                cursor.execute(
                    """
                    SELECT review_pk
                    FROM reviews
                    WHERE app_id = %s AND source_review_id = %s
                    """,
                    (app_id, record["source_review_id"]),
                )
                existing_review = cursor.fetchone()
                previous_hash = None
                if existing_review is not None:
                    cursor.execute(
                        """
                        SELECT content_hash
                        FROM review_observations
                        WHERE review_pk = %s
                        ORDER BY observed_at DESC
                        LIMIT 1
                        """,
                        (existing_review[0],),
                    )
                    previous_observation = cursor.fetchone()
                    if previous_observation is not None:
                        previous_hash = previous_observation[0]

                review_pk, inserted = upsert_review(cursor, app_id, record)
                inserted_new += int(inserted)
                updated_existing += int(not inserted)
                if not inserted:
                    if previous_hash is None:
                        change_status_unknown += 1
                    elif previous_hash == record["content_hash"]:
                        unchanged_existing += 1
                    else:
                        changed_existing += 1
                version_mismatches += int(record["version_mismatch"])
                cursor.execute(
                    """
                    INSERT INTO review_observations (
                        collection_run_id, review_pk, app_id, observed_at,
                        helpful_count, developer_reply_present, content_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id, review_pk, app_id, record["observed_at"],
                        record["helpful_count"], record["developer_reply_present"],
                        record["content_hash"],
                    ),
                )
                if record["developer_reply_present"]:
                    replies_stored += 1
                    cursor.execute(
                        """
                        INSERT INTO developer_replies (
                            review_pk, reply_text, replied_at, first_seen_at, last_seen_at
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (review_pk) DO UPDATE
                        SET reply_text = EXCLUDED.reply_text,
                            replied_at = EXCLUDED.replied_at,
                            last_seen_at = EXCLUDED.last_seen_at,
                            updated_at = now()
                        """,
                        (
                            review_pk, record["reply_text"], record["replied_at"],
                            record["observed_at"], record["observed_at"],
                        ),
                    )

    return {
        "package_name": target["package_name"],
        "display_name": target["display_name"],
        "category_name": target["category_name"],
        "status": "success" if items and not failures else (
            "partial" if normalized_by_id else "no_records_returned"
        ),
        "requested": review_count,
        "fetched": len(items),
        "unique_review_ids_fetched": len(
            {item.get("reviewId") for item in items if item.get("reviewId")}
        ),
        "mapped_successfully": len(normalized_by_id),
        "inserted_new": inserted_new,
        "updated_existing": updated_existing,
        "changed_existing": changed_existing,
        "unchanged_existing": unchanged_existing,
        "change_status_unknown": change_status_unknown,
        "observations_inserted": len(normalized_by_id),
        "developer_replies_stored": replies_stored,
        "failed_records": len(failures),
        "version_mismatch_warnings": version_mismatches,
        "continuation_available": continuation_token is not None,
        "oldest_review_at": json_value(oldest),
        "newest_review_at": json_value(newest),
        "observed_window_days": json_value(window_days),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "failures": failures,
    }


def record_failed_target(
    connection: psycopg.Connection[Any], run_id: str, target: dict[str, str],
    error: Exception, elapsed_seconds: float,
) -> None:
    with connection.transaction():
        with connection.cursor() as cursor:
            app_id = upsert_app(cursor, target)
            cursor.execute(
                """
                INSERT INTO collection_targets (
                    collection_run_id, app_id, status, records_collected,
                    unique_review_ids, elapsed_seconds, error_type, error_message
                ) VALUES (%s, %s, 'failed', 0, 0, %s, %s, %s)
                """,
                (
                    run_id, app_id, Decimal(str(round(elapsed_seconds, 3))),
                    type(error).__name__, str(error)[:2000],
                ),
            )


def run_once(
    connection: psycopg.Connection[Any], review_count: int, delay_seconds: float,
    run_number: int, targets_to_collect: tuple[dict[str, str], ...],
) -> dict[str, Any]:
    started_at = utc_now()
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO collection_runs (
                    source, collection_method, collector_name, collector_version,
                    official_api, started_at, requested_language, requested_country,
                    sort_order, reviews_requested_per_app, target_app_count,
                    delay_seconds, status
                ) VALUES (
                    'google_play', 'third_party_open_source_scraper',
                    'google-play-scraper', %s, false, %s, 'en', 'US', 'newest',
                    %s, %s, %s, 'running'
                ) RETURNING collection_run_id
                """,
                (
                    version("google-play-scraper"), started_at, review_count,
                    len(targets_to_collect), Decimal(str(delay_seconds)),
                ),
            )
            run_id = str(cursor.fetchone()[0])

    targets: list[dict[str, Any]] = []
    for index, target in enumerate(targets_to_collect):
        target_started = time.monotonic()
        try:
            targets.append(load_target(connection, run_id, target, review_count))
        except Exception as error:
            record_failed_target(
                connection, run_id, target, error, time.monotonic() - target_started
            )
            targets.append(
                {
                    "package_name": target["package_name"],
                    "display_name": target["display_name"],
                    "category_name": target["category_name"],
                    "status": "failed",
                    "requested": review_count,
                    "fetched": 0,
                    "mapped_successfully": 0,
                    "inserted_new": 0,
                    "updated_existing": 0,
                    "changed_existing": 0,
                    "unchanged_existing": 0,
                    "change_status_unknown": 0,
                    "observations_inserted": 0,
                    "failed_records": 0,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            )
        if index < len(targets_to_collect) - 1:
            time.sleep(delay_seconds)

    completed_targets = sum(target["status"] == "success" for target in targets)
    partial_targets = sum(target["status"] == "partial" for target in targets)
    if completed_targets == len(targets_to_collect):
        status = "completed"
    elif completed_targets or partial_targets:
        status = "partial"
    else:
        status = "failed"
    finished_at = utc_now()
    errors = [
        target["error_message"]
        for target in targets
        if target["status"] == "failed" and target.get("error_message")
    ]
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE collection_runs
                SET finished_at = %s, status = %s, error_message = %s
                WHERE collection_run_id = %s
                """,
                (finished_at, status, "; ".join(errors)[:4000] or None, run_id),
            )
    return {
        "run_number": run_number,
        "collection_run_id": run_id,
        "status": status,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "elapsed_seconds": round((finished_at - started_at).total_seconds(), 3),
        "targets": targets,
        "totals": {
            key: sum(int(target.get(key, 0)) for target in targets)
            for key in (
                "fetched", "mapped_successfully", "inserted_new",
                "updated_existing", "changed_existing", "unchanged_existing",
                "change_status_unknown", "observations_inserted", "failed_records",
            )
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.environ.get(
            "GOOGLE_PLAY_DATABASE_URL",
            "postgresql://localhost:5433/sciencia_google_play",
        ),
        help="PostgreSQL DSN; defaults to GOOGLE_PLAY_DATABASE_URL or local port 5433",
    )
    parser.add_argument("--reviews-per-app", type=int, default=50)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    parser.add_argument("--repeat-delay-seconds", type=float, default=2.0)
    parser.add_argument(
        "--target-profile",
        choices=tuple(TARGET_PROFILES),
        default="baseline",
        help="baseline keeps the original two-App test; recurring uses five Apps",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=SUMMARY_FILE,
        help="aggregate JSON output path; relative paths resolve from the repository root",
    )
    args = parser.parse_args()
    if not 1 <= args.reviews_per_app <= 200:
        parser.error("--reviews-per-app must be between 1 and 200")
    if not 1 <= args.runs <= 5:
        parser.error("--runs must be between 1 and 5")
    if not 0 <= args.delay_seconds <= 30:
        parser.error("--delay-seconds must be between 0 and 30")
    if not 0 <= args.repeat_delay_seconds <= 300:
        parser.error("--repeat-delay-seconds must be between 0 and 300")
    return args


def main() -> None:
    args = parse_args()
    targets_to_collect = TARGET_PROFILES[args.target_profile]
    summary_file = args.summary_file
    if not summary_file.is_absolute():
        summary_file = PROJECT_ROOT / summary_file
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(args.dsn) as connection:
        runs = []
        for run_number in range(1, args.runs + 1):
            runs.append(
                run_once(
                    connection, args.reviews_per_app, args.delay_seconds,
                    run_number, targets_to_collect,
                )
            )
            if run_number < args.runs:
                time.sleep(args.repeat_delay_seconds)

    summary = {
        "test": "bounded live Google Play to PostgreSQL integration",
        "source": "google_play",
        "method": "third_party_open_source_scraper",
        "official_google_api": False,
        "collector": {
            "name": "google-play-scraper",
            "version": version("google-play-scraper"),
        },
        "database": {"product": "PostgreSQL", "schema_version": "baseline-v1"},
        "configuration": {
            "target_profile": args.target_profile,
            "apps": list(targets_to_collect),
            "reviews_requested_per_app": args.reviews_per_app,
            "runs": args.runs,
            "language": "en",
            "country": "US",
            "sort": "newest",
        },
        "runs": runs,
        "privacy_note": (
            "Reviewer names and profile images were not retained. Review text is "
            "stored only in the local database and is not included in this summary."
        ),
        "sampling_note": (
            "Newest English-language reviews returned for the US storefront are a "
            "bounded convenience sample, not a representative population sample."
        ),
    }
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=json_value) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=json_value))
    print(f"Aggregate summary: {summary_file}")


if __name__ == "__main__":
    main()
