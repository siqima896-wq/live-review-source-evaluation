import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "steam"
RESULTS_DIR = PROJECT_ROOT / "results" / "steam"


def unix_to_iso(value):
    if value is None:
        return None

    return datetime.fromtimestamp(
        value,
        tz=timezone.utc,
    ).isoformat()


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    review_files = sorted(
        DATA_DIR.glob("steam_reviews_*.jsonl")
    )

    if not review_files:
        raise FileNotFoundError(
            "No steam_reviews_*.jsonl files found"
        )

    # 分析最新一次运行
    input_file = review_files[-1]

    records = []

    with input_file.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                print(
                    f"Invalid JSON on line {line_number}: {error}"
                )

    keys = [
        (
            record.get("app_id"),
            record.get("recommendation_id"),
        )
        for record in records
    ]

    key_counts = Counter(keys)

    duplicate_keys = [
        key
        for key, count in key_counts.items()
        if count > 1
    ]

    app_counts = Counter(
        record.get("game_name")
        for record in records
    )

    language_counts = Counter(
        record.get("language")
        for record in records
    )

    missing_recommendation_id = sum(
        not record.get("recommendation_id")
        for record in records
    )

    missing_review_text = sum(
        not str(record.get("review_text") or "").strip()
        for record in records
    )

    missing_created_timestamp = sum(
        record.get("timestamp_created") is None
        for record in records
    )

    positive_reviews = sum(
        record.get("voted_up") is True
        for record in records
    )

    negative_reviews = sum(
        record.get("voted_up") is False
        for record in records
    )

    text_lengths = [
        len(str(record.get("review_text") or "").strip())
        for record in records
    ]

    created_timestamps = [
        record["timestamp_created"]
        for record in records
        if record.get("timestamp_created") is not None
    ]

    report = {
        "input_file": str(input_file),
        "total_records": len(records),
        "unique_review_keys": len(set(keys)),
        "duplicate_keys_in_output": len(duplicate_keys),
        "records_by_game": dict(app_counts),
        "languages": dict(language_counts),
        "missing_recommendation_id": (
            missing_recommendation_id
        ),
        "missing_review_text": missing_review_text,
        "missing_timestamp_created": (
            missing_created_timestamp
        ),
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
        "positive_percentage": round(
            positive_reviews / len(records) * 100,
            2,
        ) if records else None,
        "average_review_length": round(
            mean(text_lengths),
            2,
        ) if text_lengths else None,
        "earliest_review": unix_to_iso(
            min(created_timestamps)
        ) if created_timestamps else None,
        "latest_review": unix_to_iso(
            max(created_timestamps)
        ) if created_timestamps else None,
    }

    report_file = RESULTS_DIR / (
        f"quality_report_{input_file.stem}.json"
    )

    with report_file.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(json.dumps(report, indent=2))
    print()
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
