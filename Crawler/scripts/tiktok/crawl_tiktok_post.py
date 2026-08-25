"""Crawl all accessible comments from one TikTok post via Apify.

The Actor is started asynchronously so long runs do not hold one HTTP request
open. Results are fetched page by page and appended to the canonical TikTok CSV.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit, urlunsplit

from comment_crawler.paths import TIKTOK_COMMENTS_CSV
from comment_crawler.storage import append_comment_rows, prepare_comment_csv

APIFY_API_BASE = "https://api.apify.com/v2"
DEFAULT_ACTOR = "clockworks~tiktok-comments-scraper"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


class TikTokPostError(RuntimeError):
    """Expected crawler failure with a user-facing message."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Crawl toan bo comment co the truy cap tu mot link bai TikTok qua "
            "Apify va ghi noi vao CSV TikTok hien tai."
        )
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Permalink bai TikTok; khong can khi dung --run-id.",
    )
    parser.add_argument(
        "--run-id",
        help="Tiep tuc doi/lay ket qua cua Apify run da tao, khong tao run moi.",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=100_000,
        help=(
            "Gioi han comment + reply Actor duoc yeu cau cho bai "
            "(mac dinh: 100000)."
        ),
    )
    parser.add_argument(
        "--max-replies-per-comment",
        type=int,
        default=1_000,
        help="So reply toi da cho moi comment cap cao nhat (mac dinh: 1000).",
    )
    parser.add_argument(
        "--category",
        default="TikTok direct post",
        help="Gia tri category ghi vao CSV.",
    )
    parser.add_argument("--output", type=Path, default=TIKTOK_COMMENTS_CSV)
    parser.add_argument(
        "--actor",
        default=DEFAULT_ACTOR,
        help="Apify Actor ID dung de lay comment.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=10.0,
        help="So giay giua hai lan kiem tra trang thai run (mac dinh: 10).",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=7_200,
        help="Tong so giay toi da doi Actor; 0 la khong gioi han.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=60,
        help="HTTP read timeout cho moi API request ngan (mac dinh: 60).",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=1_000,
        help="So dataset item moi lan tai, trong khoang 1..1000.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kiem tra link va hien Actor input, khong goi Apify.",
    )
    args = parser.parse_args()

    if bool(args.url) == bool(args.run_id):
        parser.error("Chi cung cap mot trong hai: URL bai TikTok hoac --run-id.")
    if args.max_comments < 1:
        parser.error("--max-comments phai lon hon 0.")
    if args.max_replies_per_comment < 0:
        parser.error("--max-replies-per-comment khong duoc am.")
    if args.poll_interval < 1:
        parser.error("--poll-interval phai tu 1 giay.")
    if args.wait_timeout < 0:
        parser.error("--wait-timeout khong duoc am.")
    if args.request_timeout < 10:
        parser.error("--request-timeout phai tu 10 giay.")
    if not 1 <= args.page_size <= 1_000:
        parser.error("--page-size phai nam trong 1..1000.")
    if args.url:
        args.url = validate_tiktok_url(args.url)
    if args.dry_run and args.run_id:
        parser.error("--dry-run chi dung khi tao run tu URL.")
    return args


def validate_tiktok_url(value: str) -> str:
    url = value.strip()
    parts = urlsplit(url)
    hostname = (parts.hostname or "").lower()
    if (
        parts.scheme not in {"http", "https"}
        or not hostname
        or (hostname != "tiktok.com" and not hostname.endswith(".tiktok.com"))
    ):
        raise argparse.ArgumentTypeError(
            "URL phai la link http(s) thuoc tiktok.com."
        )
    return url


