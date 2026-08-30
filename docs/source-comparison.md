# Live-Source Comparison

This table is the main project deliverable. Values marked `TBD` will be
replaced as the remaining sample pulls are completed.

| Dimension | Steam | YouTube Comments | Reddit Posts and Comments | Trustpilot Service Reviews |
|---|---|---|---|---|
| Content type | Game reviews | Top-level video comments in tested sample | Community posts and comments | Cross-industry service reviews |
| Current evidence | **Observed:** two live runs | **Observed:** two live runs | TBD | Access investigation pending |
| Authentication | Public Store Reviews endpoint | API key | OAuth | Data Solutions Insights API key |
| Sample targets | 4 games | 4 videos across technology, science, education, and platform culture | TBD | TBD |
| Run 1 records | 921 | 799 | TBD | TBD |
| Run 2 records | 922 | 799 | TBD | TBD |
| Shared records | 652 | 799 | TBD | TBD |
| New records in Run 2 | 270 | 0 | TBD | TBD |
| Changed records | 2 | 0 | TBD | TBD |
| Duplicate normalized keys | 0 in both runs | 0 in both runs | TBD | TBD |
| Missing text | 2 in Run 1; 3 in Run 2 | 0 in both runs | TBD | TBD |
| Pagination | **Observed:** cursor-based, up to 3 pages per game tested | **Observed:** `nextPageToken`, 2 pages per video tested | TBD | TBD |
| Stable record key | **Observed:** `(app_id, recommendation_id)` | **Observed:** `comment_id` | TBD | TBD |
| Rating/label | Recommend / do not recommend | No uniform rating | No uniform rating | 1–5 stars |
| Run 2 positive share | 95.88% | Not applicable: no uniform rating | TBD | TBD |
| Average Run 2 text length | 135.26 characters | 108.03 characters | TBD | TBD |
| Topic breadth | Low: gaming only | **Observed broader than Steam:** four distinct video-topic categories | Expected broad; unverified | Expected broad; unverified |
| Recurring-ingestion result | **Pass for tested scope** | **Pass for tested scope** | TBD | Unverified pending access |
| Main limitation | Gaming scope and strong positive imbalance | No uniform rating; comments depend on selected videos; replies not tested | TBD | Commercial API access may be required |

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
