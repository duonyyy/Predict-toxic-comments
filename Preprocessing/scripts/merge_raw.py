"""Merge canonical crawler sources into a four-column raw table."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_CRAWLER_DATA = PROJECT_DIR.parent / "Crawler" / "data"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "data" / "raw"
DEFAULT_SOURCES_CONFIG = PROJECT_DIR / "config" / "sources.json"

RAW_COLUMNS = [
    "row_id",
    "platform",
    "title",
    "comment",
]

INTERNAL_COLUMNS = [
    "row_id",
    "platform",
    "source_name",
    "source_file",
    "source_format",
    "source_record_path",
    "record_type",
    "content_id",
    "content_url",
    "title",
    "comment_id",
    "parent_id",
    "is_reply",
    "author",
    "published_at",
    "updated_at",
    "comment",
    "like_count",
    "category",
    "query_type",
    "keyword",
    "channel_title",
    "page",
    "post_number",
    "raw_record",
]


class MergeError(RuntimeError):
    """Expected merge failure that is safe to show to the user."""


@dataclass(frozen=True)
class SourceSpec:
    name: str
    platform: str
    adapter: str
    relative_path: str
    path: Path

    @property
    def source_format(self) -> str:
        return self.path.suffix.lower().lstrip(".")


@dataclass(frozen=True)
class SourceSnapshot:
    path: Path
    size: int
    modified_ns: int


@dataclass(frozen=True)
class MergeResult:
    total_rows: int
    source_counts: dict[str, int]
    csv_path: Path
    json_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gop cac nguon canonical trong Crawler/data vao raw.csv va raw.json "
            "voi mot schema chung. Luon rebuild, khong append."
        )
    )
    parser.add_argument(
        "--crawler-data",
        type=Path,
        default=DEFAULT_CRAWLER_DATA,
        help="Thu muc Crawler/data.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Thu muc ghi raw.csv va raw.json.",
    )
    parser.add_argument(
        "--sources-config",
        type=Path,
        default=DEFAULT_SOURCES_CONFIG,
        help="File JSON khai bao cac nguon canonical.",
    )
    return parser.parse_args()


def as_text(value: Any) -> str | None:
    """Map one scalar to a string without trimming or semantic normalization."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y"}


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_row(
    spec: SourceSpec,
    source_record_path: str,
    raw_record: Any,
    **mapped: Any,
) -> dict[str, str | None]:
    row: dict[str, str | None] = {column: None for column in INTERNAL_COLUMNS}
    row.update(
        {
            "row_id": f"{spec.name}:{source_record_path}",
            "platform": spec.platform,
            "source_name": spec.name,
            "source_file": spec.relative_path.replace("\\", "/"),
            "source_format": spec.source_format,
            "source_record_path": source_record_path,
            "raw_record": compact_json(raw_record),
        }
    )
    unknown = set(mapped) - set(INTERNAL_COLUMNS)
    if unknown:
        raise MergeError(
            f"Adapter {spec.adapter} tao cot khong hop le: "
            + ", ".join(sorted(unknown))
        )
    for key, value in mapped.items():
        row[key] = as_text(value)
    return row


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise MergeError(f"Khong doc duoc JSON {path}: {exc}") from exc


def iter_csv_rows(
    spec: SourceSpec,
    required_columns: set[str],
) -> Iterator[tuple[int, dict[str, str]]]:
    try:
        file = spec.path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise MergeError(f"Khong mo duoc CSV {spec.path}: {exc}") from exc
    with file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        missing = required_columns - set(columns)
        if missing:
            raise MergeError(
                f"CSV {spec.relative_path} thieu cot: "
                + ", ".join(sorted(missing))
            )
        try:
            for number, record in enumerate(reader, start=1):
                if None in record:
                    raise MergeError(
                        f"CSV {spec.relative_path} co dong {number} vuot header."
                    )
                yield number, dict(record)
        except csv.Error as exc:
            raise MergeError(
                f"CSV {spec.relative_path} loi tai dong {reader.line_num}: {exc}"
            ) from exc


