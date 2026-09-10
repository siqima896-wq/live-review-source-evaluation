# Combined App Store Data Tables

This document puts the Google Play and Apple App Store evidence into one
schema and one set of comparison tables.

## Combined record table

The latest normalized samples were combined into:

```text
data/normalized/app_store_reviews_combined.csv
```

It contains 159 records: 9 Google Play review cards and 150 Apple App Store
reviews. Because the table contains user-generated review titles and text, it
remains local and is ignored by Git.

The committed, text-free aggregate tables are:

- [`combined-source-summary.csv`](../results/app-stores/combined-source-summary.csv)
- [`combined-app-summary.csv`](../results/app-stores/combined-app-summary.csv)

## Source-level comparison

| Measure | Google Play | Apple App Store |
|---|---:|---:|
| Target apps | 3 | 3 |
| Records | 9 | 150 |
| Records per app | 3 | 50 |
| Unique review IDs | 9 | 150 |
| Duplicate review IDs | 0 | 0 |
| Missing review text | 0 | 0 |
| Missing star ratings | 0 | 0 |
| Missing review timestamps | 0 | 0 |
| Mean star rating | 1.89 | 3.65 |
| Mean text length | 462.78 | 174.80 |
| Median text length | 485 | 102 |
| Shared records in repeat | 9 | 150 |
| New records in repeat | 0 | 0 |
| Absent records in repeat | 0 | 0 |
| Changed records in repeat | 2 | 0 |

The two rating averages are not directly comparable as app-quality estimates.
Google Play exposed three curated public-page cards per app, while Apple
returned 50 newest-first records per app from a legacy feed.

## App-level comparison

| Source | App | Category | Records | Mean rating | Mean text length |
|---|---|---|---:|---:|---:|
| Google Play | Duolingo | Education | 3 | 2.00 | 479.33 |
| Apple App Store | Duolingo | Education | 50 | 3.54 | 202.20 |
| Google Play | Spotify | Music & Audio | 3 | 2.67 | 491.00 |
| Apple App Store | Spotify | Music | 50 | 3.54 | 149.92 |
| Google Play | Uber | Maps & Navigation | 3 | 1.00 | 418.00 |
| Apple App Store | Uber | Travel | 50 | 3.86 | 172.28 |

## Unified record schema

| Unified field | Google Play source field | Apple source field |
|---|---|---|
| `source` | Constant `google_play` | Constant `apple_app_store` |
| `store_app_id` | `package_name` | `app_id` |
| `app_name` | `app_name` | `app_name` |
| `category` | `category` | `category` |
| `storefront` | Fixed tested locale `US/en_US` | `storefront` |
| `review_id` | `review_id` | `review_id` |
| `review_title` | Not available | `review_title` |
| `review_text` | `review_text` | `review_text` |
| `star_rating` | `star_rating` | `star_rating` |
| `app_version` | Not available | `app_version` |
| `review_timestamp` | `review_date` | `updated_at` |
| `engagement_positive` | `helpful_count` | `vote_sum` |
| `engagement_total` | Not available | `vote_count` |
| `developer_reply_present` | `developer_reply_present` | Not available; set to false |
| `developer_reply_text` | `developer_reply_text` | Not available |
| `developer_reply_timestamp` | `developer_reply_date` | Not available |
| `ingested_at` | `ingested_at` | `ingested_at` |
| `source_file` | Latest local Google JSONL | Latest local Apple JSONL |

`engagement_positive` is only a storage alignment, not a claim that Google
helpful counts and Apple vote sums have identical semantics. Similarly, Google
review timestamps have date precision while Apple timestamps include time and
offset.

## Regenerate the tables

After both source collectors have produced local normalized JSONL files, run:

```bash
python3 src/collectors/combine_app_store_samples.py
```

The script selects the latest local sample for each store, writes the ignored
159-row combined CSV, and refreshes both committed aggregate CSV tables.
