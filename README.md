# Live Review Source Evaluation

This repository compares the live-ingestion feasibility, analytical value,
and access requirements of Steam, YouTube, TMDB, Google Play, and the Apple App
Store.

## Current status

- Steam: two-run live-ingestion test completed.
- YouTube: two-run, cross-topic sample pull completed; Run 2 refreshed on 2026-09-02.
- TMDB: two-run live sample pull completed (61 reviews from 4 films in each run).
- Google Play: bounded public-page sample completed (9 displayed cards), plus a
  third-party open-source test that returned 600 reviews per run across 3 app
  categories with two-page pagination and 100% ID overlap on immediate repeat.
  The third-party method is not an official Google API and is not cleared for
  recurring production use.
- Apple App Store: bounded legacy-feed sample and repeat completed (150 reviews
  from 3 app categories); technical quality is strong, but recurring use is not
  recommended without resolving the documented governance restrictions.

## Project documentation

- [Source comparison](docs/source-comparison.md)
- [Steam source assessment](docs/steam/steam_source_assessment.md)
- [Steam Run 1 validation](docs/steam/run1_validation.md)
- [Steam Run 2 validation](docs/steam/run2_validation.md)
- [YouTube run summary](results/youtube/run-summary.json)
- [TMDB run summary](results/tmdb/run-summary.json)
- [Google Play source assessment](docs/google-play/google_play_source_assessment.md)
- [Google Play run summary](results/google-play/run-summary.json)
- [Google Play third-party test](docs/google-play/google_play_third_party_test.md)
- [Google Play third-party aggregate results](results/google-play-third-party/run-summary.json)
- [Apple App Store source assessment](docs/apple-app-store/apple_app_store_source_assessment.md)
- [Apple App Store run summary](results/apple-app-store/run-summary.json)
- [Combined app-store data tables](docs/app-store-comparison.md)
- [Combined source summary CSV](results/app-stores/combined-source-summary.csv)
- [Combined app summary CSV](results/app-stores/combined-app-summary.csv)

## Combine the Google and Apple samples

Run `python3 src/collectors/combine_app_store_samples.py` after both collectors
have produced local normalized samples. This creates a local 159-row unified
record table at `data/normalized/app_store_reviews_combined.csv` and refreshes
the two text-free aggregate CSV tables under `results/app-stores/`.

## Apple App Store feasibility probe

The Apple collector is retained to document a completed, bounded test of the
active legacy customer-reviews JSON feed. Do not place it on a recurring
schedule without permission or governance clearance; see the source assessment
for the relevant Apple terms and `robots.txt` finding.

The completed command was
`python3 src/collectors/apple_app_store_sample_pull.py`. Normalized review text
stays under `data/normalized/` and is ignored by Git.

## Run the Google Play bounded sample

1. Run `python3 -m pip install -r requirements.txt`.
2. Run `python3 src/collectors/google_play_sample_pull.py`.

No credentials are needed because this test reads only the review cards on the
initial public app-details pages. It deliberately does not call undocumented
review endpoints and does not provide complete or paginated review coverage.
Normalized text stays under `data/normalized/` and is ignored by Git.

## Run the Google Play third-party test

1. Run `python3 -m pip install -r requirements.txt`.
2. Run `python3 src/collectors/google_play_third_party_test.py`.

This separate test uses the open-source `google-play-scraper` package rather
than an official Google API. It performs two bounded runs across three apps,
uses continuation-token pagination, and writes only aggregate evidence to Git.
Review text and reviewer IDs remain in ignored local files. See the
[third-party test report](docs/google-play/google_play_third_party_test.md) for
the access, maintenance, completeness, and governance limitations.

## Run the TMDB sample pull

1. Add `TMDB_API_KEY=your_key_here` to the local `.env` file.
2. Run `python3 src/collectors/tmdb_sample_pull.py`.
3. Run the same command again after 24–72 hours to measure newly observed,
   changed, and fixed-window-exit records. The initial two-run evaluation is
   complete; rerunning now starts an additional comparison cycle.

The collector writes aggregate evidence to `results/tmdb/run-summary.json`.
Normalized review text stays under `data/normalized/` and is ignored by Git.

## Repository structure

```text
docs/       Analysis and validation reports
src/        Source-specific collection and analysis code
results/    Aggregate run summaries and quality metrics
data/       Local or publishable samples; raw review text is not committed
```

## Evidence labels

- **Observed**: verified through a live sample pull.
- **Documentation**: confirmed only through official documentation.
- **Unverified**: not yet tested or confirmed.

Raw review text, credentials, and tokens must not be committed.
