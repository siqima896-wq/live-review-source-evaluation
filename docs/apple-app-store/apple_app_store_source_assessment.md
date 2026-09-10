# Apple App Store Review Source: Initial Feasibility Assessment

Assessment date: 2026-09-10 (America/Chicago)
Latest live sample run: 2026-09-10 18:20 UTC

## Decision summary

Apple App Store reviews are the **strongest technical fit among the app-store
routes tested, but they do not pass the production-governance screen for broad
public cross-app collection without additional permission**.

- **Repeatable structured sample:** the active legacy customer-reviews JSON
  feed returned 50 newest-first reviews for each of three apps without
  authentication.
- **Strong review fields:** every sampled record included a review ID, title,
  body, 1–5 star rating, app version, timestamp, and vote fields.
- **Broad product coverage:** Education, Music, and Travel targets all
  succeeded with the same schema.
- **Material access risk:** the feed is not part of Apple's current App Store
  Connect API documentation, `itunes.apple.com/robots.txt` disallows RSS paths,
  and the Apple Media Services terms prohibit automated scraping, copying,
  measurement, analysis, or monitoring of Service content.

The source is therefore stronger than Google Play for a bounded technical
prototype, but it should not be scheduled or adopted as the production source
unless Apple confirms the intended feed use or the project obtains a licensed
data route. Steam remains the operational fallback under the current evidence.

## Evidence and access routes

### 1. Official App Store Connect API

Apple's documented API supports
`GET /v1/apps/{id}/customerReviews` and returns a structured review resource
with rating, title, body, reviewer nickname, creation date, territory, and an
optional response relationship. It supports filtering, sorting, and linked
pagination. Requests require a signed JWT generated from an App Store Connect
API key. The app ID represents an app available to the authenticated App Store
Connect account, so this is not a general competitor-review API.

This is the preferred production route for apps the team owns or is authorized
to manage.

Sources:

- [Apple: List all customer reviews for an app](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps-_id_-customerreviews)
- [Apple: CustomerReview attributes](https://developer.apple.com/documentation/appstoreconnectapi/customerreview/attributes-data.dictionary)
- [Apple: Generate API tokens](https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests)
- [Apple: Ratings and reviews overview](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/ratings-and-reviews-overview)

### 2. Legacy public customer-reviews JSON feed

The feasibility probe found an active JSON feed at a pattern such as:

```text
https://itunes.apple.com/us/rss/customerreviews/page=1/id=570060128/sortby=mostrecent/json
```

The feed returned 50 records per tested app, identified itself as page 1, and
advertised 10 pages through its link metadata. Only page 1 was collected. All
three target feeds were observed in strict newest-first timestamp order.

This route has important governance limitations:

- It is not documented in Apple's current App Store Connect API reference.
- [`itunes.apple.com/robots.txt`](https://itunes.apple.com/robots.txt)
  disallows `/*/rss/*` for automated agents.
- The [Apple Media Services terms](https://www.apple.com/legal/internet-services/itunes/id/terms-en.html)
  prohibit automated processes used to scrape, copy, measure, analyze, or
  monitor any portion of the Services or Content.
- Apple's [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
  distinguish approved Apple RSS feeds from prohibited scraping, but the
  current official documentation reviewed for this assessment does not confirm
  that the customer-reviews feed is an approved feed for this use.

The live pull is retained as a bounded feasibility probe, not as evidence that
recurring use is authorized. This assessment is not legal advice.

## Live sample design

The test used the US storefront, `mostrecent` sorting, and one 50-record page
for each of three unrelated apps:

| App ID | App | Category | Records | Mean rating | Mean text length |
|---|---|---|---:|---:|---:|
| `570060128` | [Duolingo](https://apps.apple.com/us/app/duolingo-language-lessons/id570060128) | Education | 50 | 3.54 | 202.20 |
| `324684580` | [Spotify](https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580) | Music | 50 | 3.54 | 149.92 |
| `368677368` | [Uber](https://apps.apple.com/us/app/uber-request-a-ride/id368677368) | Travel | 50 | 3.86 | 172.28 |
| **Total** |  |  | **150** | **3.65** | **174.80** |

Normalized records remain local under `data/normalized/`. The committed
aggregate evidence is in
[`results/apple-app-store/run-summary.json`](../../results/apple-app-store/run-summary.json).
Reviewer nicknames and profile URIs are not retained.

## Observed sample quality

| Measure | Result |
|---|---:|
| Records | 150 |
| Unique review IDs | 150 |
| Duplicate review IDs | 0 |
| Missing review IDs | 0 |
| Missing titles | 0 |
| Missing review text | 0 |
| Missing star ratings | 0 |
| Missing app versions | 0 |
| Missing timestamps | 0 |
| Missing vote fields | 0 |
| Mean star rating | 3.65 / 5 |
| Mean text length | 174.80 characters |
| Median text length | 102 characters |

Rating distribution:

| Stars | Records | Share |
|---:|---:|---:|
| 1 | 34 | 22.67% |
| 2 | 11 | 7.33% |
| 3 | 9 | 6.00% |
| 4 | 16 | 10.67% |
| 5 | 80 | 53.33% |

Unlike Google Play's three curated app-page cards, these records were observed
in newest-first order and included both positive and negative ratings. The
sample nevertheless covers only one recent page and one storefront, so it is
not evidence of population-level representativeness.

## Repeat test

Short-interval repeat pulls returned the same 150 review IDs, with no new,
absent, or changed records. This passes a same-session stability smoke test.
It does not establish long-term endpoint support, and the governance findings
prevent a recommendation to schedule further recurring pulls without review.

## Requirement fit

| Dimension | Legacy public feed | Official API for authorized apps |
|---|---|---|
| Authentication | None observed | Signed JWT |
| Cross-product breadth | High technically; three categories tested | Limited to account-authorized apps |
| Structured review fields | Strong | Strong and documented |
| Pagination | 10 pages advertised; only page 1 tested | Supported through API links/cursors |
| Newest-first collection | Observed for all three targets | Supported sorting |
| Repeatable collection | Technically passed short smoke test | Strong within documented scope |
| Developer responses | Not present in tested feed | Available through response relationship |
| Storefront coverage | US only tested | Territory field and filters documented |
| Governance status | **Does not pass without permission/clearance** | Preferred for authorized apps |

## Comparison with Google Play

Apple's legacy feed is technically much stronger than Google Play's public app
page for this project: 50 versus 3 reviews per app, newest-first ordering,
review titles and app versions, and advertised pagination. Both platforms'
official APIs are restricted to apps available to the authenticated developer
account. Apple's public feed therefore solves the technical coverage problem
but not the authorization and long-term-support problem.

## Recommendation

Do not start recurring ingestion from the legacy customer-reviews feed yet.
Choose one of these paths:

1. If the project covers owned apps, use the documented App Store Connect API
   and run a 24–72 hour repeat test with authorized credentials.
2. If cross-app public data is essential, obtain written confirmation from
   Apple or use a licensed review-data provider whose terms permit research and
   recurring analysis.
3. If neither is available, keep Steam as the primary operational source even
   though Apple provides the better topic breadth and review schema.

The collector in this repository documents the bounded feasibility probe. It
should not be placed on a schedule until the governance issue is resolved.
