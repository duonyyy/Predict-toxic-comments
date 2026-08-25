"""Compute inter-annotator agreement for DS108 annotation CSV files.

The script compares two independently completed CSV files. It reports raw
agreement and Cohen's kappa for each taxonomy field, and writes a disagreement
CSV for adjudication.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


FIELDS = ("toxicity", "expression_type")


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"File không có dữ liệu: {path}")
    if "row_id" not in rows[0]:
        raise ValueError(f"Thiếu cột row_id: {path}")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        row_id = str(row.get("row_id", "")).strip()
        if not row_id:
            raise ValueError(f"Có row_id rỗng trong {path}")
        if row_id in result:
            raise ValueError(f"row_id trùng trong {path}: {row_id}")
        result[row_id] = row
    return result


def normalize_label(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or normalized.lower() in {"null", "none", "nan"}:
        return None
    return normalized


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float | None:
    if not labels_a or len(labels_a) != len(labels_b):
        return None
    total = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / total
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    categories = set(counts_a) | set(counts_b)
    expected = sum(
        (counts_a[label] / total) * (counts_b[label] / total)
        for label in categories
    )
    if expected == 1:
        return 1.0 if observed == 1 else 0.0
    return (observed - expected) / (1 - expected)


def evaluate_field(
    common_ids: list[str], rows_a: dict[str, dict[str, str]], rows_b: dict[str, dict[str, str]], field: str
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    compared_a: list[str] = []
    compared_b: list[str] = []
    missing_a = 0
    missing_b = 0
    disagreements: list[dict[str, str]] = []

    for row_id in common_ids:
        label_a = normalize_label(rows_a[row_id].get(field))
        label_b = normalize_label(rows_b[row_id].get(field))
        if label_a is None:
            missing_a += 1
        if label_b is None:
            missing_b += 1
        if label_a is None or label_b is None:
            continue
        compared_a.append(label_a)
        compared_b.append(label_b)
        if label_a != label_b:
            disagreements.append(
                {
                    "row_id": row_id,
                    "field": field,
                    "annotator_a": label_a,
                    "annotator_b": label_b,
                    "comment": rows_a[row_id].get("comment", ""),
                }
            )

    n = len(compared_a)
    agreement = sum(a == b for a, b in zip(compared_a, compared_b)) / n if n else None
    return (
        {
            "n_common_rows": len(common_ids),
            "n_compared": n,
            "missing_annotator_a": missing_a,
            "missing_annotator_b": missing_b,
            "n_disagreements": len(disagreements),
            "observed_agreement": agreement,
            "cohen_kappa": cohen_kappa(compared_a, compared_b),
        },
        disagreements,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotator_a", type=Path)
    parser.add_argument("annotator_b", type=Path)
    parser.add_argument("--report", type=Path, default=Path("iaa_report.json"))
    parser.add_argument("--disagreements", type=Path, default=Path("iaa_disagreements.csv"))
    args = parser.parse_args()

    rows_a = read_rows(args.annotator_a)
    rows_b = read_rows(args.annotator_b)
    common_ids = sorted(set(rows_a) & set(rows_b))
    if not common_ids:
        raise ValueError("Hai file không có row_id chung.")

    report: dict[str, Any] = {
        "annotator_a": str(args.annotator_a),
        "annotator_b": str(args.annotator_b),
        "n_rows_a": len(rows_a),
        "n_rows_b": len(rows_b),
        "n_common_rows": len(common_ids),
        "fields": {},
    }
    all_disagreements: list[dict[str, str]] = []
    for field in FIELDS:
        metrics, disagreements = evaluate_field(common_ids, rows_a, rows_b, field)
        report["fields"][field] = metrics
        all_disagreements.extend(disagreements)

    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.disagreements.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["row_id", "field", "annotator_a", "annotator_b", "comment"],
        )
        writer.writeheader()
        writer.writerows(all_disagreements)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Đã lưu báo cáo: {args.report}")
    print(f"Đã lưu hàng bất đồng: {args.disagreements}")


if __name__ == "__main__":
    main()
