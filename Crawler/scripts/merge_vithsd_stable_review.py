#!/usr/bin/env python3
"""Merge stable VithSD rows and review candidates into one auditable CSV."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path


OUTPUT_FIELDS = [
    "record_id",
    "data_status",
    "annotation_status",
    "source_kind",
    "source_file",
    "original_row_id",
    "candidate_id",
    "comment",
    "individual",
    "groups",
    "religion_creed",
    "race_ethnicity",
    "politics",
    "selected",
    "confidence",
    "primary_target",
    "reason",
    "retrieval_category",
    "query_type",
    "keyword",
    "content_id",
    "video_id",
    "title",
    "comment_id",
    "author",
    "published_at",
    "needs_semantic_review",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "").casefold()).strip()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    data = root / "data/vithsd_balancing_10000"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stable", type=Path, default=data / "vithsd_balancing_10000.csv")
    parser.add_argument("--review", type=Path, default=data / "vithsd_review_queue.csv")
    parser.add_argument("--crawl", type=Path, default=data / "vithsd_gap_crawl_candidates.csv")
    parser.add_argument("--output", type=Path, default=data / "vithsd_stable_review_merged.csv")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def map_annotated(row: dict[str, str], source_file: str, status: str) -> dict[str, str]:
    output = {field: "" for field in OUTPUT_FIELDS}
    output.update(
        {
            "data_status": status,
            "annotation_status": "ANNOTATED",
            "source_kind": "selected_yes" if status == "DA_ON" else "annotated_review",
            "source_file": source_file,
            "original_row_id": row.get("row_id", ""),
            "comment": row.get("comment", ""),
            "individual": row.get("individual", ""),
            "groups": row.get("groups", ""),
            "religion_creed": row.get("religion_creed", ""),
            "race_ethnicity": row.get("race_ethnicity", ""),
            "politics": row.get("politics", ""),
            "selected": row.get("selected", ""),
            "confidence": row.get("confidence", ""),
            "primary_target": row.get("primary_target", ""),
            "reason": row.get("reason", ""),
            "needs_semantic_review": "0",
        }
    )
    return output


def map_crawl(row: dict[str, str], source_file: str) -> dict[str, str]:
    output = {field: "" for field in OUTPUT_FIELDS}
    output.update(
        {
            "data_status": "CAN_REVIEW_CRAWL",
            "annotation_status": "PENDING_SEMANTIC_REVIEW",
            "source_kind": "youtube_gap_crawl",
            "source_file": source_file,
            "candidate_id": row.get("candidate_id", ""),
            "comment": row.get("comment", ""),
            "retrieval_category": row.get("retrieval_category", ""),
            "query_type": row.get("query_type", ""),
            "keyword": row.get("keyword", ""),
            "content_id": row.get("content_id", ""),
            "video_id": row.get("video_id", ""),
            "title": row.get("title", ""),
            "comment_id": row.get("comment_id", ""),
            "author": row.get("author", ""),
            "published_at": row.get("published_at", ""),
            "needs_semantic_review": "1",
        }
    )
    return output


def main() -> int:
    args = parse_args()
    sources = [
        ("DA_ON", args.stable, lambda row: map_annotated(row, args.stable.name, "DA_ON")),
        ("CAN_REVIEW", args.review, lambda row: map_annotated(row, args.review.name, "CAN_REVIEW")),
        ("CAN_REVIEW_CRAWL", args.crawl, lambda row: map_crawl(row, args.crawl.name)),
    ]

    merged: list[dict[str, str]] = []
    seen_comments: dict[str, str] = {}
    duplicate_count = 0
    for _, path, mapper in sources:
        rows = read_rows(path)
        for row in rows:
            comment = normalize(row.get("comment", ""))
            if not comment:
                continue
            if comment in seen_comments:
                duplicate_count += 1
                continue
            mapped = mapper(row)
            mapped["record_id"] = f"vithsd_{len(merged) + 1:06d}"
            seen_comments[comment] = mapped["record_id"]
            merged.append(mapped)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)

    counts = {status: sum(row["data_status"] == status for row in merged) for status, _, _ in sources}
    print(f"Merged rows: {len(merged)}")
    print(f"Counts: {counts}")
    print(f"Duplicate normalized comments skipped: {duplicate_count}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
