#!/usr/bin/env python3
"""Keep only Religion, Race/Ethnicity, and Politics rows from the merged file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


TARGET_COLUMNS = (
    ("Religion", "religion_creed"),
    ("Race", "race_ethnicity"),
    ("Politics", "politics"),
)
CRAWL_CATEGORY_MAP = {
    "Tôn giáo": "Religion",
    "Dân tộc/sắc tộc": "Race",
    "Politics": "Politics",
}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    data = root / "data/vithsd_balancing_10000"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=data / "vithsd_stable_review_merged.csv")
    parser.add_argument("--output", type=Path, default=data / "vithsd_religion_race_politics.csv")
    parser.add_argument(
        "--include-crawl",
        action="store_true",
        help="Keep pending crawl candidates as well; default keeps only annotated rows.",
    )
    parser.add_argument(
        "--two-fields",
        action="store_true",
        help="Export only comment and target_scope columns.",
    )
    return parser.parse_args()


def positive(value: str) -> bool:
    try:
        return int(value or 0) > 0
    except ValueError:
        return False


def scope_for(row: dict[str, str]) -> list[str]:
    if row.get("data_status") == "CAN_REVIEW_CRAWL":
        category = CRAWL_CATEGORY_MAP.get(row.get("retrieval_category", ""))
        return [category] if category else []
    return [label for label, column in TARGET_COLUMNS if positive(row.get(column, ""))]


def main() -> int:
    args = parse_args()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Input merged CSV is empty.")

    fields = list(rows[0])
    if "target_scope" not in fields:
        fields.append("target_scope")
    kept: list[dict[str, str]] = []
    for row in rows:
        if row.get("data_status") == "CAN_REVIEW_CRAWL" and not args.include_crawl:
            continue
        scope = scope_for(row)
        if not scope:
            continue
        output = dict(row)
        output["target_scope"] = "|".join(scope)
        kept.append(output)

    if args.two_fields:
        fields = ["comment", "target_scope"]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(kept)

    print(f"Input rows: {len(rows)}")
    print(f"Kept rows: {len(kept)}")
    print(f"Dropped rows: {len(rows) - len(kept)}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