def normalize_video_url(value: str) -> str:
    parts = urlsplit((value or "").strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return ""
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def video_id_from_url(url: str) -> str:
    path_parts = [part for part in urlsplit(url).path.split("/") if part]
    if "video" not in path_parts:
        return ""
    index = path_parts.index("video")
    return path_parts[index + 1] if index + 1 < len(path_parts) else ""


def stable_comment_id(video_id: str, text: str, author: str) -> str:
    raw = f"{video_id}|{author}|{text}".encode("utf-8")
    return "generated-" + hashlib.sha1(raw).hexdigest()[:20]


def actor_input(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "postURLs": [args.url],
        "commentsPerPost": args.max_comments,
        "topLevelCommentsPerPost": args.max_comments,
        "maxRepliesPerComment": args.max_replies_per_comment,
    }


def requests_module() -> Any:
    try:
        import requests
    except ImportError as exc:
        raise TikTokPostError("Chay `python -m pip install -e .` truoc.") from exc
    return requests


def response_json(response: Any, context: str) -> Any:
    if response.status_code >= 400:
        try:
            payload = response.json()
            message = (
                payload.get("error", {}).get("message")
                if isinstance(payload, dict)
                else None
            )
        except ValueError:
            message = None
        raise TikTokPostError(
            f"{context} tra HTTP {response.status_code}: "
            f"{message or response.reason}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise TikTokPostError(f"{context} khong tra JSON hop le.") from exc


def start_actor(
    token: str,
    actor_id: str,
    payload: dict[str, Any],
    request_timeout: int,
) -> dict[str, Any]:
    requests = requests_module()
    url = f"{APIFY_API_BASE}/actors/{actor_id}/runs"
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=(15, request_timeout),
        )
    except requests.RequestException as exc:
        raise TikTokPostError(f"Khong tao duoc Apify run: {exc}") from exc
    body = response_json(response, "Tao Apify run")
    run = body.get("data") if isinstance(body, dict) else None
    if not isinstance(run, dict) or not run.get("id"):
        raise TikTokPostError("Apify khong tra run ID.")
    return run


def get_run(token: str, run_id: str, request_timeout: int) -> dict[str, Any]:
    requests = requests_module()
    try:
        response = requests.get(
            f"{APIFY_API_BASE}/actor-runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=(15, request_timeout),
        )
    except requests.RequestException as exc:
        raise TikTokPostError(f"Khong doc duoc Apify run {run_id}: {exc}") from exc
    body = response_json(response, f"Doc Apify run {run_id}")
    run = body.get("data") if isinstance(body, dict) else None
    if not isinstance(run, dict):
        raise TikTokPostError(f"Apify run {run_id} khong co payload hop le.")
    return run


def wait_for_run(
    token: str,
    run_id: str,
    poll_interval: float,
    wait_timeout: int,
    request_timeout: int,
) -> dict[str, Any]:
    started = time.monotonic()
    previous_status = ""
    while True:
        run = get_run(token, run_id, request_timeout)
        status = str(run.get("status") or "UNKNOWN").upper()
        status_message = str(run.get("statusMessage") or "").strip()
        if status != previous_status:
            suffix = f" - {status_message}" if status_message else ""
            print(f"Apify run {run_id}: {status}{suffix}")
            previous_status = status
        if status in TERMINAL_STATUSES:
            if status != "SUCCEEDED":
                raise TikTokPostError(
                    f"Apify run {run_id} ket thuc voi trang thai {status}: "
                    f"{status_message or 'khong co thong bao'}"
                )
            return run
        if wait_timeout and time.monotonic() - started >= wait_timeout:
            raise TikTokPostError(
                f"Da doi qua {wait_timeout} giay. Run van co the dang chay. "
                f"Chay lai voi --run-id {run_id} de tiep tuc."
            )
        time.sleep(poll_interval)


def fetch_dataset_page(
    token: str,
    dataset_id: str,
    offset: int,
    limit: int,
    request_timeout: int,
) -> list[dict[str, Any]]:
    requests = requests_module()
    try:
        response = requests.get(
            f"{APIFY_API_BASE}/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "offset": offset,
                "limit": limit,
                "clean": "true",
                "desc": "false",
            },
            timeout=(15, request_timeout),
        )
    except requests.RequestException as exc:
        raise TikTokPostError(
            f"Khong tai duoc dataset {dataset_id} tai offset {offset}: {exc}"
        ) from exc
    body = response_json(response, f"Tai dataset {dataset_id}")
    if not isinstance(body, list):
        raise TikTokPostError(f"Dataset {dataset_id} khong tra mot JSON array.")
    return [item for item in body if isinstance(item, dict)]


def item_url(item: dict[str, Any], fallback_url: str) -> str:
    for key in ("videoWebUrl", "submittedVideoUrl", "input"):
        value = item.get(key)
        if isinstance(value, str):
            normalized = normalize_video_url(value)
            if normalized:
                return normalized
    return normalize_video_url(fallback_url)


