"""Apply manually cleaned review rows back to the active crawler JSON files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
from pathlib import Path
from typing import Any


def walk_comments(value: Any):
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
    ) as handle:
        temp_path = Path(handle.name)
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def normalize_file(root: Path, raw: str) -> Path:
    relative = raw.replace("/", "\\")
    if relative.lower().startswith("crawler\\"):
        relative = relative[len("Crawler\\") :]
    return root / relative


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def remove_first_words(value: str, count: int) -> str:
    matches = list(re.finditer(r"\S+", value))
    if len(matches) <= count:
        return ""
    return value[matches[count].start() :].strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("Crawler"))
    parser.add_argument(
        "--cleaned",
        type=Path,
        default=Path("Crawler/data/facebook/tag_prefix_review_cleaned.csv"),
    )
    args = parser.parse_args()

    with args.cleaned.open(encoding="utf-8-sig", newline="") as handle:
        cleaned_rows = list(csv.DictReader(handle))

    grouped: dict[Path, list[tuple[int, str]]] = {}
    for row in cleaned_rows:
        suggestion = row.get("suggestion", "")
        match = re.search(r"remove first (\d+) words", suggestion)
        if not match:
            raise RuntimeError(f"Không đọc được số từ cần xóa: {suggestion!r}")
        path = normalize_file(args.root, row["file"])
        grouped.setdefault(path, []).append(
            (int(match.group(1)), row.get("original", "").strip())
        )

    changed_comments = 0
    changed_files = 0
    unmatched: list[str] = []
    pending: list[tuple[Path, Any]] = []

    for path, replacements in grouped.items():
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        comments = list(walk_comments(data))
        cursor = 0
        file_changed = False
        for count, new in replacements:
            found = None
            for index in range(cursor, len(comments)):
                current = comments[index]["comment"]
                suffix = remove_first_words(current, count)
                current_normalized = normalize_text(current)
                new_normalized = normalize_text(new)
                if (
                    current_normalized == new_normalized
                    or normalize_text(suffix) == new_normalized
                    or (
                        new_normalized
                        and current_normalized.endswith(new_normalized)
                    )
                ):
                    found = index
                    break
            if found is None:
                unmatched.append(f"{path}: remove {count} words => {new!r}")
                continue
            if comments[found]["comment"] != new:
                comments[found]["comment"] = new
                changed_comments += 1
                file_changed = True
            cursor = found + 1
        if file_changed:
            pending.append((path, data))

    if unmatched:
        print("UNMATCHED:")
        for item in unmatched:
            print(item)
        raise RuntimeError(
            f"Không đối chiếu được {len(unmatched)} dòng; chưa ghi bất kỳ file nào"
        )

    for path, data in pending:
        write_json_atomic(path, data)
        changed_files += 1

    print(f"changed_files={changed_files}")
    print(f"changed_comments={changed_comments}")
    print(f"review_rows={len(cleaned_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
