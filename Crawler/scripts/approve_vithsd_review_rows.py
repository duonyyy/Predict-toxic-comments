#!/usr/bin/env python3
"""Accept all annotated review rows as DA_ON after explicit user approval."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    data = root / "data/vithsd_balancing_10000"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=data / "vithsd_religion_race_politics_reviewed.csv")
    parser.add_argument("--output", type=Path, default=data / "vithsd_religion_race_politics_approved.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Input CSV is empty.")

    fields = list(rows[0])
    if "approval_basis" not in fields:
        fields.append("approval_basis")

    review_accepted = 0
    output_rows: list[dict[str, str]] = []
    for row in rows:
        output = dict(row)
        if row.get("data_status") == "CAN_REVIEW":
            output["approval_basis"] = "USER_ACCEPTED_REVIEW"
            review_accepted += 1
        else:
            output["approval_basis"] = "ALREADY_DA_ON"
        output["data_status"] = "DA_ON"
        output["annotation_status"] = "APPROVED"
        output_rows.append(output)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Approved rows: {len(output_rows)}")
    print(f"Review rows accepted by user: {review_accepted}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
