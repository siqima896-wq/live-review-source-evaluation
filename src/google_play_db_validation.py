"""Validate the loaded Google Play integration data and database constraints."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play-04-db-integration"
RUN_SUMMARY_FILE = RESULTS_DIR / "run-summary.json"
VALIDATION_FILE = RESULTS_DIR / "validation-summary.json"


def scalar(cursor: psycopg.Cursor[Any], query: str, params: tuple[Any, ...] = ()) -> Any:
    cursor.execute(query, params)
    return cursor.fetchone()[0]


def expect_rejection(
    cursor: psycopg.Cursor[Any], name: str, statement: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any]:
    savepoint = f"probe_{name}"
    cursor.execute(f"SAVEPOINT {savepoint}")
    try:
        cursor.execute(statement, params)
    except psycopg.Error as error:
        cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        cursor.execute(f"RELEASE SAVEPOINT {savepoint}")
        return {
            "name": name,
            "passed": True,
            "rejected_by": error.diag.constraint_name,
            "sqlstate": error.sqlstate,
        }
    cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
    cursor.execute(f"RELEASE SAVEPOINT {savepoint}")
    return {"name": name, "passed": False, "error": "invalid row was accepted"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.environ.get(
            "GOOGLE_PLAY_DATABASE_URL",
            "postgresql://localhost:5433/sciencia_google_play",
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not RUN_SUMMARY_FILE.exists():
        raise SystemExit(f"Run the integration first; missing {RUN_SUMMARY_FILE}")
    run_summary = json.loads(RUN_SUMMARY_FILE.read_text(encoding="utf-8"))
    run_ids = [run["collection_run_id"] for run in run_summary["runs"]]

    with psycopg.connect(args.dsn) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                database_version = scalar(cursor, "SELECT version()")
                table_counts = {
                    table: scalar(cursor, f"SELECT count(*) FROM {table}")
                    for table in (
                        "apps", "collection_runs", "collection_targets",
                        "app_snapshots", "reviews", "review_observations",
                        "developer_replies",
                    )
                }
                duplicate_reviews = scalar(
                    cursor,
                    """
                    SELECT count(*) FROM (
                        SELECT app_id, source_review_id
                        FROM reviews GROUP BY app_id, source_review_id
                        HAVING count(*) > 1
                    ) duplicate_groups
                    """,
                )
                orphan_observations = scalar(
                    cursor,
                    """
                    SELECT count(*)
                    FROM review_observations observation
                    LEFT JOIN reviews review
                      ON review.review_pk = observation.review_pk
                     AND review.app_id = observation.app_id
                    LEFT JOIN collection_targets target
                      ON target.collection_run_id = observation.collection_run_id
                     AND target.app_id = observation.app_id
                    WHERE review.review_pk IS NULL OR target.app_id IS NULL
                    """,
                )
                invalid_seen_order = scalar(
                    cursor,
                    "SELECT count(*) FROM reviews WHERE last_seen_at < first_seen_at",
                )
                missing_expected_replies = scalar(
                    cursor,
                    """
                    SELECT count(*)
                    FROM review_observations observation
                    LEFT JOIN developer_replies reply
                      ON reply.review_pk = observation.review_pk
                    WHERE observation.developer_reply_present
                      AND reply.review_pk IS NULL
                    """,
                )

                per_run = []
                for expected_run in run_summary["runs"]:
                    run_id = expected_run["collection_run_id"]
                    stored_targets = scalar(
                        cursor,
                        "SELECT count(*) FROM collection_targets WHERE collection_run_id = %s",
                        (run_id,),
                    )
                    stored_observations = scalar(
                        cursor,
                        "SELECT count(*) FROM review_observations WHERE collection_run_id = %s",
                        (run_id,),
                    )
                    stored_snapshots = scalar(
                        cursor,
                        "SELECT count(*) FROM app_snapshots WHERE collection_run_id = %s",
                        (run_id,),
                    )
                    expected_observations = expected_run["totals"]["observations_inserted"]
                    per_run.append(
                        {
                            "collection_run_id": run_id,
                            "expected_targets": len(expected_run["targets"]),
                            "stored_targets": stored_targets,
                            "expected_observations": expected_observations,
                            "stored_observations": stored_observations,
                            "stored_snapshots": stored_snapshots,
                            "passed": (
                                stored_targets == len(expected_run["targets"])
                                and stored_observations == expected_observations
                                and stored_snapshots
                                == sum(target["status"] != "failed" for target in expected_run["targets"])
                            ),
                        }
                    )

                cursor.execute(
                    """
                    SELECT app_id, source_review_id, review_text, star_rating,
                           review_version, reviewed_at, first_seen_at, last_seen_at
                    FROM reviews ORDER BY review_pk LIMIT 1
                    """
                )
                sample_review = cursor.fetchone()
                if sample_review is None:
                    raise RuntimeError("No reviews are available for constraint validation")
                app_id = int(sample_review[0])
                now = datetime.now(timezone.utc)
                invalid_app_id = int(scalar(cursor, "SELECT max(app_id) FROM apps")) + 100000

                constraint_tests = [
                    expect_rejection(
                        cursor,
                        "rating_range",
                        """
                        INSERT INTO reviews (
                            app_id, source_review_id, review_text, star_rating,
                            reviewed_at, first_seen_at, last_seen_at
                        ) VALUES (%s, 'constraint-probe-rating', 'probe', 6, %s, %s, %s)
                        """,
                        (app_id, now, now, now),
                    ),
                    expect_rejection(
                        cursor,
                        "duplicate_review_identity",
                        """
                        INSERT INTO reviews (
                            app_id, source_review_id, review_text, star_rating,
                            review_version, reviewed_at, first_seen_at, last_seen_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        sample_review,
                    ),
                    expect_rejection(
                        cursor,
                        "review_app_foreign_key",
                        """
                        INSERT INTO reviews (
                            app_id, source_review_id, review_text, star_rating,
                            reviewed_at, first_seen_at, last_seen_at
                        ) VALUES (%s, 'constraint-probe-orphan', 'probe', 5, %s, %s, %s)
                        """,
                        (invalid_app_id, now, now, now),
                    ),
                    expect_rejection(
                        cursor,
                        "run_time_order",
                        """
                        INSERT INTO collection_runs (
                            collection_method, collector_name, started_at, finished_at,
                            requested_language, requested_country, sort_order,
                            reviews_requested_per_app, target_app_count, status
                        ) VALUES (
                            'constraint_probe', 'constraint_probe', %s, %s,
                            'en', 'US', 'newest', 1, 0, 'completed'
                        )
                        """,
                        (now, now - timedelta(seconds=1)),
                    ),
                ]

                cursor.execute(
                    """
                    INSERT INTO reviews (
                        app_id, source_review_id, review_text, star_rating,
                        reviewed_at, first_seen_at, last_seen_at
                    ) VALUES (%s, 'constraint-probe-observation', 'probe', 5, %s, %s, %s)
                    RETURNING review_pk
                    """,
                    (app_id, now, now, now),
                )
                temporary_review_pk = int(cursor.fetchone()[0])
                constraint_tests.append(
                    expect_rejection(
                        cursor,
                        "helpful_count_nonnegative",
                        """
                        INSERT INTO review_observations (
                            collection_run_id, review_pk, app_id, observed_at,
                            helpful_count, developer_reply_present
                        ) VALUES (%s, %s, %s, %s, -1, false)
                        """,
                        (run_ids[0], temporary_review_pk, app_id, now),
                    )
                )
                constraint_tests.append(
                    expect_rejection(
                        cursor,
                        "observation_review_app_relationship",
                        """
                        INSERT INTO review_observations (
                            collection_run_id, review_pk, app_id, observed_at,
                            helpful_count, developer_reply_present
                        ) VALUES (%s, %s, %s, %s, 0, false)
                        """,
                        (run_ids[0], temporary_review_pk, invalid_app_id, now),
                    )
                )
                # Discard the temporary valid row as well as every constraint probe.
                # psycopg.Rollback cleanly exits this transaction context without
                # committing or surfacing an exception to the caller.
                raise psycopg.Rollback()

    integrity_checks = {
        "no_duplicate_reviews": duplicate_reviews == 0,
        "no_orphan_observations": orphan_observations == 0,
        "valid_seen_time_order": invalid_seen_order == 0,
        "developer_reply_rows_present_when_expected": missing_expected_replies == 0,
        "run_counts_match_summary": all(run["passed"] for run in per_run),
        "all_constraint_probes_rejected": all(test["passed"] for test in constraint_tests),
    }
    validation = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "database_version": database_version,
        "validated_collection_run_ids": run_ids,
        "table_counts": table_counts,
        "per_run_reconciliation": per_run,
        "integrity_metrics": {
            "duplicate_review_groups": duplicate_reviews,
            "orphan_observations": orphan_observations,
            "invalid_seen_time_order": invalid_seen_order,
            "missing_expected_developer_replies": missing_expected_replies,
        },
        "integrity_checks": integrity_checks,
        "constraint_tests": constraint_tests,
        "overall_status": "passed" if all(integrity_checks.values()) else "failed",
        "transaction_note": "All invalid-row probes and temporary rows were rolled back.",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_FILE.write_text(
        json.dumps(validation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    if validation["overall_status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
