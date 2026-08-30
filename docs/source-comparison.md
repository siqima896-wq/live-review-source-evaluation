# Live-Source Comparison

This table is the main project deliverable. Values marked `TBD` will be
replaced as the remaining sample pulls are completed.

| Dimension | Steam | YouTube Comments | Reddit Posts and Comments | Trustpilot Service Reviews |
|---|---|---|---|---|
| Content type | Game reviews | Video comments and replies | Community posts and comments | Cross-industry service reviews |
| Current evidence | **Observed:** two live runs | TBD | TBD | Access investigation pending |
| Authentication | Public Store Reviews endpoint | API key | OAuth | Data Solutions Insights API key |
| Sample targets | 4 games | TBD | TBD | TBD |
| Run 1 records | 921 | TBD | TBD | TBD |
| Run 2 records | 922 | TBD | TBD | TBD |
| Shared records | 652 | TBD | TBD | TBD |
| New records in Run 2 | 270 | TBD | TBD | TBD |
| Changed records | 2 | TBD | TBD | TBD |
| Duplicate normalized keys | 0 in both runs | TBD | TBD | TBD |
| Missing text | 2 in Run 1; 3 in Run 2 | TBD | TBD | TBD |
| Pagination | **Observed:** cursor-based, up to 3 pages per game tested | TBD | TBD | TBD |
| Stable record key | **Observed:** `(app_id, recommendation_id)` | TBD | TBD | TBD |
| Rating/label | Recommend / do not recommend | No uniform rating | No uniform rating | 1–5 stars |
| Run 2 positive share | 95.88% | TBD | TBD | TBD |
| Average Run 2 text length | 135.26 characters | TBD | TBD | TBD |
| Topic breadth | Low: gaming only | Expected broad; unverified | Expected broad; unverified | Expected broad; unverified |
| Recurring-ingestion result | **Pass for tested scope** | TBD | TBD | Unverified pending access |
| Main limitation | Gaming scope and strong positive imbalance | TBD | TBD | Commercial API access may be required |

## Steam interpretation

Steam is technically feasible within the tested scope. Repeated collection,
cursor pagination, new-record discovery, changed-record detection, and clean
normalized keys were observed. The 269 Run 1 records absent from Run 2 are
described as leaving the fixed recent-review window, not as deletions.

Supporting evidence is available in the
[Steam assessment](steam/steam_source_assessment.md) and under
[`results/steam`](../results/steam/).
