#!/usr/bin/env python3
"""Export newly crawled YouTube candidates for the remaining VithSD label gaps."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path


TARGET_CATEGORIES = ("Tôn giáo", "Dân tộc/sắc tộc", "Politics")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "").casefold()).strip()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root / "data/youtube/youtube_comments_keywords.csv")
    parser.add_argument("--dataset", type=Path, default=root.parent / "Dataset/final_cleaned_comments.csv")
    parser.add_argument("--output", type=Path, default=root / "data/vithsd_balancing_10000/vithsd_gap_crawl_candidates.csv")
    parser.add_argument("--report", type=Path, default=root / "data/vithsd_balancing_10000/vithsd_gap_crawl_run_report.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.dataset.open(encoding="utf-8-sig", newline="") as handle:
        existing = {normalize(row.get("comment", "")) for row in csv.DictReader(handle)}

    with args.source.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("category") in TARGET_CATEGORIES]

    seen: set[str] = set()
    candidates: list[dict[str, str]] = []
    for row in rows:
        comment = normalize(row.get("comment", ""))
        if not comment or comment in existing or comment in seen:
            continue
        seen.add(comment)
        candidates.append(
            {
                "candidate_id": f"yt_gap_{len(candidates) + 1:06d}",
                "platform": row.get("platform", ""),
                "retrieval_category": row.get("category", ""),
                "query_type": row.get("query_type", ""),
                "keyword": row.get("keyword", ""),
                "content_id": row.get("content_id", ""),
                "video_id": row.get("video_id", ""),
                "title": row.get("title", ""),
                "comment_id": row.get("comment_id", ""),
                "author": row.get("author", ""),
                "published_at": row.get("published_at", ""),
                "comment": row.get("comment", ""),
                "needs_semantic_review": "1",
                "source_file": str(args.source),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(candidates[0]) if candidates else [
        "candidate_id", "platform", "retrieval_category", "query_type", "keyword", "content_id",
        "video_id", "title", "comment_id", "author", "published_at", "comment",
        "needs_semantic_review", "source_file",
    ]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    by_category = Counter(row["retrieval_category"] for row in candidates)
    by_type = Counter((row["retrieval_category"], row["query_type"]) for row in candidates)
    report = [
        "# VithSD focused crawl run",
        "",
        "- Source: `Crawler/data/youtube/youtube_comments_keywords.csv`",
        "- Scope: retrieval categories `Tôn giáo`, `Dân tộc/sắc tộc`, `Politics`.",
        "- Existing-dataset exclusion: normalized comments already in `Dataset/final_cleaned_comments.csv` were removed.",
        "- Deduplication: one candidate per normalized comment; no semantic label was assigned.",
        "",
        f"- Target-category source rows: {len(rows):,}",
        f"- Exported unique new candidates: {len(candidates):,}",
        f"- Excluded as existing/duplicate: {len(rows) - len(candidates):,}",
        "",
        "## Candidates by retrieval category",
        "",
        "| Retrieval category | Candidates |",
        "|---|---:|",
    ]
    report.extend(f"| {category} | {by_category.get(category, 0):,} |" for category in TARGET_CATEGORIES)
    report.extend([
        "",
        "## Candidates by query type",
        "",
        "| Retrieval category | Query type | Candidates |",
        "|---|---|---:|",
    ])
    report.extend(
        f"| {category} | {query_type} | {count:,} |"
        for (category, query_type), count in sorted(by_type.items())
    )
    report.extend([
        "",
        "> Retrieval category and query type are provenance only. Every exported row still requires semantic annotation into the VithSD target labels and quality review.",
        "",
    ])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report), encoding="utf-8")
    print(f"Exported {len(candidates)} candidates to {args.output}")
    print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
