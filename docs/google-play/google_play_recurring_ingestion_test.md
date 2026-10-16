# Google Play Recurring-Ingestion Test

Status: Round 1 completed; Round 2 pending after a longer interval

Round 1 date: 2026-10-16 America/Chicago (database timestamps are UTC)

## Objective

This bounded follow-up tests the existing PostgreSQL design under a more
realistic recurring-collection pattern. It keeps the schema unchanged and
expands the collection from two Apps and 50 reviews per App to five Apps and
200 reviews per App. A later round will use the same settings to measure:

1. review overlap across runs;
2. newly observed reviews;
3. changed review content or metadata; and
4. collection, mapping, or loading failures.

The collector still uses the unofficial `google-play-scraper` 1.2.7 package.
This is a bounded research test, not production scheduling or monitoring.

## Fixed configuration

| App | Package | Category | Reviews requested |
|---|---|---|---:|
| Duolingo | `com.duolingo` | Education | 200 |
| Spotify | `com.spotify.music` | Music & Audio | 200 |
| TikTok | `com.zhiliaoapp.musically` | Social | 200 |
| Discord | `com.discord` | Communication | 200 |
| DoorDash | `com.dd.doordash` | Food & Drink | 200 |

All rounds use the US storefront, English language request, newest sort order,
and the same 200-review limit. These settings must remain fixed for the later
round to be comparable.

## Round 1 results

Collection run ID: `d9114398-ef0b-48d9-81ff-5ab93031b3bb`

| App | Fetched | Mapped | New | Existing | Developer replies | Failed | Window days |
|---|---:|---:|---:|---:|---:|---:|---:|
| Duolingo | 200 | 200 | 200 | 0 | 0 | 0 | 0.2171 |
| Spotify | 200 | 200 | 200 | 0 | 34 | 0 | 0.2745 |
| TikTok | 200 | 200 | 200 | 0 | 143 | 0 | 0.2185 |
| Discord | 200 | 200 | 200 | 0 | 79 | 0 | 1.5691 |
| DoorDash | 200 | 200 | 200 | 0 | 0 | 0 | 1.9491 |
| **Total** | **1,000** | **1,000** | **1,000** | **0** | **256** | **0** |  |

Round 1 completed in 5.229 seconds. All five targets succeeded, all fetched
records mapped and loaded, and continuation tokens were available for every
App. No version-source mismatch warnings occurred.

The earlier database baseline sampled Duolingo and Spotify on 2026-10-10. By
Round 1, their newest-review windows had moved completely beyond that sample,
so none of the earlier 100 reviews reappeared. This is useful window-turnover
evidence, but it does not yet provide overlap or changed-review evidence. Those
outcomes require Round 2 with the same five-App configuration.

## Validation and database state

Round 1 reconciliation passed. The run summary expected five targets, five App
snapshots, and 1,000 observations; the database contained exactly those rows
for the run.

After Round 1, the cumulative local database contained:

| Table | Rows |
|---|---:|
| `apps` | 5 |
| `collection_runs` | 3 |
| `collection_targets` | 9 |
| `app_snapshots` | 9 |
| `reviews` | 1,100 |
| `review_observations` | 1,200 |
| `developer_replies` | 260 |

There were no duplicate review identity groups, orphan observations, invalid
first/last-seen orderings, or missing developer-reply rows. All six invalid-row
constraint probes were rejected. Overall validation status: **passed**.

## Change classification

For future rounds, every review already present in the database is classified
as changed, unchanged, or unknown by comparing its new content hash with its
latest prior observation. The hash covers review text, star rating, review
version, review timestamp, helpful count, developer reply text, and developer
reply timestamp. This prepares Round 2 to distinguish overlap from actual
content or metadata changes without changing the schema.

## Round 2 procedure

After approximately 48 hours, run:

```bash
.venv/bin/python src/google_play_db_integration.py \
  --target-profile recurring \
  --reviews-per-app 200 \
  --runs 1 \
  --delay-seconds 0.5 \
  --summary-file results/google-play-05-recurring-ingestion/round-02-run-summary.json

.venv/bin/python src/google_play_db_validation.py \
  --run-summary results/google-play-05-recurring-ingestion/round-02-run-summary.json \
  --validation-file results/google-play-05-recurring-ingestion/round-02-validation-summary.json
```

Round 2 should not recreate or clear the database. Keeping the existing rows is
necessary to measure overlap, new reviews, changes, and repeat observations.

## Evidence and privacy

- `round-01-run-summary.json` contains aggregate collection and loading evidence.
- `round-01-validation-summary.json` contains reconciliation and constraint results.
- Reviewer names and profile images are not retained.
- Review text remains only in the local PostgreSQL database and is not committed.
