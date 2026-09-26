# Live-Source Comparison

This table is the main project deliverable. All three original sources have
completed two live sample pulls. Google Play has since completed a bounded
public-page sample and a separate third-party open-source pagination test; its
evidence is summarized with Apple below because neither route is equivalent to
a supported cross-app API pull. Apple App Store has also completed a bounded
legacy-feed sample and repeat; the shared table separates technical results
from governance status.

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

## Combined App Store comparison

| Dimension | Google Play Reviews | Apple App Store Reviews |
|---|---|---|
| Current evidence | **Observed:** 9-card public-page sample; separate third-party test returned 600 records per run | **Observed:** 150-record bounded legacy-feed sample plus repeat smoke test |
| Authentication | None for initial public page; official API requires developer authorization | None for legacy feed; official API requires App Store Connect JWT |
| Sample targets | 3 apps across education, music/audio, and navigation | 3 apps across education, music, and travel |
| Records | Public page: 9; third party: 600 per run, 200 per app | 150; 50 per app |
| Shared records in repeat | Public page: 9; third party: 600 | 150 |
| New / absent / changed | Third-party repeat: 0 / 0 / 0 | 0 / 0 / 0 |
| Duplicate review IDs | 0 | 0 |
| Missing ID / text / rating / timestamp | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| Rating | 1–5 stars; third-party mean 4.00 | 1–5 stars; mean 3.65 |
| Average text length | Third party: 80.20 characters | 174.80 characters |
| Median text length | Third party: 30 characters | 102 characters |
| Review title | Not available | Complete for all 150 records |
| App version | Not available | Complete for all 150 records |
| Developer response | Third party: 17 observed per run | Not present in tested feed |
| Pagination | No supported public pagination; third-party continuation returned 2 pages per app | Feed advertised 10 pages; only page 1 tested |
| Ordering | Public page curated; third-party test requested newest | Newest-first observed for all targets |
| Topic breadth | Broad in principle; three unrelated categories tested | Broad in principle; three unrelated categories tested |
| Recurring-ingestion result | **Short-term technical repeat passed through third party; long-term reliability and governance not established** | **Technical smoke test passed; governance screen failed pending permission** |
| Main limitation | Third-party tool uses undocumented interfaces and is not an official Google API | Apple terms restrict automated analysis; robots.txt disallows RSS paths |

The aligned record-level table contains 159 rows and remains local because it
includes user-generated review text. The committed combined source- and
app-level tables are documented in the
[combined app-store data tables](app-store-comparison.md).

### Google Play interpretation

The initial bounded test retrieved three public review cards each for Duolingo,
Spotify, and Uber. All nine had unique IDs, text, star ratings, dates, and
helpful counts; one included a developer reply. An immediate repeat shared all
nine IDs and detected two helpful-count changes. This small curated sample is
not suitable for population-level sentiment estimates.

A later test using the third-party open-source `google-play-scraper` package
retrieved 200 reviews per app in each of two immediate runs. All 600 review IDs
were unique within each run and shared across runs, and two 100-record pages
were observed for each target. This establishes meaningful bounded volume,
multi-app pagination, and short-term repeatability. It does not establish
official support, historical completeness, long-term stability, or governance
clearance.

Google's supported Reviews API provides structured, token-paginated access for
a developer's own production apps, but not unrelated apps. Bulk public
scraping depends on undocumented interfaces and is not a sound basis for a
supported recurring pipeline without an explicit governance decision. Google
Play therefore has strong schema, topical breadth, and now observed third-party
technical feasibility, but still lacks supported access for this project's
cross-product requirement.

Supporting evidence is in the
[Google Play assessment](google-play/google_play_source_assessment.md) and
[public-page run summary](../results/google-play-01-public-page-test/run-summary.json). The
[third-party test report](google-play/google_play_third_party_test.md) and
[aggregate result](../results/google-play-02-third-party-validation/run-summary.json) provide
the supplemental evidence. Review text remains local and is excluded from Git.

### Apple App Store interpretation

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

For a **bounded research prototype**, select Google Play through the tested
third-party package only if the team explicitly accepts an unofficial
dependency and clears the relevant access and downstream-use requirements. It
now has the strongest observed combination of broad app coverage, structured
reviews, bounded volume, pagination, and short-term repeatability among the app
store routes tested.

Do not treat that conditional prototype choice as approval for a recurring
production pipeline. Google's supported Reviews API is limited to apps
controlled by the authenticated developer, while the tested third-party route
uses undocumented interfaces. Apple's legacy feed also remains blocked by the
documented governance concerns. If supported cross-app access is mandatory,
**neither Google Play nor Apple currently passes**, and the source decision
should pause pending permission or a licensed data route rather than default
to Steam. Steam remains technically usable, but its gaming-only users,
products, and topics are too narrow for the stated broad-source objective.

YouTube remains a possible secondary source when topic breadth matters, but
comments lack a uniform rating. TMDB provides much longer review text and some
ratings, but the tested sample was small and showed no new or changed records
in Run 2.

Reddit and Trustpilot were also attempted as candidate sources, but neither
could be included in the live-pull comparison because API access was not
obtained during this evaluation. Reddit requires prior API approval through an
access application before a live pull can be completed. Trustpilot likewise
requires an access application form for the relevant API credentials. Their
current access feasibility is therefore weaker than Steam and YouTube. These
statements describe access findings only; no ingestion or data-quality claims
are made for Reddit or Trustpilot without live-run evidence.