def nested_comments(
    item: dict[str, Any],
    *,
    fallback_url: str,
) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield one top-level item and any nested replies with their parent ID."""
    yield item, str(item.get("repliesToId") or "")
    parent_id = str(item.get("cid") or "")
    replies = item.get("replies")
    if not isinstance(replies, list):
        return
    inherited_url = item_url(item, fallback_url)
    for reply in replies:
        if not isinstance(reply, dict):
            continue
        enriched = dict(reply)
        if inherited_url and not item_url(enriched, ""):
            enriched["videoWebUrl"] = inherited_url
        yield enriched, str(enriched.get("repliesToId") or parent_id)


def normalize_page(
    items: list[dict[str, Any]],
    *,
    fallback_url: str,
    category: str,
    seen: set[tuple[str, str]],
    run_seen: set[tuple[str, str]],
    title_by_video: dict[str, str],
) -> tuple[list[dict[str, str]], Counter[str]]:
    rows: list[dict[str, str]] = []
    stats: Counter[str] = Counter(dataset_items=len(items))

    for dataset_item in items:
        if dataset_item.get("errorCode"):
            stats["error_items"] += 1
            print(
                f"Bo item loi: {dataset_item.get('errorCode')}: "
                f"{dataset_item.get('error', '')}",
                file=sys.stderr,
            )
            continue
        for item, parent_id in nested_comments(
            dataset_item,
            fallback_url=fallback_url,
        ):
            text_value = item.get("text")
            text = str(text_value) if text_value is not None else ""
            if not text.strip():
                stats["empty_text"] += 1
                continue

            url = item_url(item, fallback_url)
            video_id = (
                video_id_from_url(url)
                or str(item.get("videoId") or item.get("aweme_id") or "")
            )
            if not video_id:
                stats["missing_video_id"] += 1
                continue

            author = str(
                item.get("uniqueId")
                or item.get("author")
                or (
                    item.get("user", {}).get("uniqueId")
                    if isinstance(item.get("user"), dict)
                    else ""
                )
                or ""
            ).strip()
            comment_id = str(item.get("cid") or "").strip()
            if not comment_id:
                comment_id = stable_comment_id(video_id, text, author)
            key = (video_id, comment_id)
            if key in run_seen:
                stats["duplicate_in_dataset"] += 1
                continue
            run_seen.add(key)
            if key in seen:
                stats["already_stored"] += 1
                continue

            title = str(
                item.get("videoTitle")
                or item.get("videoDescription")
                or item.get("title")
                or ""
            ).strip()
            if title:
                title_by_video[video_id] = title
            else:
                title = title_by_video.get(video_id, "")

            is_reply = bool(parent_id)
            rows.append(
                {
                    "platform": "tiktok",
                    "category": category,
                    "query_type": (
                        "apify_post_reply" if is_reply else "apify_post_url"
                    ),
                    "keyword": url or fallback_url,
                    "content_id": video_id,
                    "video_id": video_id,
                    "title": title,
                    "comment_id": comment_id,
                    "author": author,
                    "published_at": str(
                        item.get("createTimeISO") or item.get("createTime") or ""
                    ),
                    "comment": text,
                }
            )
            seen.add(key)
            stats["replies" if is_reply else "top_level_comments"] += 1
            stats["kept"] += 1
    return rows, stats


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        args = parse_args()
    except argparse.ArgumentTypeError as exc:
        print(f"Link TikTok khong hop le: {exc}", file=sys.stderr)
        return 2

    payload = actor_input(args) if args.url else None
    if args.dry_run:
        print("Dry run: khong goi Apify, khong phat sinh chi phi.")
        print(f"Actor: {args.actor}")
        print(f"Input: {payload}")
        print(f"Output: {args.output}")
        return 0

    token = os.getenv("APIFY_TOKEN")
    if not token:
        print(
            "Thieu APIFY_TOKEN. Dat bien moi truong APIFY_TOKEN truoc khi chay.",
            file=sys.stderr,
        )
        return 1

    run_id = str(args.run_id or "")
    fallback_url = str(args.url or "")
    try:
        if not run_id:
            print(
                f"Tao Actor run cho 1 bai, toi da {args.max_comments} "
                f"comment/reply. Actor co the phat sinh chi phi."
            )
            run = start_actor(token, args.actor, payload or {}, args.request_timeout)
            run_id = str(run["id"])
            print(f"Da tao Apify run: {run_id}")
            print(f"Console: https://console.apify.com/storage/runs/{run_id}")

        run = wait_for_run(
            token,
            run_id,
            args.poll_interval,
            args.wait_timeout,
            args.request_timeout,
        )
        dataset_id = str(run.get("defaultDatasetId") or "")
        if not dataset_id:
            raise TikTokPostError(f"Apify run {run_id} khong co defaultDatasetId.")

        seen = prepare_comment_csv(args.output)
        run_seen: set[tuple[str, str]] = set()
        title_by_video: dict[str, str] = {}
        total_stats: Counter[str] = Counter()
        offset = 0

        while True:
            items = fetch_dataset_page(
                token,
                dataset_id,
                offset,
                args.page_size,
                args.request_timeout,
            )
            if not items:
                break
            rows, stats = normalize_page(
                items,
                fallback_url=fallback_url,
                category=args.category,
                seen=seen,
                run_seen=run_seen,
                title_by_video=title_by_video,
            )
            append_comment_rows(args.output, rows)
            total_stats.update(stats)
            offset += len(items)
            print(
                f"Dataset: da doc {offset} item, vua ghi {len(rows)} dong, "
                f"tong moi {total_stats['kept']}."
            )
            if len(items) < args.page_size:
                break

        print(
            "HOAN THANH: "
            + ", ".join(
                f"{name}={value}" for name, value in sorted(total_stats.items())
            )
        )
        print(f"Da ghi noi vao: {args.output}")
        return 0
    except KeyboardInterrupt:
        print(
            f"\nDa dung cho. Apify run co the van dang chay: {run_id or 'chua tao'}",
            file=sys.stderr,
        )
        if run_id:
            print(
                "Tiep tuc ma khong tao run moi:\n"
                f"python -u -X utf8 scripts/tiktok/crawl_tiktok_post.py "
                f"--run-id {run_id}",
                file=sys.stderr,
            )
        return 130
    except (TikTokPostError, OSError, RuntimeError) as exc:
        print(f"Dung crawl TikTok post: {exc}", file=sys.stderr)
        if run_id:
            print(
                f"Co the tiep tuc bang --run-id {run_id} de tranh tao run moi.",
                file=sys.stderr,
            )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
