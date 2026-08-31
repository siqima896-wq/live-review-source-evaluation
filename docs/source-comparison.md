# Live-Source Comparison

This table is the main project deliverable. Values marked `TBD` will be
replaced as the remaining sample pulls are completed.

| Dimension | Steam | YouTube Comments | TMDB Movie Reviews |
|---|---|---|---|
| Content type | Game reviews | Top-level video comments in tested sample | User-written movie reviews |
| Current evidence | **Observed:** two live runs | **Observed:** two live runs | **Observed:** one live run on 2026-08-31 |
| Authentication | Public Store Reviews endpoint | API key | API key |
| Sample targets | 4 games | 4 videos across technology, science, education, and platform culture | 4 films across genres and countries |
| Run 1 records | 921 | 799 | 61 |
| Run 2 records | 922 | 799 | TBD |
| Shared records | 652 | 799 | TBD |
| New records in Run 2 | 270 | 0 | TBD |
| Changed records | 2 | 0 | TBD |
| Duplicate normalized keys | 0 in both runs | 0 in both runs | 0 in Run 1 |
| Missing text | 2 in Run 1; 3 in Run 2 | 0 in both runs | 0 in Run 1 |
| Pagination | **Observed:** cursor-based, up to 3 pages per game tested | **Observed:** `nextPageToken`, 2 pages per video tested | **Observed:** page-number pagination; 2 pages for Oppenheimer, 5 pages total |
| Stable record key | **Observed:** `(app_id, recommendation_id)` | **Observed:** `comment_id` | **Observed:** 61 unique `review_id` values; cross-run stability unverified |
| Rating/label | Recommend / do not recommend | No uniform rating | 53 ratings present; 8 missing; mean of present ratings 7.26 |
| Run 2 positive share | 95.88% | Not applicable: no uniform rating | TBD |
| Average Run 2 text length | 135.26 characters | 108.03 characters | TBD |
| Average Run 1 text length | See run evidence | See run evidence | 1610.84 characters; median 898 |
| Topic breadth | Low: gaming only | **Observed broader than Steam:** four distinct video-topic categories | Film only; four selected films, not evidence of broader users or topics overall |
| Recurring-ingestion result | **Pass for tested scope** | **Pass for tested scope** | First pull and pagination passed; recurring collection unverified |
| Main limitation | Gaming scope and strong positive imbalance | No uniform rating; comments depend on selected videos; replies not tested | Entertainment scope; ratings may be missing; API terms require careful review for downstream analysis |

## Steam interpretation

Steam is technically feasible within the tested scope. Repeated collection,
cursor pagination, new-record discovery, changed-record detection, and clean
normalized keys were observed. The 269 Run 1 records absent from Run 2 are
described as leaving the fixed recent-review window, not as deletions.

Supporting evidence is available in the
[Steam assessment](steam/steam_source_assessment.md) and under
[`results/steam`](../results/steam/).

## YouTube interpretation

YouTube was technically feasible within the tested scope. Both runs retrieved
799 top-level comments from four videos using eight API requests per run. All
799 normalized `comment_id` values were unique, and no comment IDs or texts
were missing. The second run found the same 799 records with no observed
changes, demonstrating repeatable pagination and stable keys for this short
interval. The sampled topics were broader than Steam, but the evidence does
not establish population-level user breadth, and comments do not provide a
uniform review rating.

Supporting aggregate evidence is available in the
[YouTube run summary](../results/youtube/run-summary.json). Raw normalized
comment text remains local and is excluded from Git.

## TMDB interpretation

The first live run on 2026-08-31 retrieved 61 reviews using five page requests:
Barbie (18), Oppenheimer (25), Parasite (16), and Spirited Away (2).
The normalized output contains 61 unique review IDs and no missing IDs or
review text. Ratings are present for 53 records and absent for eight.
All targets succeeded without reported API errors.

The sample's mean text length is 1610.84 characters (median 898), but the
selected films and small sample do not establish population-wide content or
user diversity. Collection requested `en-US`; other languages were not tested.
The returned page totals were exhausted for these targets at collection time.
This is not proof of complete historical coverage or a newest-first feed.

Only one run has been completed. Cross-run ID stability, newly observed
records, edits, and recurring collection remain unverified. A later run should
compare the same targets; records absent from a later sample must not be
assumed deleted without independent evidence. Downstream usage permissions
also require review; successful access alone does not establish permission
for every analytical use.

Supporting aggregate evidence is in the
[TMDB run summary](../results/tmdb/run-summary.json). Credentials and normalized
review text remain local and are excluded from Git.
