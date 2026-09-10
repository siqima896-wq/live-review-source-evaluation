# Normalized Data

Collectors write normalized JSONL files to this directory. The app-store
combiner also writes `app_store_reviews_combined.csv`. JSONL and CSV files in
this directory are ignored by Git because they may contain user-generated
text. Aggregate, non-sensitive metrics belong under `results/`.
