import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "steam"
RESULTS_DIR = PROJECT_ROOT / "results" / "steam"


def load_jsonl(file_path):
    records = []

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                print(
                    f"Invalid JSON in {file_path.name}, "
                    f"line {line_number}: {error}"
                )
                continue

            records.append(record)

    return records


def review_key(record):
    return (
        record.get("app_id"),
        record.get("recommendation_id"),
    )


def build_record_map(records):
    result = {}

    for record in records:
        key = review_key(record)

        if key[0] is None or key[1] is None:
            continue

        result[key] = record

    return result


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    review_files = sorted(
        DATA_DIR.glob("steam_reviews_*.jsonl")
    )

    if len(review_files) < 2:
        raise RuntimeError(
            "At least two steam review files are required."
        )

    run1_file = review_files[-2]
    run2_file = review_files[-1]

    run1_records = load_jsonl(run1_file)
    run2_records = load_jsonl(run2_file)

    run1_map = build_record_map(run1_records)
    run2_map = build_record_map(run2_records)

    run1_keys = set(run1_map)
    run2_keys = set(run2_map)

    shared_keys = run1_keys & run2_keys
    new_keys = run2_keys - run1_keys

    # 这些记录不能直接称为“被删除”；
    # 它们可能只是离开了最近300条评论窗口。
    not_in_run2_keys = run1_keys - run2_keys

    updated_keys = set()

    for key in shared_keys:
        run1_record = run1_map[key]
        run2_record = run2_map[key]

        timestamp_changed = (
            run1_record.get("timestamp_updated")
            != run2_record.get("timestamp_updated")
        )

        text_changed = (
            run1_record.get("review_text")
            != run2_record.get("review_text")
        )

        if timestamp_changed or text_changed:
            updated_keys.add(key)

    all_game_names = sorted({
        record.get("game_name")
        for record in run1_records + run2_records
        if record.get("game_name")
    })

    game_stats = {}

    for game_name in all_game_names:
        run1_game_keys = {
            key
            for key, record in run1_map.items()
            if record.get("game_name") == game_name
        }

        run2_game_keys = {
            key
            for key, record in run2_map.items()
            if record.get("game_name") == game_name
        }

        game_shared = run1_game_keys & run2_game_keys
        game_new = run2_game_keys - run1_game_keys
        game_not_in_run2 = (
            run1_game_keys - run2_game_keys
        )

        game_updated = {
            key
            for key in updated_keys
            if key in game_shared
        }

        game_stats[game_name] = {
            "run1_records": len(run1_game_keys),
            "run2_records": len(run2_game_keys),
            "shared_records": len(game_shared),
            "new_in_run2": len(game_new),
            "not_in_run2_window": len(
                game_not_in_run2
            ),
            "updated_records": len(game_updated),
        }

    run1_positive = Counter(
        record.get("voted_up")
        for record in run1_records
    )

    run2_positive = Counter(
        record.get("voted_up")
        for record in run2_records
    )

    comparison = {
        "run1_file": str(run1_file),
        "run2_file": str(run2_file),
        "run1_total_records": len(run1_records),
        "run2_total_records": len(run2_records),
        "shared_records": len(shared_keys),
        "new_records_in_run2": len(new_keys),
        "not_in_run2_window": len(
            not_in_run2_keys
        ),
        "updated_records": len(updated_keys),
        "run1_positive_reviews": run1_positive.get(
            True, 0
        ),
        "run1_negative_reviews": run1_positive.get(
            False, 0
        ),
        "run2_positive_reviews": run2_positive.get(
            True, 0
        ),
        "run2_negative_reviews": run2_positive.get(
            False, 0
        ),
        "results_by_game": game_stats,
        "sample_new_review_keys": [
            {
                "app_id": key[0],
                "recommendation_id": key[1],
            }
            for key in sorted(new_keys)[:10]
        ],
        "sample_updated_review_keys": [
            {
                "app_id": key[0],
                "recommendation_id": key[1],
            }
            for key in sorted(updated_keys)[:10]
        ],
    }

    run1_id = run1_file.stem.replace(
        "steam_reviews_", ""
    )

    run2_id = run2_file.stem.replace(
        "steam_reviews_", ""
    )

    output_file = RESULTS_DIR / (
        f"run_comparison_{run1_id}_to_{run2_id}.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            comparison,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(json.dumps(comparison, indent=2))
    print()
    print(f"Comparison saved to: {output_file}")


if __name__ == "__main__":
    main()
