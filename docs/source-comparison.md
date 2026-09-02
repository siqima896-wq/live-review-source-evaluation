# Live-Source Comparison

This table is the main project deliverable. All three sources have completed
two live sample pulls.

| Dimension | Steam | YouTube Comments | TMDB Movie Reviews |
|---|---|---|---|
| Content type | Game reviews | Top-level video comments in tested sample | User-written movie reviews |
| Current evidence | **Observed:** two live runs | **Observed:** two live runs; Run 2 refreshed on 2026-09-02 | **Observed:** two live runs on 2026-08-31 and 2026-09-02 |
| Authentication | Public Store Reviews endpoint | API key | API key |
| Sample targets | 4 games | 4 videos across technology, science, education, and platform culture | 4 films across genres and countries |
| Run 1 records | 921 | 799 | 61 |
| Run 2 records | 922 | 800 | 61 |
| Shared records | 652 | 591 | 61 |
| New records in Run 2 | 270 | 209 | 0 |
| Changed records | 2 | 0 | 0 |
| Duplicate normalized keys | 0 in both runs | 0 in both runs | 0 in both runs |
| Missing text | 2 in Run 1; 3 in Run 2 | 0 in both runs | 0 in both runs |
| Pagination | **Observed:** cursor-based, up to 3 pages per game tested | **Observed:** `nextPageToken`, 2 pages per video tested | **Observed:** page-number pagination; 2 pages for Oppenheimer, 5 pages total |
| Stable record key | **Observed:** `(app_id, recommendation_id)` | **Observed:** `comment_id` | **Observed:** 61 unique `review_id` values shared across both runs |
| Rating/label | Recommend / do not recommend | No uniform rating | 53 ratings present; 8 missing; mean of present ratings 7.26 |
| Run 2 positive share | 95.88% | Not applicable: no uniform rating | Not applicable: ratings are optional; mean of present ratings 7.26/10 |
| Average Run 2 text length | 135.26 characters | 109.55 characters | 1610.84 characters |
| Average Run 1 text length | See run evidence | See run evidence | 1610.84 characters; median 898 |
| Topic breadth | Low: gaming only | **Observed broader than Steam:** four distinct video-topic categories | Film only; four selected films, not evidence of broader users or topics overall |
| Recurring-ingestion result | **Pass for tested scope** | **Pass for tested scope** | **Pass for tested scope** |
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

YouTube was technically feasible within the tested scope. Run 1 retrieved 799
top-level comments and the refreshed Run 2 retrieved 800 from four videos,
using eight API requests per run. Run 2 contained 591 shared records, 209 new
records, 208 records no longer in the fixed recent-comment window, and no
observed changes among shared records. All 800 Run 2 `comment_id` values were
unique, with no missing IDs or texts. The sampled topics were broader than
Steam, but the evidence does not establish population-level user breadth, and
comments do not provide a uniform review rating.

Supporting aggregate evidence is available in the
[YouTube run summary](../results/youtube/run-summary.json). Raw normalized
comment text remains local and is excluded from Git.

## TMDB interpretation

The live runs on 2026-08-31 and 2026-09-02 each retrieved 61 reviews using five
page requests: Barbie (18), Oppenheimer (25), Parasite (16), and Spirited Away
(2). Run 2 shared all 61 review IDs with Run 1, with no new, absent, or changed
records. Both outputs contain 61 unique review IDs and no missing IDs or review
text. Ratings are present for 53 records and absent for eight. All targets
succeeded without reported API errors.

The sample's mean text length is 1610.84 characters (median 898), but the
selected films and small sample do not establish population-wide content or
user diversity. Collection requested `en-US`; other languages were not tested.
The returned page totals were exhausted for these targets at collection time.
This is not proof of complete historical coverage or a newest-first feed.

The second run confirms cross-run ID stability and repeatable collection for
this short interval and tested scope. It does not establish how often new or
edited reviews appear. Records absent from a later sample must not be assumed
deleted without independent evidence. Downstream usage permissions also
require review; successful access alone does not establish permission for
every analytical use.

Supporting aggregate evidence is in the
[TMDB run summary](../results/tmdb/run-summary.json). Credentials and normalized
review text remain local and are excluded from Git.
