# Steam Live Source Assessment

## 1. Assessment Purpose

This assessment evaluates Steam as a candidate live source for the
data ingestion module.

The purpose of the test was to determine whether Steam provides:

- structured programmatic access;
- repeatable collection from a live source;
- cursor-based pagination;
- newly available records across separate collection runs;
- review text, timestamps, recommendation labels, and useful metadata;
- data of sufficient quality for downstream analysis.

Steam is evaluated here as a technical candidate. This document does
not treat Steam as the final source recommendation because its
analytical breadth must still be compared with other live sources.

## 2. Test Scope

Four Steam applications were selected to represent different levels
of review activity:

| Game | App ID | Sample Role |
|---|---:|---|
| Portal 2 | 620 | Established, high-volume title |
| Stardew Valley | 413150 | Independent, high-volume title |
| Cyberpunk 2077 | 1091500 | Large commercial title |
| Are You Happy | 3388440 | Lower-volume title |

The same collection configuration was used in both runs:

- Filter: recent
- Language: English
- Review type: all
- Purchase type: all
- Maximum pages per game: 3
- Requested reviews per page: 100
- Delay between page requests: 1 second
- Request timeout: 30 seconds

## 3. Collection Runs

Two collection runs were completed on separate dates.

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Collection date | 25 August 2026 | 26 August 2026 |
| Total records | 921 | 922 |
| Unique review keys | 921 | 922 |
| Portal 2 | 300 | 300 |
| Stardew Valley | 300 | 300 |
| Cyberpunk 2077 | 299 | 300 |
| Are You Happy | 22 | 22 |
| Positive reviews | 882 | 884 |
| Negative reviews | 39 | 38 |

All four App IDs were collected successfully in both runs.

## 4. Run-to-Run Comparison

The two normalized outputs were compared using the combination of
`app_id` and `recommendation_id` as the unique review key.

| Game | Shared | New in Run 2 | Not in Run 2 Window | Updated |
|---|---:|---:|---:|---:|
| Portal 2 | 268 | 32 | 32 | 1 |
| Stardew Valley | 203 | 97 | 97 | 1 |
| Cyberpunk 2077 | 159 | 141 | 140 | 0 |
| Are You Happy | 22 | 0 | 0 | 0 |
| **Total** | **652** | **270** | **269** | **2** |

Run 2 contained 270 review IDs that were not present in Run 1. This
demonstrates that the collection process can retrieve newly available
records from the live endpoint.

Two shared review records had a changed review timestamp and/or review
text.

The 269 records that did not appear in Run 2 should not be described
as deleted reviews. The experiment collected a fixed recent-review
window, so older reviews may leave that window as new reviews arrive.

## 5. Ingestion Feasibility

### Verified

- The endpoint returned structured JSON for all four tested App IDs.
- The same collection process completed successfully on two separate dates.
- Cursor-based multi-page collection worked for the higher-volume games.
- Run 2 contained 270 review IDs not present in Run 1.
- Two shared records showed a changed timestamp and/or review text.
- The response contained review text, recommendation labels, timestamps,
  purchase indicators, playtime fields, and engagement metadata.
- The normalized output contained no duplicate `(app_id,
  recommendation_id)` keys.
- Both high-volume and low-volume applications could be processed using
  the same collection structure.

### Documentation Only

- Steam documentation describes the Store Reviews endpoint and its
  cursor-based pagination.
- Steam documentation states that up to 100 reviews may be requested
  per page.
- Steam documentation describes the available review and author fields.

### Open Items

- The exact endpoint rate limit has not been established.
- Behaviour under sustained or scheduled collection has not been tested.
- Full historical depth has not been measured.
- Collection beyond the first 300 recent reviews per application has
  not been fully assessed.
- A complete review of applicable usage terms has not yet been documented.

## 6. Data Quality and Analytical Value

Run 2 produced the following quality results:

- Total records: 922
- Unique review keys: 922
- Missing recommendation IDs: 0
- Missing review text: 3
- Missing creation timestamps: 0
- Positive reviews: 884
- Negative reviews: 38
- Positive-review percentage: 95.88%
- Average review-text length: 135.26 characters
- Latest review date: 26 August 2026

### Strengths

- Review text is available for downstream text analysis.
- Recommendation labels provide a direct positive/negative signal.
- Creation and update timestamps support incremental processing.
- Engagement, purchase, and playtime fields provide useful analytical
  context.
- Different applications show different levels of review activity.
- Newly available records were observed between the two runs.

### Limitations

- Three Run 2 records contained no review text and must be flagged or
  excluded before sentiment analysis.
- The sample is strongly imbalanced toward positive reviews.
- High-volume titles can change substantially within a recent-review
  window.
- Low-volume titles may produce no new records during a short test period.
- Steam users, products, and topics are limited to the gaming domain.
- The tested sample does not establish broad representativeness across
  consumer products or industries.

## 7. Preliminary Assessment

Steam has been validated as a technically feasible live source for
testing repeatable ingestion.

The two-run experiment demonstrated:

- successful repeated execution;
- cursor-based multi-page collection;
- collection of 270 newly observed review IDs;
- detection of changed records;
- stable normalized fields across multiple applications;
- useful text, label, timestamp, and metadata fields.

Steam is therefore a strong candidate for testing the ingestion
mechanics and building an initial reusable connector.

However, Steam should not yet be treated as the final source
recommendation. Its analytical scope is limited to gaming, and its
breadth should be compared with other sanctioned live sources before
a final decision is made.

## 8. Recommended Next Step

Use the Steam test as evidence that the ingestion approach works, then
continue the broader live-source comparison.

Additional candidate sources should be evaluated using the same
criteria:

- sanctioned and stable programmatic access;
- repeatable collection of new records;
- pagination, historical depth, and rate limits;
- review text, ratings, timestamps, and metadata;
- breadth of users, products, topics, and categories;
- expected scale and data quality;
- legal and terms-of-service constraints.

For every source, findings should continue to be classified as:

- Verified through a sample pull;
- Documentation only;
- Open item.

## 9. Evidence Files

### Collection Code

- `steam_sample_pull.py`
- `analyze_run.py`
- `compare_runs.py`

### Run 1

- Raw normalized JSONL was generated locally and is not committed.
- [`results/steam/run_summary_20260825T111345Z.json`](../../results/steam/run_summary_20260825T111345Z.json)
- [`results/steam/quality_report_steam_reviews_20260825T111345Z.json`](../../results/steam/quality_report_steam_reviews_20260825T111345Z.json)
- [`docs/steam/run1_validation.md`](run1_validation.md)

### Run 2

- Raw normalized JSONL was generated locally and is not committed.
- [`results/steam/run_summary_20260826T100948Z.json`](../../results/steam/run_summary_20260826T100948Z.json)
- [`results/steam/quality_report_steam_reviews_20260826T100948Z.json`](../../results/steam/quality_report_steam_reviews_20260826T100948Z.json)
- [`docs/steam/run2_validation.md`](run2_validation.md)

### Comparison

- [`results/steam/run_comparison_20260825T111345Z_to_20260826T100948Z.json`](../../results/steam/run_comparison_20260825T111345Z_to_20260826T100948Z.json)
