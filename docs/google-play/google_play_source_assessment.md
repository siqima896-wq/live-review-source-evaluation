# Google Play Review Source: Initial Feasibility Assessment

Assessment date: 2026-09-09 (America/Chicago)
Latest live sample run: 2026-09-10 02:47 UTC

## Decision summary

Google Play reviews are a **conditional fit, not the strongest overall fit for
the current cross-product public-data requirement**.

- **Strong data model:** observed review cards contained a stable-looking
  review ID, text, 1–5 star rating, date, helpful count, and optional developer
  reply.
- **Broad product coverage:** the small test succeeded for Education, Music &
  Audio, and Maps & Navigation apps, which is broader than the gaming-only and
  film-only candidates.
- **Weak supported access for competitor/cross-app research:** Google's
  supported Reviews API is for production apps controlled by the authenticated
  developer. It is not a general public, cross-app review API.
- **Weak public-page scalability:** the initial public app page exposed only
  three curated review cards per tested app. Its HTML is undocumented and did
  not provide a supported pagination contract.

Accordingly, Google Play becomes a strong candidate only if the project will
analyze reviews for apps the team owns and can authorize through Play Console.
For broad public coverage across unrelated products, it should not replace
Steam as the primary source on current evidence. Apple App Store should still
be assessed before the final source decision.

## Evidence and access routes

### 1. Official Google Play Developer Reviews API

Google documents an authenticated API for retrieving and replying to reviews
of a developer's production apps. Access requires OAuth or a service account
with the **Reply to reviews** permission. The API returns only reviews that
include comments, supports token pagination with up to 100 reviews per page,
and the list endpoint exposes reviews created or modified within the last week.
The documented default quota is 200 `GET` requests per hour. Historical
reviews can instead be downloaded from Play Console as CSV.

This is the best-supported and most repeatable route, but it does not satisfy a
cross-app public dataset unless the team controls all target apps.

Sources:

- [Google: Reply to Reviews](https://developers.google.com/android-publisher/reply-to-reviews)
- [Google Play Developer API: reviews resource](https://developers.google.com/android-publisher/api-ref/rest/v3/reviews)

### 2. Public app-details pages

The repository collector requests only public app-details pages such as the
[Duolingo listing](https://play.google.com/store/apps/details?id=com.duolingo&hl=en_US&gl=US).
No account or API key was required. The pages exposed three review cards per
tested app, but this is a curated display surface rather than a documented data
API. The selected cards are not necessarily newest-first or representative of
the review population.

Common third-party scrapers call undocumented Google Play review/internal
endpoints. They were not used here. Google's current `robots.txt` disallows
`/store/getreviews` and `/_`, and Google's general terms prohibit automated
access that violates machine-readable instructions. Google Play's terms also
prohibit collecting or harvesting users' personal data, including account
names. The collector therefore stays on the initial app-details page and
discards reviewer names and profile images.

Sources:

- [Google Play robots.txt](https://play.google.com/robots.txt)
- [Google Terms of Service](https://policies.google.com/terms)
- [Google Play Terms of Service](https://play.google.com/about/play-terms/)

This assessment is a technical and source-governance screen, not legal advice.
Terms and intended downstream use should be reviewed before production use.

## Live sample design

The test fixed the storefront to `US`, page language to `en_US`, and selected
three unrelated product categories:

| Package | App | Category | Public review cards |
|---|---|---|---:|
| `com.duolingo` | Duolingo: Language Lessons | Education | 3 |
| `com.spotify.music` | Spotify: Music and Podcasts | Music & Audio | 3 |
| `com.ubercab` | Uber - Request a ride | Maps & Navigation | 3 |
| **Total** |  |  | **9** |

The normalized records remain local under `data/normalized/`. The committed
aggregate evidence is in
[`results/google-play/run-summary.json`](../../results/google-play/run-summary.json).
Reviewer names and images are not retained.

## Observed sample quality

| Measure | Result |
|---|---:|
| Records | 9 |
| Unique review IDs | 9 |
| Duplicate review IDs | 0 |
| Missing review IDs | 0 |
| Missing review text | 0 |
| Missing star ratings | 0 |
| Missing review dates | 0 |
| Missing helpful counts | 0 |
| Records with a developer reply | 1 |
| Mean star rating | 1.89 / 5 |
| Mean text length | 462.78 characters |
| Median text length | 485 characters |

The low mean rating should **not** be interpreted as an app-level sentiment
estimate. The page exposes a small curated set of reviews and appears to favor
detailed or helpful reviews rather than a random or newest-first sample.

## Immediate repeat test

A repeat roughly six minutes after the initial pull returned the same nine
review IDs, with zero new or absent cards. Two records changed because their
helpful counts changed.
This demonstrates that the collector can detect field updates, but it is only
a same-session smoke test. It does not establish long-term HTML stability or a
reliable recurring-ingestion feed.

## Requirement fit

| Dimension | Public app page | Official API for owned apps |
|---|---|---|
| Authentication | None observed | OAuth or service account |
| Cross-product breadth | High in principle; three categories tested | Limited to developer-controlled apps |
| Structured review fields | Good for displayed cards | Strong and documented |
| Supported pagination | No | Yes, token-based |
| Repeatable collection | Low–medium; HTML selectors are undocumented | High within documented scope |
| Historical completeness | No | Recent list window; CSV export for history |
| User/location coverage | Not established | Depends on the developer's app population |
| Governance risk | Material for bulk/undocumented scraping | Lower when used within API terms |

## Recommendation

Do not build the next project phase around bulk public Google Play scraping.
The source has better topical breadth and a better review schema than Steam,
YouTube Comments, or TMDB, but it does not currently provide a supported
cross-app collection route.

If the team owns suitable production apps, obtain Play Console authorization
and run a second feasibility test through the official API. That test should
collect up to 100 recent reviews per app, repeat after 24–72 hours, and measure
new, changed, and no-longer-in-window IDs. Otherwise, proceed to the Apple App
Store assessment and compare its supported public access with this result.

## Reproduce the bounded public-page sample

```bash
python3 -m pip install -r requirements.txt
python3 src/collectors/google_play_sample_pull.py
```

The script commits only aggregate evidence. Review and developer-reply text is
written to ignored local JSONL files.
