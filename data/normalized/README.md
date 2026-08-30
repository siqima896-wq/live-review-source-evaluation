# Normalized Data

Collectors write normalized JSONL files to this directory. The JSONL files are
ignored by Git because they may contain user-generated text. Aggregate,
non-sensitive metrics belong under `results/<source>/run-summary.json`.
