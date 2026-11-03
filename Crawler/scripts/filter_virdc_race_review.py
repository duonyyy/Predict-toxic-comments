#!/usr/bin/env python3
"""Filter ViRDC regional/ethnic comments into a Race review queue.

The ViRDC source labels are provenance only (Other/Discrimination/Supportive).
They are intentionally not converted to ViTHSD CLEAN/OFFENSIVE/HATE here.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = value.replace("_", " ")
    return re.sub(r"\s+", " ", value).strip()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    repo_root = root.parent
    default_virdc = (
        repo_root
        / "_tmp_virdc/Vietnamese-Regional-Discrimination-Detection-main/Dataset/Reginal Discrimination/All Data/balanced_data.csv"
    )
    default_keywords = root / "config/keywords_vi.json"
    data_dir = root / "data/vithsd_balancing_10000"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=default_virdc)
    parser.add_argument("--keywords", type=Path, default=default_keywords)
    parser.add_argument(
        "--approved",
        type=Path,
        default=data_dir / "vithsd_comment_target_approved.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=data_dir / "virdc_race_review_candidates.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=data_dir / "virdc_race_filter_report.md",
    )
    return parser.parse_args()


def load_terms(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    categories = payload.get("categories", {})
    raw_terms: list[str] = []
    for category in ("Vùng miền", "Dân tộc/sắc tộc"):
        values = categories.get(category, {})
        for key in ("neutral_keywords", "toxic_enriched_keywords", "hashtags"):
            raw_terms.extend(values.get(key, []))
    return sorted({normalize(term) for term in raw_terms if normalize(term)}, key=len, reverse=True)


def load_existing(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {normalize(row.get("comment", "")) for row in csv.DictReader(handle)}


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"ViRDC source not found: {args.source}")

    terms = load_terms(args.keywords)
    existing = load_existing(args.approved)
    seen: set[str] = set()
    candidates: list[dict[str, str]] = []
    source_label_counts: Counter[str] = Counter()
    keyword_counts: Counter[str] = Counter()
    source_rows = 0
    lexical_hits = 0
    excluded_existing = 0
    excluded_duplicate = 0

    with args.source.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_rows += 1
            processed = row.get("processed_comment", "")
            comment = re.sub(r"\s+", " ", processed.replace("_", " ")).strip()
            normalized = normalize(comment)
            if not normalized:
                continue
            hits = [term for term in terms if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized)]
            if not hits:
                continue
            lexical_hits += 1
            if normalized in existing:
                excluded_existing += 1
                continue
            if normalized in seen:
                excluded_duplicate += 1
                continue
            seen.add(normalized)
            source_label = row.get("label", "")
            source_label_counts[source_label] += 1
            keyword_counts[hits[0]] += 1
            candidates.append({"comment": comment, "target_scope": "Race"})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["comment", "target_scope"])
        writer.writeheader()
        writer.writerows(candidates)

    report = [
        "# ViRDC Race review filter",
        "",
        f"- Source: `{args.source}`",
        "- Source split: `balanced_data.csv`.",
        "- Filter: lexical hits from `Vùng miền` and `Dân tộc/sắc tộc` in `Crawler/config/keywords_vi.json`.",
        "- Output label: `target_scope=Race` only; ViRDC labels were not converted to CLEAN/OFFENSIVE/HATE.",
        "- Comment transformation: source underscores were replaced with spaces for annotation readability.",
        "",
        f"- Source rows: {source_rows:,}",
        f"- Lexical-hit rows: {lexical_hits:,}",
        f"- Excluded because already in approved file: {excluded_existing:,}",
        f"- Excluded duplicate after normalization: {excluded_duplicate:,}",
        f"- Review candidates written: {len(candidates):,}",
        "",
        "## ViRDC source-label distribution among retained candidates",
        "",
        "| Source label | Count |",
        "|---:|---:|",
    ]
    report.extend(f"| {label or '(blank)'} | {count:,} |" for label, count in sorted(source_label_counts.items()))
    report.extend([
        "",
        "> The source labels are not ViTHSD severity labels. Every row needs semantic review before it enters the approved dataset.",
        "",
    ])
    args.report.write_text("\n".join(report), encoding="utf-8")

    print(f"Source rows: {source_rows}")
    print(f"Lexical-hit rows: {lexical_hits}")
    print(f"Excluded existing: {excluded_existing}")
    print(f"Excluded duplicate: {excluded_duplicate}")
    print(f"Review candidates: {len(candidates)}")
    print(f"Output: {args.output}")
    print(f"Report: {args.report}")
    print(f"Source labels: {dict(source_label_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
