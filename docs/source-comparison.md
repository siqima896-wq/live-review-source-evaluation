# Live-Source Comparison

This table is the main project deliverable. All three original sources have
completed two live sample pulls. Google Play has since completed a bounded
public-page sample and immediate repeat smoke test; its evidence is summarized
separately because it is not equivalent to a supported paginated API pull.
Apple App Store has also completed a bounded legacy-feed sample and repeat;
its technical and governance evidence is likewise summarized separately.

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

## Google Play addendum

| Dimension | Google Play Reviews |
|---|---|
| Content type | App reviews |
| Current evidence | **Observed:** bounded public-page sample plus immediate repeat smoke test |
| Authentication | None for initial public page; official API requires developer authorization |
| Sample targets | 3 apps across education, music/audio, and navigation |
| Records | 9 displayed review cards |
| Shared records in immediate repeat | 9 |
| Changed records | 2 helpful-count changes |
| Duplicate normalized keys | 0 |
| Missing core fields | 0 missing IDs, text, star ratings, dates, or helpful counts |
| Stable record key | **Observed:** 9 unique review IDs shared in the immediate repeat |
| Rating/label | 1–5 stars present for all 9 cards |
| Average rating | 1.89/5; not representative because displayed cards are curated |
| Average text length | 462.78 characters |
| Topic breadth | Broad in principle; three unrelated app categories tested |
| Recurring-ingestion result | **Not established:** public page lacks supported pagination; official API is for owned apps |
| Main limitation | No supported general cross-app review API; public HTML is curated and undocumented |

The bounded test retrieved three public review cards each for Duolingo,
Spotify, and Uber. All nine had unique IDs, text, star ratings, dates, and
helpful counts; one included a developer reply. An immediate repeat shared all
nine IDs and detected two helpful-count changes. This small curated sample is
not suitable for population-level sentiment estimates.

Google's supported Reviews API provides structured, token-paginated access for
a developer's own production apps, but not unrelated apps. Bulk public
scraping commonly depends on undocumented endpoints and is not a sound basis
for a supported recurring pipeline. Google Play therefore has strong schema
and topical breadth but weak access feasibility for this project's
cross-product requirement.

Supporting evidence is in the
[Google Play assessment](google-play/google_play_source_assessment.md) and
[run summary](../results/google-play/run-summary.json). Review text remains
local and is excluded from Git.

## Apple App Store addendum

| Dimension | Apple App Store Reviews |
|---|---|
| Content type | App reviews |
| Current evidence | **Observed:** 150-record bounded legacy-feed sample plus short repeat test |
| Authentication | None for legacy feed; official API requires App Store Connect JWT |
| Sample targets | 3 apps across education, music, and travel |
| Records | 150; 50 per app |
| Shared records in repeat | 150 |
| New / absent / changed records | 0 / 0 / 0 |
| Duplicate normalized keys | 0 |
| Missing core fields | 0 missing IDs, titles, text, ratings, versions, timestamps, or vote fields |
| Pagination | Feed advertised 10 pages; only page 1 tested |
| Stable record key | **Observed:** 150 unique review IDs shared in the repeat |
| Rating/label | 1–5 stars present for all 150 reviews; mean 3.65 |
| Average text length | 174.80 characters; median 102 |
| Topic breadth | Broad in principle; three unrelated app categories tested |
| Recurring-ingestion result | **Technical smoke test passed; governance screen failed pending permission** |
| Main limitation | Legacy public feed is not in current API docs; Apple terms restrict automated analysis and robots.txt disallows RSS paths |

Apple's legacy feed was the strongest public app-store route technically. It
returned 50 newest-first reviews per app with a consistent schema, complete
core fields, version metadata, and no duplicate IDs. The immediate repeat
returned the same 150 IDs with no observed changes.

The technical result does not establish permission for recurring collection.
Apple's current documented Customer Reviews API requires App Store Connect JWT
authorization and applies to apps available to the authenticated account. The
legacy feed is not part of that current API documentation; Apple Media Services
terms restrict automated scraping and analysis, and `itunes.apple.com` robots
rules disallow RSS paths. It should therefore not be scheduled without written
permission or a licensed data route.

Supporting evidence is in the
[Apple App Store assessment](apple-app-store/apple_app_store_source_assessment.md)
and [run summary](../results/apple-app-store/run-summary.json). Review text
remains local and is excluded from Git.

## Recommendation

Keep **Steam as the primary operational source for the next phase**. Apple App
Store is the strongest technical candidate for broad, structured app reviews,
but it is only a provisional candidate until the team obtains permission or a
licensed access route for recurring cross-app analysis. Steam currently
provides the strongest usable balance of
ingestion feasibility, analytical value, and access: its public endpoint does
not require an API key, both live runs completed successfully, Run 2 found 270
new records and two changed records, and the data includes a direct
recommend/do-not-recommend label plus useful timestamps and metadata. Its main
tradeoffs are a gaming-only scope and a strongly positive class imbalance.
YouTube is a useful secondary source when topic breadth matters, but its
comments lack a uniform rating. TMDB provides much longer review text and some
ratings, but the tested sample was small and showed no new or changed records
in Run 2. Google Play offers broader products and a stronger review schema,
but its supported API is limited to apps controlled by the authenticated
developer; the public-page route is too small and undocumented to displace
Steam for the current cross-product requirement. Apple is technically stronger
than Google Play's public route, but its governance restrictions prevent a
production recommendation on current evidence.

Reddit and Trustpilot were also attempted as candidate sources, but neither
could be included in the live-pull comparison because API access was not
obtained during this evaluation. Reddit requires prior API approval through an
access application before a live pull can be completed. Trustpilot likewise
requires an access application form for the relevant API credentials. Their
current access feasibility is therefore weaker than Steam and YouTube. These
statements describe access findings only; no ingestion or data-quality claims
are made for Reddit or Trustpilot without live-run evidence.
