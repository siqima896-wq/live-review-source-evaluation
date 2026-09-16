# Google Play Third Party Collection Test

Test date: 2026-09-15 America Chicago

## Decision summary

The bounded test **passed technically for volume, multi-app pagination, and an
immediate repeat**, but it did **not** resolve access-governance or long-term
reliability concerns.

The open-source Python package
[`google-play-scraper`](https://github.com/JoMingyu/google-play-scraper) 1.2.7
retrieved 200 newest-sorted reviews from each of three unrelated apps in both
runs. Each target returned two 100-record pages through continuation tokens.
Run 2 reproduced all 600 Run 1 review IDs, with no duplicate IDs, missing core
fields, or observed record changes.

This is a materially stronger technical result than the initial public-page
test, which exposed only three curated review cards per app. It shows that a
third-party route can return a useful bounded volume across multiple products.
It does not make the route an official or supported Google API.

## Method

The test used a third-party, MIT-licensed open-source package. It did not use
Google's official Reviews API and did not authenticate through Play Console.
The package depends on undocumented Google Play interfaces.

| Setting | Value |
|---|---|
| Package | `google-play-scraper` 1.2.7 |
| Storefront | United States |
| Language | English |
| Sort | Newest |
| Apps | Duolingo, Spotify, Uber |
| Page size | 100 reviews |
| Pages per app | 2 |
| Maximum per app per run | 200 reviews |
| Runs | 2 immediate runs |

Reviewer names and profile images were discarded. Review and developer-reply
text was retained only in ignored local JSONL files. The committed
[aggregate summary](../../results/google-play-third-party/run-summary.json)
contains no review text or reviewer identifiers.

## Observed results

| App | Category | Run 1 | Run 2 | Shared IDs | New in Run 2 | Absent in Run 2 | Changed |
|---|---|---:|---:|---:|---:|---:|---:|
| Duolingo | Education | 200 | 200 | 200 | 0 | 0 | 0 |
| Spotify | Music and Audio | 200 | 200 | 200 | 0 | 0 | 0 |
| Uber | Maps and Navigation | 200 | 200 | 200 | 0 | 0 | 0 |
| **Total** |  | **600** | **600** | **600** | **0** | **0** | **0** |

Both runs completed without surfaced errors. Every app returned two full pages,
and a continuation token remained available after page two. Run 2 contained
600 unique review IDs and had no missing review ID, text, star rating,
timestamp, or helpful-count value. Seventeen records included a developer
reply. The average rating was 4.00 out of 5; this descriptive value should not
be treated as a population estimate.

## What the test establishes

- A substantially larger sample than the initial public page can be collected.
- The method works across three unrelated app categories in the tested locale.
- Continuation-token pagination returned two non-duplicative pages per app.
- An immediate rerun was reproducible at the review-ID and tested-field level.
- Stable review IDs make local deduplication and change detection possible.

## What the test does not establish

- **Official support:** the package is not a Google API and Google does not
  provide a supported cross-app reviews API for this use case.
- **Long-term stability:** the test repeated within seconds. It does not show
  that the method will continue to work after Google changes its internal
  interfaces.
- **Complete history:** continuation beyond the bounded two pages was not
  tested, and a continuation token is not evidence that all historical reviews
  are obtainable.
- **Representative sampling:** newest sorting and locale parameters do not
  prove reviewer geography or population representativeness.
- **Reliable error reporting:** the tested package catches some internal
  request or parsing failures, so a short or empty result may not include a
  detailed underlying error.
- **Governance clearance:** successful collection does not establish
  permission for recurring automated access or downstream analysis. The
  package's latest [PyPI release](https://pypi.org/project/google-play-scraper/)
  was published in June 2024, which also creates a maintenance risk.

## Decision impact

The test changes the **technical** assessment of Google Play: the third-party
route is capable of meaningful bounded collection and short-term repeat runs,
so the earlier nine-card public-page limitation is not a technical volume
barrier if an unofficial tool is acceptable.

The test does not change the **governance** assessment. For a bounded research
prototype, Google Play is now the strongest broad app-review option on observed
volume and pagination. It should not be placed on a recurring production
schedule unless the team explicitly accepts the unofficial dependency and
clears the relevant access and downstream-use requirements. If supported,
official cross-app access is mandatory, neither this route nor Apple's legacy
feed currently qualifies; the correct decision would be to pause rather than
default to Steam, whose product and topic coverage remains too narrow.

## Reproduce the test

```bash
python3 -m pip install -r requirements.txt
python3 src/collectors/google_play_third_party_test.py
```

The script is bounded by default to two 100-review pages per app and two runs.
It commits only aggregate evidence; normalized review text remains local.
