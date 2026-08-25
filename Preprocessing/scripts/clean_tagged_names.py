"""Remove high-confidence Facebook tag prefixes from comment text.

The crawler currently stores flattened comment text, so the exact Facebook
mention metadata is no longer available.  This script therefore makes only a
conservative edit and writes ambiguous candidates to a CSV for manual review.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
from pathlib import Path
from typing import Any


HIGH_CONFIDENCE_NEXT = {
    "t",
    "m",
    "mình",
    "tôi",
    "tao",
    "bạn",
    "ơi",
    "à",
    "ạ",
    "nhé",
    "nha",
    "nhỉ",
}

REVIEW_NEXT = HIGH_CONFIDENCE_NEXT | {
    "đã",
    "đang",
    "chưa",
    "có",
    "là",
    "không",
    "với",
    "này",
    "được",
    "thích",
    "ghét",
    "sao",
    "đi",
    "đến",
    "ở",
    "cho",
    "từ",
    "theo",
    "để",
    "như",
    "cũng",
    "vẫn",
    "bị",
    "vào",
    "ra",
    "mang",
    "nói",
    "hỏi",
    "xem",
}

# Sentence starters that commonly look like a proper name when title-cased.
# They are intentionally conservative; doubtful cases go to the review CSV.
NOT_NAME_STARTS = {
    "Alo",
    "Anh",
    "Bà",
    "Bố",
    "Bóng",
    "Bồ",
    "Chị",
    "Chú",
    "Cô",
    "Còn",
    "Cứu",
    "Đất",
    "Đùa",
    "Hà",
    "Hai",
    "Hồi",
    "Khứa",
    "Là",
    "Lúc",
    "Mẹ",
    "Mấy",
    "Nếu",
    "Nét",
    "Nhìn",
    "Ông",
    "Quá",
    "Quả",
    "Sau",
    "Thế",
    "Tôi",
    "Việt",
    "Vấn",
}

EDGE_PUNCTUATION = re.compile(r"^[^\wÀ-ỹĐđ]+|[^\wÀ-ỹĐđ]+$")


def clean_token(token: str) -> str:
    return EDGE_PUNCTUATION.sub("", token)


def is_title_name_word(token: str) -> bool:
    """Accept normal Vietnamese title-case words, not initials/all-caps."""
    return len(token) >= 2 and token.istitle() and token[0].isupper()


def candidate_prefix(text: str, *, high_confidence: bool) -> tuple[int, str] | None:
    tokens = text.strip().split()
    # Prefer the longest prefix so a 3-word name is not reduced to 2 words.
    for length in (4, 3, 2):
        if len(tokens) <= length:
            continue
        name = [clean_token(token) for token in tokens[:length]]
        next_word = clean_token(tokens[length]).lower()
        if not all(is_title_name_word(token) for token in name):
            continue
        if high_confidence:
            if length > 3 or name[0] in NOT_NAME_STARTS:
                continue
            if next_word not in HIGH_CONFIDENCE_NEXT:
                continue
        elif name[0] in NOT_NAME_STARTS or next_word not in REVIEW_NEXT:
            continue
        return length, next_word
    return None


def walk_comments(value: Any):
    # An explicit stack avoids generator recursion overhead on large nested
    # crawler outputs and never descends into scalar comment strings.
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if isinstance(current.get("comment"), str):
                yield current
            stack.extend(
                child
                for child in current.values()
                if isinstance(child, (dict, list))
            )
        elif isinstance(current, list):
            stack.extend(child for child in current if isinstance(child, (dict, list)))


def write_json_atomic(path: Path, data: Any) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp:
        temp_path = Path(temp.name)
        json.dump(data, temp, ensure_ascii=False, indent=2)
        temp.write("\n")
    temp_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(r"Crawler/data/facebook"),
        help="Folder containing crawler JSON files",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(r"Crawler/data/facebook/tag_prefix_review.csv"),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--include-backups",
        action="store_true",
        help="Also edit *.json.bak files; omitted by default to preserve recovery copies",
    )
    args = parser.parse_args()

    paths = sorted(args.root.rglob("*.json"))
    if args.include_backups:
        paths += sorted(args.root.rglob("*.json.bak"))

    review_rows: list[dict[str, str]] = []
    changed_files = 0
    cleaned_comments = 0
    invalid_files = 0

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid_files += 1
            review_rows.append(
                {
                    "file": str(path),
                    "status": "invalid_json",
                    "original": str(exc),
                    "suggestion": "fix JSON manually",
                }
            )
            continue

        file_changed = False
        for item in walk_comments(data):
            original = item["comment"]
            high = candidate_prefix(original, high_confidence=True)
            broad = candidate_prefix(original, high_confidence=False)

            if high is not None:
                length, _ = high
                tokens = original.strip().split()
                item["comment"] = " ".join(tokens[length:]).lstrip()
                file_changed = True
                cleaned_comments += 1
            elif broad is not None:
                length, next_word = broad
                review_rows.append(
                    {
                        "file": str(path),
                        "status": "review",
                        "original": original,
                        "suggestion": f"remove first {length} words; next word={next_word}",
                    }
                )

        if file_changed and not args.dry_run:
            write_json_atomic(path, data)
        changed_files += int(file_changed)

    if not args.dry_run:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["file", "status", "original", "suggestion"],
            )
            writer.writeheader()
            writer.writerows(review_rows)

    print(f"files={len(paths)} changed_files={changed_files}")
    print(f"cleaned_comments={cleaned_comments} review_candidates={len(review_rows)}")
    print(f"invalid_files={invalid_files}")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
