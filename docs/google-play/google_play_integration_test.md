# Google Play PostgreSQL Integration Test

Status: passed

Test date: 2026-10-11 America/Chicago (database timestamps are UTC)

## Objective

This test verifies the initial end-to-end implementation requested after schema
review:

1. collect reviews from the live Google Play source;
2. clean and map the returned fields into the proposed relational model;
3. write the mapped data to PostgreSQL successfully;
4. preserve collection context and repeated-run observations; and
5. verify key relationships and constraints after loading.

The collector uses the unofficial `google-play-scraper` 1.2.7 package. It is
not an official Google API and remains subject to the governance and
maintenance limitations documented in the source assessment.

## Environment and scope

| Item | Value |
|---|---|
| Database | PostgreSQL 15.19 via Postgres.app |
| Database name | `sciencia_google_play` |
| Local endpoint | `localhost:5433` |
| Apps | Duolingo and Spotify |
| Reviews requested | 50 per App per run |
| Runs | 2 immediate live runs |
| Storefront | US |
| Language request | English |
| Sort order | Newest |

No database password is stored in the repository; the documented connection is
only the password-free local development endpoint. Reviewer names and profile
images are never retained. Review text is stored in the local database for the
implemented schema but is excluded from committed test evidence.

## Results

### Run 1: initial load

| App | Package | Fetched | Mapped | New reviews | Observations | Failed |
|---|---|---:|---:|---:|---:|---:|
| Duolingo | `com.duolingo` | 50 | 50 | 50 | 50 | 0 |
| Spotify | `com.spotify.music` | 50 | 50 | 50 | 50 | 0 |
| **Total** |  | **100** | **100** | **100** | **100** | **0** |

### Run 2: repeat load

| App | Package | Fetched | Mapped | New reviews | Updated existing | Observations | Failed |
|---|---|---:|---:|---:|---:|---:|---:|
| Duolingo | `com.duolingo` | 50 | 50 | 0 | 50 | 50 | 0 |
| Spotify | `com.spotify.music` | 50 | 50 | 0 | 50 | 50 | 0 |
| **Total** |  | **100** | **100** | **0** | **100** | **100** | **0** |

The repeat run observed the same bounded newest-review window. The `reviews`
table remained at 100 unique rows, while `review_observations` increased to 200
rows. This is the intended behavior: one current review record can be linked to
multiple collection runs without duplicating its source identity.

## Collection-window context

| App | Oldest review (UTC) | Newest review (UTC) | Window days |
|---|---|---|---:|
| Duolingo | 2026-10-10 19:35:46 | 2026-10-10 21:11:26 | 0.0664 |
| Spotify | 2026-10-10 18:13:12 | 2026-10-10 21:09:46 | 0.1226 |

Both Apps returned the same count, but their observed time windows differ. The
values were stored on `collection_targets`, confirming that the EDA coverage
finding is preserved in the implemented database.

## Post-load database state

| Table | Rows |
|---|---:|
| `apps` | 2 |
| `collection_runs` | 2 |
| `collection_targets` | 4 |
| `app_snapshots` | 4 |
| `reviews` | 100 |
| `review_observations` | 200 |
| `developer_replies` | 4 |

There were no mapping failures, version-source mismatches, duplicate review
identity groups, orphan observations, invalid first/last-seen orderings, or
missing developer-reply rows for observations marked as replied.

## Relationship and constraint verification

All normal-load reconciliation checks passed. Each run stored two targets, two
app snapshots, and exactly 100 observations, matching the collector summary.

The validation script also attempted invalid writes inside a transaction. All
were rejected, and all probe rows were rolled back:

| Probe | Expected protection | Result |
|---|---|---|
| Rating of 6 | `reviews_rating_ck` | Rejected |
| Duplicate App/review ID | `reviews_app_source_id_uq` | Rejected |
| Review for nonexistent App | Review App foreign key | Rejected |
| Run ending before it starts | `collection_runs_finished_ck` | Rejected |
| Negative helpful count | `review_observations_helpful_ck` | Rejected |
| Observation with invalid run/App relationship | Composite target foreign key | Rejected |

Overall validation status: **passed**.

## Reproduction

The repository contains all implementation and setup assets:

- `scripts/setup_google_play_db.sh` creates the database and applies the DDL;
- `src/google_play_db_integration.py` performs live collection, mapping, and
  transactional loading;
- `src/google_play_db_validation.py` reconciles counts and exercises database
  constraints;
- `docs/google-play/google_play_schema.sql` is the implemented schema;
- `results/google-play-04-db-integration/run-summary.json` records aggregate
  collection and load results; and
- `results/google-play-04-db-integration/validation-summary.json` records the
  post-load checks and constraint results.

Exact commands are documented in the repository root README.

## Limitations and next review points

- The sample is intentionally small and uses newest English-language reviews
  returned for the US storefront; it is not statistically representative.
- Immediate repeat collection validates idempotent review upserts and repeated
  observations but does not test long-term review edits or window turnover.
- The third-party collector relies on undocumented Google Play interfaces and
  is not yet cleared for recurring production collection.
- Review text is sensitive free text. Production deployment should add access,
  retention, backup, and deletion controls before scaling collection.
