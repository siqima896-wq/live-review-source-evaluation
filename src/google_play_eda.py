"""Create aggregate EDA tables, charts, and metrics for the Google Play sample.

This script reads the newest local ``google_play_eda_*.jsonl`` file by default.
It never writes review text or review IDs to the version-controlled results.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "normalized"
RESULTS_DIR = PROJECT_ROOT / "results" / "google-play-03-expanded-eda"

THEMES = {
    "reliability_or_crashes": ("crash", "crashes", "crashing", "freeze", "freezes", "frozen", "bug", "buggy", "glitch"),
    "login_or_account": ("login", "log in", "sign in", "account", "password", "verification"),
    "ads": (" ad ", " ads ", "advertisement", "advertising"),
    "payment_or_subscription": ("payment", "charged", "charge", "refund", "subscription", "premium", "price", "expensive"),
    "update_or_version": ("update", "updated", "version"),
    "customer_support": ("customer service", "customer support", "support team", "help center"),
    "performance": ("slow", "lag", "laggy", "battery", "loading", "load time"),
}

CORE_FIELDS = ("review_id", "review_text", "star_rating", "helpful_count", "review_timestamp")
OPTIONAL_FIELDS = ("review_created_version", "app_version", "developer_reply_text", "developer_reply_timestamp")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def is_missing(value: object) -> bool:
    return value is None or value == ""


def rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def text_has_theme(text: str, keywords: tuple[str, ...]) -> bool:
    padded = f" {text.casefold()} "
    return any(keyword in padded for keyword in keywords)


def summarize(records: list[dict]) -> dict:
    count = len(records)
    ratings = [int(row["star_rating"]) for row in records if row.get("star_rating") is not None]
    lengths = [len(row.get("review_text") or "") for row in records]
    helpful = [int(row.get("helpful_count") or 0) for row in records]
    timestamps = [parse_datetime(row.get("review_timestamp")) for row in records]
    timestamps = [value for value in timestamps if value is not None]
    replies = sum(bool(row.get("developer_reply_present")) for row in records)
    negative = sum(value <= 2 for value in ratings)
    positive = sum(value >= 4 for value in ratings)
    theme_counts = {
        theme: sum(text_has_theme(row.get("review_text") or "", words) for row in records)
        for theme, words in THEMES.items()
    }
    return {
        "records": count,
        "mean_rating": round(mean(ratings), 3) if ratings else None,
        "median_rating": round(median(ratings), 3) if ratings else None,
        "one_star_rate": rate(sum(value == 1 for value in ratings), len(ratings)),
        "negative_rating_rate": rate(negative, len(ratings)),
        "positive_rating_rate": rate(positive, len(ratings)),
        "mean_text_length": round(mean(lengths), 2) if lengths else None,
        "median_text_length": round(median(lengths), 2) if lengths else None,
        "p90_text_length": round(percentile(lengths, 0.9) or 0, 2),
        "mean_helpful_count": round(mean(helpful), 3) if helpful else None,
        "median_helpful_count": round(median(helpful), 3) if helpful else None,
        "reviews_with_helpful_votes_rate": rate(sum(value > 0 for value in helpful), len(helpful)),
        "developer_reply_rate": rate(replies, count),
        "version_coverage_rate": rate(sum(not is_missing(row.get("review_created_version")) for row in records), count),
        "oldest_review_timestamp": min(timestamps).isoformat() if timestamps else None,
        "newest_review_timestamp": max(timestamps).isoformat() if timestamps else None,
        "time_span_days": round((max(timestamps) - min(timestamps)).total_seconds() / 86400, 2) if timestamps else None,
        "theme_rates": {theme: rate(value, count) for theme, value in theme_counts.items()},
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def xml_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_chart(path: Path, title: str, labels: list[str], values: list[float],
              x_label: str, value_format: str = ".2f",
              axis_maximum: float | None = None) -> None:
    width, left, right, top, row_height = 1000, 230, 80, 80, 34
    height = top + len(labels) * row_height + 75
    plot_width = width - left - right
    maximum = axis_maximum if axis_maximum is not None else (max(values) if values else 1)
    maximum = maximum or 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{xml_escape(title)}</text>',
    ]
    for index, (label, value) in enumerate(zip(labels, values)):
        y = top + index * row_height
        bar_width = value / maximum * plot_width
        parts.append(f'<text x="{left-12}" y="{y+18}" text-anchor="end" font-family="Arial" font-size="13">{xml_escape(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="22" rx="3" fill="#3973ac"/>')
        parts.append(f'<text x="{left+bar_width+8}" y="{y+17}" font-family="Arial" font-size="12">{format(value, value_format)}</text>')
    parts.append(f'<text x="{left + plot_width/2}" y="{height-20}" text-anchor="middle" font-family="Arial" font-size="13">{xml_escape(x_label)}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def stacked_rating_chart(path: Path, distributions: dict[str, Counter]) -> None:
    labels = list(distributions)
    width, left, right, top, row_height = 1050, 230, 120, 90, 38
    height = top + len(labels) * row_height + 100
    plot_width = width - left - right
    colors = {1: "#b2182b", 2: "#ef8a62", 3: "#d9d9d9", 4: "#67a9cf", 5: "#2166ac"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="{width/2}" y="38" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">Rating distribution by category</text>']
    for index, label in enumerate(labels):
        y = top + index * row_height
        total = sum(distributions[label].values()) or 1
        x = left
        parts.append(f'<text x="{left-12}" y="{y+18}" text-anchor="end" font-family="Arial" font-size="13">{xml_escape(label)}</text>')
        for rating in range(1, 6):
            segment = distributions[label][rating] / total * plot_width
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{segment:.1f}" height="23" fill="{colors[rating]}"/>')
            x += segment
    legend_x = left
    for rating in range(1, 6):
        parts.append(f'<rect x="{legend_x}" y="{height-55}" width="18" height="18" fill="{colors[rating]}"/>')
        parts.append(f'<text x="{legend_x+24}" y="{height-41}" font-family="Arial" font-size="12">{rating} star</text>')
        legend_x += 110
    parts.extend([f'<text x="{left+plot_width/2}" y="{height-15}" text-anchor="middle" font-family="Arial" font-size="13">Share of reviews</text>', '</svg>'])
    path.write_text("\n".join(parts), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = sorted(DATA_DIR.glob("google_play_eda_*.jsonl"))
    input_path = args.input or (candidates[-1] if candidates else None)
    if input_path is None or not input_path.exists():
        raise SystemExit("No Google Play EDA JSONL input found. Run the EDA collector first.")
    with input_path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]
    if not records:
        raise SystemExit("The input contains no records.")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    by_app: dict[str, list[dict]] = defaultdict(list)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        by_app[row["app_name"]].append(row)
        by_category[row["category"]].append(row)

    app_rows = []
    for app_name, subset in sorted(by_app.items()):
        stats = summarize(subset)
        app_rows.append({
            "app_name": app_name,
            "package_name": subset[0]["package_name"],
            "category": subset[0]["category"],
            **{key: value for key, value in stats.items() if key != "theme_rates"},
        })
    app_fields = list(app_rows[0])
    write_csv(RESULTS_DIR / "app-summary.csv", app_rows, app_fields)

    category_rows = []
    for category, subset in sorted(by_category.items()):
        stats = summarize(subset)
        category_rows.append({
            "category": category,
            "apps": len({row["package_name"] for row in subset}),
            **{key: value for key, value in stats.items() if key != "theme_rates"},
        })
    write_csv(RESULTS_DIR / "category-summary.csv", category_rows, list(category_rows[0]))

    coverage_rows = []
    for field in (*CORE_FIELDS, *OPTIONAL_FIELDS, "developer_reply_present", "ingested_at"):
        present = sum(not is_missing(row.get(field)) for row in records)
        coverage_rows.append({
            "field": field,
            "field_type": "core" if field in CORE_FIELDS else "optional_or_derived",
            "present_records": present,
            "missing_records": len(records) - present,
            "coverage_rate": rate(present, len(records)),
        })
    write_csv(RESULTS_DIR / "field-coverage.csv", coverage_rows, list(coverage_rows[0]))

    rating_rows = []
    distributions = {}
    for category, subset in sorted(by_category.items()):
        counts = Counter(int(row["star_rating"]) for row in subset)
        distributions[category] = counts
        for rating in range(1, 6):
            rating_rows.append({"category": category, "star_rating": rating, "records": counts[rating], "share": rate(counts[rating], len(subset))})
    write_csv(RESULTS_DIR / "rating-distribution.csv", rating_rows, list(rating_rows[0]))

    theme_rows = []
    for category, subset in sorted(by_category.items()):
        for theme, keywords in THEMES.items():
            mentions = sum(text_has_theme(row.get("review_text") or "", keywords) for row in subset)
            theme_rows.append({"category": category, "theme": theme, "reviews_with_theme": mentions, "share": rate(mentions, len(subset))})
    write_csv(RESULTS_DIR / "theme-summary.csv", theme_rows, list(theme_rows[0]))

    global_stats = summarize(records)
    composite_ids = [(row.get("package_name"), row.get("review_id")) for row in records]
    normalized_texts = [(row.get("review_text") or "").strip().casefold() for row in records]
    exact_text_counts = Counter(value for value in normalized_texts if value)
    duplicate_text_records = sum(value - 1 for value in exact_text_counts.values() if value > 1)
    metadata_consistency = {
        "developer_reply_flag_without_text": sum(bool(row.get("developer_reply_present")) and is_missing(row.get("developer_reply_text")) for row in records),
        "developer_reply_text_without_flag": sum(not is_missing(row.get("developer_reply_text")) and not bool(row.get("developer_reply_present")) for row in records),
        "reply_timestamp_without_reply_text": sum(not is_missing(row.get("developer_reply_timestamp")) and is_missing(row.get("developer_reply_text")) for row in records),
        "review_created_version_vs_app_version_mismatches": sum(row.get("review_created_version") != row.get("app_version") for row in records),
    }
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path.relative_to(PROJECT_ROOT)),
        "scope": {"records": len(records), "apps": len(by_app), "categories": len(by_category)},
        "overall": global_stats,
        "data_quality": {
            "duplicate_composite_review_ids": len(composite_ids) - len(set(composite_ids)),
            "exact_duplicate_text_records": duplicate_text_records,
            "exact_duplicate_text_rate": rate(duplicate_text_records, len(records)),
            "invalid_rating_records": sum(row.get("star_rating") not in (1, 2, 3, 4, 5) for row in records),
            "future_review_timestamps": sum((parse_datetime(row.get("review_timestamp")) or datetime.min.replace(tzinfo=timezone.utc)) > (parse_datetime(row.get("ingested_at")) or datetime.max.replace(tzinfo=timezone.utc)) for row in records),
            **metadata_consistency,
        },
        "field_coverage": {row["field"]: row["coverage_rate"] for row in coverage_rows},
        "app_extremes": {
            "highest_mean_rating": max(app_rows, key=lambda row: row["mean_rating"]),
            "lowest_mean_rating": min(app_rows, key=lambda row: row["mean_rating"]),
            "highest_developer_reply_rate": max(app_rows, key=lambda row: row["developer_reply_rate"]),
            "longest_median_review": max(app_rows, key=lambda row: row["median_text_length"]),
            "widest_time_span": max(app_rows, key=lambda row: row["time_span_days"]),
        },
        "category_extremes": {
            "highest_mean_rating": max(category_rows, key=lambda row: row["mean_rating"]),
            "lowest_mean_rating": min(category_rows, key=lambda row: row["mean_rating"]),
            "highest_developer_reply_rate": max(category_rows, key=lambda row: row["developer_reply_rate"]),
            "longest_median_review": max(category_rows, key=lambda row: row["median_text_length"]),
        },
        "theme_definition": {theme: list(words) for theme, words in THEMES.items()},
        "limitations": [
            "The sample contains the newest reviews returned for an English-language US storefront request; it is not random or population-representative.",
            "Storefront and language parameters do not establish reviewer location or guarantee that every review is written in English.",
            "Each app contributes the same bounded count, so pooled results intentionally do not reflect app popularity or total review volume.",
            "Theme rates use fixed keyword matching and indicate mentions, not sentiment, intent, or a complete topic classification.",
            "The collection route is an unofficial third-party package that depends on undocumented Google Play interfaces.",
        ],
    }
    (RESULTS_DIR / "analysis-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    ordered_apps = sorted(app_rows, key=lambda row: row["mean_rating"])
    bar_chart(RESULTS_DIR / "app-mean-rating.svg", "Mean rating by app (newest 300 reviews)", [row["app_name"] for row in ordered_apps], [row["mean_rating"] for row in ordered_apps], "Mean star rating (0–5)", ".2f", 5.0)
    ordered_categories = sorted(category_rows, key=lambda row: row["developer_reply_rate"])
    bar_chart(RESULTS_DIR / "category-developer-reply-rate.svg", "Developer reply rate by category", [row["category"] for row in ordered_categories], [row["developer_reply_rate"] * 100 for row in ordered_categories], "Reviews with a developer reply (0–100%)", ".1f", 100.0)
    stacked_rating_chart(RESULTS_DIR / "category-rating-distribution.svg", distributions)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Aggregate EDA outputs written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
