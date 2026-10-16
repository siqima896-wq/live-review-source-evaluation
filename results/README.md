# Results Guide

For the current Google Play analysis, start with
[`google-play-03-expanded-eda`](google-play-03-expanded-eda/) and the
[full EDA report](../docs/google-play/google_play_eda.md).

The Google Play folders follow the research sequence:

| Stage | Folder | Purpose | Main file |
|---|---|---|---|
| 01 | [`google-play-01-public-page-test`](google-play-01-public-page-test/) | Initial test of review cards visible on public app pages | [`run-summary.json`](google-play-01-public-page-test/run-summary.json) |
| 02 | [`google-play-02-third-party-validation`](google-play-02-third-party-validation/) | Bounded validation of the unofficial scraper, pagination, and repeatability | [`run-summary.json`](google-play-02-third-party-validation/run-summary.json) |
| 03 | [`google-play-03-expanded-eda`](google-play-03-expanded-eda/) | Expanded 20-app, 10-category exploratory analysis | [`analysis-summary.json`](google-play-03-expanded-eda/analysis-summary.json) |
| 04 | [`google-play-04-db-integration`](google-play-04-db-integration/) | Live collection, PostgreSQL load, repeat-run deduplication, and constraint validation | [`run-summary.json`](google-play-04-db-integration/run-summary.json) and [`validation-summary.json`](google-play-04-db-integration/validation-summary.json) |
| 05 | [`google-play-05-recurring-ingestion`](google-play-05-recurring-ingestion/) | Five-App recurring-ingestion test with cross-run change classification | [`round-01-run-summary.json`](google-play-05-recurring-ingestion/round-01-run-summary.json) and [`round-01-validation-summary.json`](google-play-05-recurring-ingestion/round-01-validation-summary.json) |

Review text and reviewer identifiers are not committed. These folders contain
aggregate summaries, tables, and charts only.