def adapt_threads(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    # Chap nhan ca file Threads moi va file legacy, nhung chi map ve title/comment.
    # Cac cot post_id, link_bai_viet va ten cot cu khong duoc dua vao raw output.
    for number, record in iter_csv_rows(spec, set()):
        if "title" in record and "comment" in record:
            title = record.get("title")
            comment = record.get("comment")
        elif "tieu_de_bai_viet" in record and "noi_dung_comment" in record:
            title = record.get("tieu_de_bai_viet")
            comment = record.get("noi_dung_comment")
        else:
            raise MergeError(
                f"CSV {spec.relative_path} can cot title/comment "
                "(hoac tieu_de_bai_viet/noi_dung_comment)."
            )
        yield build_row(
            spec,
            f"row[{number}]",
            record,
            record_type="comment",
            title=title,
            comment=comment,
        )


def adapt_tiktok(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    required = {
        "platform",
        "category",
        "query_type",
        "keyword",
        "video_id",
        "title",
        "comment_id",
        "author",
        "published_at",
        "comment",
    }
    for number, record in iter_csv_rows(spec, required):
        query_type = record.get("query_type")
        record_type = (
            "reply"
            if str(query_type or "").casefold() == "apify_post_reply"
            else "comment"
        )
        yield build_row(
            spec,
            f"row[{number}]",
            record,
            record_type=record_type,
            content_id=first_present(
                record.get("content_id"),
                record.get("video_id"),
            ),
            title=record.get("title"),
            comment_id=record.get("comment_id"),
            author=record.get("author"),
            published_at=record.get("published_at"),
            comment=record.get("comment"),
            category=record.get("category"),
            query_type=query_type,
            keyword=record.get("keyword"),
        )


def adapt_youtube_keywords(
    spec: SourceSpec,
) -> Iterator[dict[str, str | None]]:
    required = {
        "platform",
        "category",
        "query_type",
        "keyword",
        "video_id",
        "title",
        "comment_id",
        "author",
        "published_at",
        "comment",
    }
    for number, record in iter_csv_rows(spec, required):
        yield build_row(
            spec,
            f"row[{number}]",
            record,
            record_type="comment",
            content_id=first_present(
                record.get("content_id"),
                record.get("video_id"),
            ),
            title=record.get("title"),
            comment_id=record.get("comment_id"),
            author=record.get("author"),
            published_at=record.get("published_at"),
            comment=record.get("comment"),
            category=record.get("category"),
            query_type=record.get("query_type"),
            keyword=record.get("keyword"),
        )


def adapt_youtube_links(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    required = {
        "video_id",
        "video_url",
        "title",
        "channel_title",
        "comment_id",
        "parent_id",
        "is_reply",
        "comment",
        "like_count",
        "published_at",
        "updated_at",
    }
    for number, record in iter_csv_rows(spec, required):
        reply = is_truthy(record.get("is_reply"))
        yield build_row(
            spec,
            f"row[{number}]",
            record,
            record_type="reply" if reply else "comment",
            content_id=record.get("video_id"),
            content_url=record.get("video_url"),
            title=record.get("title"),
            comment_id=record.get("comment_id"),
            parent_id=record.get("parent_id"),
            is_reply=record.get("is_reply"),
            published_at=record.get("published_at"),
            updated_at=record.get("updated_at"),
            comment=record.get("comment"),
            like_count=record.get("like_count"),
            channel_title=record.get("channel_title"),
        )


def adapt_voz_csv(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    required = {
        "title",
        "thread_url",
        "post_id",
        "username",
        "datetime",
        "comment",
        "page",
    }
    seen_threads: set[str] = set()
    for number, record in iter_csv_rows(spec, required):
        thread_url = str(record.get("thread_url") or "")
        record_type = "post" if thread_url not in seen_threads else "comment"
        seen_threads.add(thread_url)
        yield build_row(
            spec,
            f"row[{number}]",
            record,
            record_type=record_type,
            content_id=thread_url,
            content_url=thread_url,
            title=record.get("title"),
            comment_id=record.get("post_id"),
            author=record.get("username"),
            published_at=record.get("datetime"),
            comment=record.get("comment"),
            page=record.get("page"),
        )


def ensure_dict(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MergeError(f"{context} phai la JSON object.")
    return value


def ensure_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise MergeError(f"{context} phai la JSON array.")
    return value


def map_nested_comment(
    spec: SourceSpec,
    source_record_path: str,
    comment_record: Any,
    *,
    content_id: Any,
    content_url: Any,
    title: Any,
    record_type: str,
) -> dict[str, str | None]:
    comment = ensure_dict(comment_record, source_record_path)
    return build_row(
        spec,
        source_record_path,
        comment,
        record_type=record_type,
        content_id=content_id,
        content_url=content_url,
        title=title,
        comment_id=comment.get("post_id"),
        parent_id=first_present(
            comment.get("parent_id"),
            comment.get("repliesToId"),
        ),
        is_reply=comment.get("is_reply"),
        author=first_present(comment.get("username"), comment.get("author")),
        published_at=first_present(
            comment.get("datetime"),
            comment.get("published_at"),
        ),
        updated_at=comment.get("updated_at"),
        comment=first_present(comment.get("comment"), comment.get("text")),
        like_count=first_present(
            comment.get("like_count"),
            comment.get("diggCount"),
        ),
        page=comment.get("page"),
        post_number=comment.get("post_number"),
    )


def adapt_facebook_group(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    root = ensure_dict(load_json(spec.path), spec.relative_path)
    threads = ensure_list(
        root.get("facebook_threads"),
        f"{spec.relative_path}.facebook_threads",
    )
    for thread_index, thread_value in enumerate(threads):
        thread_path = f"facebook_threads[{thread_index}]"
        thread = ensure_dict(thread_value, thread_path)
        url = thread.get("url")
        title = thread.get("title")
        comments = ensure_list(
            thread.get("comments"),
            f"{thread_path}.comments",
        )
        for comment_index, comment in enumerate(comments):
            path = f"{thread_path}.comments[{comment_index}]"
            yield map_nested_comment(
                spec,
                path,
                comment,
                content_id=url,
                content_url=url,
                title=title,
                record_type="post" if comment_index == 0 else "comment",
            )


def adapt_facebook_single(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    posts = ensure_list(load_json(spec.path), spec.relative_path)
    for post_index, post_value in enumerate(posts):
        post_path = f"[{post_index}]"
        post = ensure_dict(post_value, post_path)
        url = post.get("url")
        title = post.get("title")
        comments = ensure_list(post.get("comments"), f"{post_path}.comments")
        for comment_index, comment in enumerate(comments):
            path = f"{post_path}.comments[{comment_index}]"
            yield map_nested_comment(
                spec,
                path,
                comment,
                content_id=url,
                content_url=url,
                title=title,
                record_type="post" if comment_index == 0 else "comment",
            )


def adapt_facebook_page(spec: SourceSpec) -> Iterator[dict[str, str | None]]:
    posts = ensure_list(load_json(spec.path), spec.relative_path)
    for post_index, post_value in enumerate(posts):
        post_path = f"[{post_index}]"
        post = ensure_dict(post_value, post_path)
        content_id = first_present(post.get("id"), post.get("url"))
        url = post.get("url")
        title = post.get("title")
        yield build_row(
            spec,
            post_path,
            post,
            record_type="post",
            content_id=content_id,
            content_url=url,
            title=title,
            author=post.get("username"),
            published_at=post.get("datetime"),
            comment=first_present(post.get("text"), title),
        )
        comments = ensure_list(post.get("comments"), f"{post_path}.comments")
        for comment_index, comment in enumerate(comments):
            path = f"{post_path}.comments[{comment_index}]"
            yield map_nested_comment(
                spec,
                path,
                comment,
                content_id=content_id,
                content_url=url,
                title=title,
                record_type="comment",
            )


ADAPTERS = {
    "facebook_group_json": adapt_facebook_group,
    "facebook_page_json": adapt_facebook_page,
    "facebook_single_json": adapt_facebook_single,
    "thread_city_csv": adapt_threads,
    "tiktok_csv": adapt_tiktok,
    "voz_csv": adapt_voz_csv,
    "youtube_keywords_csv": adapt_youtube_keywords,
    "youtube_links_csv": adapt_youtube_links,
}


def load_source_specs(config_path: Path, crawler_data: Path) -> list[SourceSpec]:
    config = ensure_dict(load_json(config_path), str(config_path))
    if config.get("version") != 1:
        raise MergeError("sources.json phai co version=1.")
    source_values = ensure_list(config.get("sources"), "sources.json.sources")
    root = crawler_data.resolve()
    specs: list[SourceSpec] = []
    names: set[str] = set()
    relative_paths: set[str] = set()

    for index, value in enumerate(source_values):
        item = ensure_dict(value, f"sources[{index}]")
        name = str(item.get("name") or "").strip()
        platform = str(item.get("platform") or "").strip()
        adapter = str(item.get("adapter") or "").strip()
        relative_path = str(item.get("path") or "").strip().replace("\\", "/")
        if not all((name, platform, adapter, relative_path)):
            raise MergeError(
                f"sources[{index}] phai co name, platform, adapter va path."
            )
        if name in names:
            raise MergeError(f"Trung source name: {name}")
        if relative_path in relative_paths:
            raise MergeError(f"Trung source path: {relative_path}")
        if adapter not in ADAPTERS:
            raise MergeError(f"Adapter khong ho tro: {adapter}")

        path = (root / Path(relative_path)).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise MergeError(
                f"Source nam ngoai Crawler/data: {relative_path}"
            ) from exc
        if not path.is_file():
            raise MergeError(f"Khong tim thay source: {path}")
        names.add(name)
        relative_paths.add(relative_path)
        specs.append(
            SourceSpec(
                name=name,
                platform=platform,
                adapter=adapter,
                relative_path=relative_path,
                path=path,
            )
        )
    if not specs:
        raise MergeError("sources.json khong co source.")
    return specs


def snapshot_sources(specs: Iterable[SourceSpec]) -> list[SourceSnapshot]:
    snapshots: list[SourceSnapshot] = []
    for spec in specs:
        try:
            stat = spec.path.stat()
        except OSError as exc:
            raise MergeError(f"Khong stat duoc {spec.path}: {exc}") from exc
        snapshots.append(
            SourceSnapshot(
                path=spec.path,
                size=stat.st_size,
                modified_ns=stat.st_mtime_ns,
            )
        )
    return snapshots


def verify_snapshots(snapshots: Iterable[SourceSnapshot]) -> None:
    changed: list[str] = []
    for snapshot in snapshots:
        try:
            stat = snapshot.path.stat()
        except OSError:
            changed.append(str(snapshot.path))
            continue
        if (
            stat.st_size != snapshot.size
            or stat.st_mtime_ns != snapshot.modified_ns
        ):
            changed.append(str(snapshot.path))
    if changed:
        raise MergeError(
            "Source thay doi trong luc merge; khong publish output:\n- "
            + "\n- ".join(changed)
        )


def iter_rows(specs: Iterable[SourceSpec]) -> Iterator[dict[str, str | None]]:
    for spec in specs:
        adapter = ADAPTERS[spec.adapter]
        yield from adapter(spec)


def write_temp_outputs(
    specs: list[SourceSpec],
    csv_temp: Path,
    json_temp: Path,
) -> tuple[int, dict[str, int]]:
    source_counts: Counter[str] = Counter()
    row_ids: set[str] = set()
    total = 0
    try:
        with (
            csv_temp.open("w", encoding="utf-8-sig", newline="") as csv_file,
            json_temp.open("w", encoding="utf-8", newline="\n") as json_file,
        ):
            writer = csv.DictWriter(csv_file, fieldnames=RAW_COLUMNS)
            writer.writeheader()
            json_file.write("[")
            first = True
            for row in iter_rows(specs):
                source_row_id = str(row["row_id"])
                if source_row_id in row_ids:
                    raise MergeError(f"Trung source record: {source_row_id}")
                row_ids.add(source_row_id)
                total += 1
                output_row: dict[str, str | int | None] = {
                    "row_id": total,
                    "platform": row["platform"],
                    "title": row["title"],
                    "comment": row["comment"],
                }
                writer.writerow(output_row)
                if not first:
                    json_file.write(",")
                json.dump(
                    output_row,
                    json_file,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                first = False
                source_counts[str(row["source_name"])] += 1
            json_file.write("]\n")
            csv_file.flush()
            json_file.flush()
            os.fsync(csv_file.fileno())
            os.fsync(json_file.fileno())
    except (OSError, csv.Error) as exc:
        raise MergeError(f"Khong ghi duoc output tam: {exc}") from exc
    return total, dict(source_counts)


def validate_temp_outputs(
    csv_temp: Path,
    json_temp: Path,
    expected_rows: int,
) -> None:
    try:
        with json_temp.open("r", encoding="utf-8") as file:
            json_rows = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise MergeError(f"raw.json tam khong hop le: {exc}") from exc
    if not isinstance(json_rows, list):
        raise MergeError("raw.json tam khong phai JSON array.")
    if len(json_rows) != expected_rows:
        raise MergeError(
            f"raw.json co {len(json_rows)} dong, can {expected_rows}."
        )

    try:
        with csv_temp.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != RAW_COLUMNS:
                raise MergeError("raw.csv tam sai header.")
            csv_count = 0
            for csv_count, (csv_row, json_row) in enumerate(
                zip(reader, json_rows, strict=True),
                start=1,
            ):
                if not isinstance(json_row, dict):
                    raise MergeError(
                        f"raw.json dong {csv_count} khong phai object."
                    )
                for column in RAW_COLUMNS:
                    expected = json_row.get(column)
                    expected_csv = "" if expected is None else str(expected)
                    if csv_row.get(column) != expected_csv:
                        raise MergeError(
                            f"CSV/JSON lech tai dong {csv_count}, cot {column}."
                        )
    except ValueError as exc:
        raise MergeError("CSV/JSON khac so dong.") from exc
    except (OSError, csv.Error) as exc:
        raise MergeError(f"Khong validate duoc raw.csv tam: {exc}") from exc
    if csv_count != expected_rows:
        raise MergeError(f"raw.csv co {csv_count} dong, can {expected_rows}.")


def publish_pair(
    csv_temp: Path,
    json_temp: Path,
    csv_path: Path,
    json_path: Path,
    token: str,
) -> None:
    csv_backup = csv_path.with_name(f".{csv_path.name}.{token}.previous")
    json_backup = json_path.with_name(f".{json_path.name}.{token}.previous")
    backups = [(csv_path, csv_backup), (json_path, json_backup)]
    installed: list[Path] = []
    published = False
    try:
        for destination, backup in backups:
            if destination.exists():
                os.replace(destination, backup)
        os.replace(csv_temp, csv_path)
        installed.append(csv_path)
        os.replace(json_temp, json_path)
        installed.append(json_path)
        published = True
    except OSError as exc:
        for destination in installed:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
        for destination, backup in backups:
            if backup.exists():
                try:
                    os.replace(backup, destination)
                except OSError:
                    pass
        raise MergeError(f"Khong publish duoc cap output: {exc}") from exc
    finally:
        if published:
            for _, backup in backups:
                try:
                    backup.unlink(missing_ok=True)
                except OSError:
                    pass


def merge_raw(
    crawler_data: Path,
    output_dir: Path,
    sources_config: Path,
) -> MergeResult:
    specs = load_source_specs(sources_config.resolve(), crawler_data.resolve())
    snapshots = snapshot_sources(specs)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    csv_path = output_dir / "raw.csv"
    json_path = output_dir / "raw.json"
    csv_temp = output_dir / f".raw.csv.{token}.tmp"
    json_temp = output_dir / f".raw.json.{token}.tmp"

    try:
        total, source_counts = write_temp_outputs(specs, csv_temp, json_temp)
        verify_snapshots(snapshots)
        validate_temp_outputs(csv_temp, json_temp, total)
        verify_snapshots(snapshots)
        publish_pair(csv_temp, json_temp, csv_path, json_path, token)
    finally:
        for temp in (csv_temp, json_temp):
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
    return MergeResult(
        total_rows=total,
        source_counts=source_counts,
        csv_path=csv_path,
        json_path=json_path,
    )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    try:
        result = merge_raw(
            crawler_data=args.crawler_data,
            output_dir=args.output_dir,
            sources_config=args.sources_config,
        )
    except MergeError as exc:
        print(f"MERGE THAT BAI: {exc}", file=sys.stderr)
        return 2

    print("So dong theo nguon:")
    for name, count in result.source_counts.items():
        print(f"- {name}: {count}")
    print(f"HOAN THANH: {result.total_rows} dong")
    print(f"CSV: {result.csv_path}")
    print(f"JSON: {result.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
