# Steam Review Ingestion Prototype

## Overview

This project evaluates Steam as a live source for repeatable review
ingestion.

It collects recent English-language reviews, saves normalized JSONL
output, performs data-quality checks, and compares records from
separate collection runs.

Steam is currently treated as a technical candidate, not the final
source recommendation.

## Tested Applications

| Game | App ID |
|---|---:|
| Portal 2 | 620 |
| Stardew Valley | 413150 |
| Cyberpunk 2077 | 1091500 |
| Are You Happy | 3388440 |

## Collection Configuration

- Filter: `recent`
- Language: `english`
- Review type: `all`
- Purchase type: `all`
- Maximum pages per game: `3`
- Reviews requested per page: `100`
- Delay between requests: `1 second`
- Request timeout: `30 seconds`

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependency:

```bash
pip install requests
```

## Usage

Collect reviews:

```bash
python src/steam/steam_sample_pull.py
```

Analyze the latest run:

```bash
python src/steam/analyze_run.py
```

Compare the latest two runs:

```bash
python src/steam/compare_runs.py
```

## Project Structure

```text
src/steam/                 Collector and analysis scripts
data/steam/                Locally generated normalized JSONL (ignored by Git)
results/steam/             Aggregate JSON run evidence
docs/steam/                Validation and assessment reports
```

## Normalized Fields

The output includes:

- application ID and game name;
- recommendation ID;
- review text and language;
- creation and update timestamps;
- positive or negative recommendation;
- engagement and purchase metadata;
- ingestion timestamp.

The combination of `app_id` and `recommendation_id` is used as the
unique review key.

## Validation Results

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Total records | 921 | 922 |
| Unique records | 921 | 922 |
| Positive reviews | 882 | 884 |
| Negative reviews | 39 | 38 |

Run-to-run comparison:

| Metric | Result |
|---|---:|
| Shared records | 652 |
| New records in Run 2 | 270 |
| Not in Run 2 recent window | 269 |
| Updated records | 2 |

The results demonstrate that the process can be run repeatedly and can
collect newly available records from a live source.

## Data-Quality Findings

- No recommendation IDs were missing.
- Three Run 2 records contained no review text.
- No creation timestamps were missing.
- Run 2 was 95.88% positive.
- Empty-text records require cleaning.
- The strong positive imbalance should be considered in downstream
  sentiment analysis.

## Limitations

- Steam data is limited to gaming.
- Only English-language reviews were tested.
- Only four applications and three pages per application were tested.
- The exact rate limit and full historical depth remain open items.
- Records missing from Run 2 should not be treated as deleted because
  the experiment used a fixed recent-review window.

## Reports

Detailed evidence is available in:

- [`docs/steam/run1_validation.md`](../../docs/steam/run1_validation.md)
- [`docs/steam/run2_validation.md`](../../docs/steam/run2_validation.md)
- [`docs/steam/steam_source_assessment.md`](../../docs/steam/steam_source_assessment.md)

## Conclusion

Steam has been validated as a technically feasible live source for
testing repeatable ingestion.

However, it should not yet be treated as the final source
recommendation because its analytical scope is limited to gaming.

The next step is to compare Steam with other sanctioned live sources
across ingestion feasibility and analytical value.
