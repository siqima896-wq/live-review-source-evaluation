import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


GAMES = {
    620: "Portal 2",
    413150: "Stardew Valley",
    1091500: "Cyberpunk 2077",
    3388440: "Are You Happy",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "steam"
RESULTS_DIR = PROJECT_ROOT / "results" / "steam"

# 每个游戏最多采集3页
PAGES_PER_GAME = 3

# Steam官方文档说明每页最多可请求100条
REVIEWS_PER_PAGE = 100

# 每次翻页之间等待1秒，避免请求过密
REQUEST_DELAY_SECONDS = 1


def fetch_review_page(app_id: int, cursor: str = "*") -> dict:
    """
    从Steam取得一页评论。
    """

    url = f"https://store.steampowered.com/appreviews/{app_id}"

    params = {
        "json": 1,
        "filter": "recent",
        "language": "english",
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": REVIEWS_PER_PAGE,
        "cursor": cursor,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
        headers={
            "User-Agent": "Siqi-Data-Ingestion-Prototype/0.1"
        },
    )

    print(
        f"App {app_id}: "
        f"HTTP {response.status_code}, "
        f"{len(response.content)} bytes"
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("success") != 1:
        raise RuntimeError(
            f"Steam returned an unsuccessful response for app {app_id}"
        )

    return payload


def normalize_review(
    app_id: int,
    game_name: str,
    review: dict,
) -> dict:
    """
    将Steam原始评论转换成统一的数据结构。
    """

    author = review.get("author", {})

    return {
        "source": "steam",
        "app_id": app_id,
        "game_name": game_name,
        "recommendation_id": review.get("recommendationid"),
        "review_text": review.get("review"),
        "language": review.get("language"),
        "timestamp_created": review.get("timestamp_created"),
        "timestamp_updated": review.get("timestamp_updated"),
        "voted_up": review.get("voted_up"),
        "votes_up": review.get("votes_up"),
        "votes_funny": review.get("votes_funny"),
        "comment_count": review.get("comment_count"),
        "steam_purchase": review.get("steam_purchase"),
        "received_for_free": review.get("received_for_free"),
        "written_during_early_access": review.get(
            "written_during_early_access"
        ),
        "playtime_at_review": author.get("playtime_at_review"),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_game_reviews(
    app_id: int,
    game_name: str,
) -> list[dict]:

    cursor = "*"
    collected = []
    seen_ids = set()

    for page_number in range(1, PAGES_PER_GAME + 1):
        payload = fetch_review_page(app_id, cursor)
        reviews = payload.get("reviews", [])

        print(
            f"{game_name}: page {page_number}, "
            f"{len(reviews)} reviews returned"
        )

        if not reviews:
            print(f"{game_name}: no more reviews")
            break

        for review in reviews:
            recommendation_id = review.get("recommendationid")

            if not recommendation_id:
                print(
                    f"{game_name}: skipped a review "
                    "without recommendation ID"
                )
                continue

            if recommendation_id in seen_ids:
                continue

            seen_ids.add(recommendation_id)

            normalized_review = normalize_review(
                app_id,
                game_name,
                review,
            )

            collected.append(normalized_review)

        next_cursor = payload.get("cursor")

        if not next_cursor:
            print(f"{game_name}: no next cursor returned")
            break

        if next_cursor == cursor:
            print(f"{game_name}: cursor did not change")
            break

        cursor = next_cursor

        time.sleep(REQUEST_DELAY_SECONDS)

    return collected


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    run_time = datetime.now(timezone.utc)
    run_id = run_time.strftime("%Y%m%dT%H%M%SZ")

    all_reviews = []
    game_results = {}

    for app_id, game_name in GAMES.items():
        print()
        print("=" * 60)
        print(f"Collecting reviews for {game_name} ({app_id})")
        print("=" * 60)

        try:
            reviews = collect_game_reviews(
                app_id,
                game_name,
            )

            all_reviews.extend(reviews)

            game_results[str(app_id)] = {
                "game_name": game_name,
                "status": "success",
                "reviews_collected": len(reviews),
            }

        except requests.RequestException as error:
            print(f"Request failed for {game_name}: {error}")

            game_results[str(app_id)] = {
                "game_name": game_name,
                "status": "request_failed",
                "reviews_collected": 0,
                "error": str(error),
            }

        except (ValueError, RuntimeError) as error:
            print(f"Invalid response for {game_name}: {error}")

            game_results[str(app_id)] = {
                "game_name": game_name,
                "status": "invalid_response",
                "reviews_collected": 0,
                "error": str(error),
            }

    output_file = OUTPUT_DIR / f"steam_reviews_{run_id}.jsonl"

    with output_file.open("w", encoding="utf-8") as file:
        for review in all_reviews:
            file.write(
                json.dumps(
                    review,
                    ensure_ascii=False,
                )
                + "\n"
            )

    unique_ids = {
        (
            review["app_id"],
            review["recommendation_id"],
        )
        for review in all_reviews
    }

    summary = {
        "run_id": run_id,
        "run_started_at": run_time.isoformat(),
        "games_requested": len(GAMES),
        "pages_per_game": PAGES_PER_GAME,
        "reviews_per_page": REVIEWS_PER_PAGE,
        "maximum_expected_reviews": (
            len(GAMES)
            * PAGES_PER_GAME
            * REVIEWS_PER_PAGE
        ),
        "reviews_collected": len(all_reviews),
        "unique_reviews": len(unique_ids),
        "duplicate_reviews": (
            len(all_reviews) - len(unique_ids)
        ),
        "game_results": game_results,
        "output_file": str(output_file.relative_to(PROJECT_ROOT)),
    }

    summary_file = RESULTS_DIR / f"run_summary_{run_id}.json"

    with summary_file.open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("Collection complete")
    print("=" * 60)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
