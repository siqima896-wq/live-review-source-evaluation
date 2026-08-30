# Live Review Source Evaluation

This repository compares the live-ingestion feasibility, analytical value,
and access requirements of Steam, YouTube, Reddit, and Trustpilot.

## Current status

- Steam: two-run live-ingestion test completed.
- YouTube: two-run, cross-topic sample pull completed.
- Reddit: sample pull pending.
- Trustpilot: API access investigation pending.

## Project documentation

- [Source comparison](docs/source-comparison.md)
- [Steam source assessment](docs/steam/steam_source_assessment.md)
- [Steam Run 1 validation](docs/steam/run1_validation.md)
- [Steam Run 2 validation](docs/steam/run2_validation.md)
- [YouTube run summary](results/youtube/run-summary.json)

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
