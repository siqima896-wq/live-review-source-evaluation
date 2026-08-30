# Steam Review Ingestion — Run 2 Validation

## Run Information

- Run ID: 20260826T100948Z
- Collection date: 26 August 2026
- Games requested: 4
- Total records collected: 922
- Unique review keys: 922
- Duplicate keys in normalized output: 0

## Collection Results

| Game | App ID | Status | Reviews Collected |
|---|---:|---|---:|
| Portal 2 | 620 | Success | 300 |
| Stardew Valley | 413150 | Success | 300 |
| Cyberpunk 2077 | 1091500 | Success | 300 |
| Are You Happy | 3388440 | Success | 22 |

## Run-to-Run Comparison

| Game | Shared | New in Run 2 | Not in Run 2 Window | Updated |
|---|---:|---:|---:|---:|
| Portal 2 | 268 | 32 | 32 | 1 |
| Stardew Valley | 203 | 97 | 97 | 1 |
| Cyberpunk 2077 | 159 | 141 | 140 | 0 |
| Are You Happy | 22 | 0 | 0 | 0 |
| **Total** | **652** | **270** | **269** | **2** |

## Verified Findings

- The Steam review collection process completed successfully in two separate runs.
- The second run collected 922 unique normalized review records.
- A total of 652 review IDs appeared in both runs.
- A total of 270 review IDs appeared in Run 2 but not in Run 1.
- Two shared review records had a changed review timestamp and/or review text.
- Live collection of newly available review records was demonstrated.
- Cursor-based multi-page collection worked across the higher-volume games.
- No duplicate review keys were present in the normalized Run 2 output.
- All collected records were returned with the English-language filter.
- The latest collected review was created on 26 August 2026.

## Data Quality Findings

- Three Run 2 records contained no review text.
- All Run 2 records contained a recommendation ID.
- All Run 2 records contained a creation timestamp.
- Run 2 contained 884 positive and 38 negative reviews.
- The positive-review rate was 95.88%.
- The average review-text length was 135.26 characters.

## Interpretation

The results demonstrate that the Steam review endpoint supports
repeatable collection from a live source. The second run did not
simply reproduce the first sample: 270 new review IDs were observed
across the tested games.

The number of records that were not present in the second run should
not be interpreted as deleted reviews. Because the experiment
collected a fixed recent-review window, older records may leave that
window as newer reviews arrive.

The results also show that ingestion behaviour differs by product
activity. Cyberpunk 2077 produced 141 new records, while Are You Happy
produced no new records during the test interval.

## Analytical Considerations

- The sample is strongly imbalanced toward positive reviews.
- Empty review text must be handled during transformation.
- High-volume games can change substantially between collection runs.
- Low-volume games may produce no new records during a short interval.
- Steam remains limited to gaming-related users, products, and topics.

## Remaining Open Items

- The exact endpoint rate limit has not been established.
- Full historical depth has not been tested.
- Behaviour beyond the first 300 recent reviews has not been fully assessed.
- Broader analytical representativeness remains to be compared with other live
  sources.

## Evidence Files

- Raw normalized JSONL: generated locally and not included in this repository.
- [`results/steam/run_summary_20260825T111345Z.json`](../../results/steam/run_summary_20260825T111345Z.json)
- [`results/steam/run_summary_20260826T100948Z.json`](../../results/steam/run_summary_20260826T100948Z.json)
- [`results/steam/quality_report_steam_reviews_20260825T111345Z.json`](../../results/steam/quality_report_steam_reviews_20260825T111345Z.json)
- [`results/steam/quality_report_steam_reviews_20260826T100948Z.json`](../../results/steam/quality_report_steam_reviews_20260826T100948Z.json)
- [`results/steam/run_comparison_20260825T111345Z_to_20260826T100948Z.json`](../../results/steam/run_comparison_20260825T111345Z_to_20260826T100948Z.json)
