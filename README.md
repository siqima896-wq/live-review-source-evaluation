# Live Review Source Evaluation

This repository compares the live-ingestion feasibility, analytical value,
and access requirements of Steam, YouTube, and TMDB.

## Current status

- Steam: two-run live-ingestion test completed.
- YouTube: two-run, cross-topic sample pull completed; Run 2 refreshed on 2026-09-02.
- TMDB: two-run live sample pull completed (61 reviews from 4 films in each run).

## Project documentation

- [Source comparison](docs/source-comparison.md)
- [Steam source assessment](docs/steam/steam_source_assessment.md)
- [Steam Run 1 validation](docs/steam/run1_validation.md)
- [Steam Run 2 validation](docs/steam/run2_validation.md)
- [YouTube run summary](results/youtube/run-summary.json)
- [TMDB run summary](results/tmdb/run-summary.json)

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
