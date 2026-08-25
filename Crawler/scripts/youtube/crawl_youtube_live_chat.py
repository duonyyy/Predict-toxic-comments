#!/usr/bin/env python3
"""Capture public chat messages while a YouTube livestream is active."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from comment_crawler.paths import YOUTUBE_COMMENTS_CSV
from comment_crawler.storage import append_comment_rows, prepare_comment_csv

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
TERMINAL_CHAT_REASONS = {"liveChatEnded", "liveChatNotFound"}


class LiveChatError(RuntimeError):
    """Expected crawler failure with a concise user-facing message."""


@dataclass(frozen=True)
class VideoLiveDetails:
    video_id: str
    title: str
    channel_title: str
    live_chat_id: str
    scheduled_start: str
    actual_start: str
    actual_end: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Crawl chat cong khai truc tiep tu mot livestream YouTube dang phat "
            "va ghi noi vao CSV YouTube hien tai."
        )
    )
    parser.add_argument("video", help="Link livestream YouTube hoac video ID.")
    parser.add_argument(
        "--api-key",
        default=os.getenv("YOUTUBE_API_KEY"),
        help="Mac dinh doc tu bien moi truong YOUTUBE_API_KEY.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=YOUTUBE_COMMENTS_CSV,
        help="CSV output; mac dinh data/youtube/youtube_comments_keywords.csv.",
    )
    parser.add_argument(
        "--category",
        default="YouTube live",
        help="Gia tri category ghi vao CSV.",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=0,
        help="So chat moi toi da; 0 la chay den khi live ket thuc/Ctrl+C.",
    )
    parser.add_argument(
        "--duration-minutes",
        type=float,
        default=0,
        help="So phut toi da theo doi; 0 la khong gioi han.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=2_000,
        help="So message toi da moi API response, trong khoang 200..2000.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=30,
        help="HTTP timeout giay cho moi API request (mac dinh: 30).",
    )
    parser.add_argument(
        "--include-events",
        action="store_true",
        help="Luu ca su kien he thong khong co noi dung chat hien thi.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Khong in tung message ra terminal.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chi kiem tra tham so va video ID; khong goi YouTube API.",
    )
    args = parser.parse_args()
    if args.max_messages < 0:
        parser.error("--max-messages khong duoc am.")
    if args.duration_minutes < 0:
        parser.error("--duration-minutes khong duoc am.")
    if not 200 <= args.max_results <= 2_000:
        parser.error("--max-results phai nam trong 200..2000.")
    if args.request_timeout < 10:
        parser.error("--request-timeout phai tu 10 giay.")
    try:
        args.video_id = extract_video_id(args.video)
    except ValueError as exc:
        parser.error(str(exc))
    return args


def extract_video_id(value: str) -> str:
    candidate = value.strip()
    if VIDEO_ID_PATTERN.fullmatch(candidate):
        return candidate
    parts = urlsplit(candidate)
    hostname = (parts.hostname or "").lower()
    path_parts = [part for part in parts.path.split("/") if part]
    video_id = ""
    if hostname in {"youtu.be", "www.youtu.be"} and path_parts:
        video_id = path_parts[0]
    elif hostname == "youtube.com" or hostname.endswith(".youtube.com"):
        if parts.path.rstrip("/") == "/watch":
            video_id = (parse_qs(parts.query).get("v") or [""])[0]
        elif path_parts and path_parts[0] in {"live", "shorts", "embed"}:
            video_id = path_parts[1] if len(path_parts) > 1 else ""
    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValueError(
            "Khong nhan dien duoc video ID. Dung link watch, live, youtu.be "
            "hoac video ID 11 ky tu."
        )
    return video_id


def requests_module() -> Any:
    try:
        import requests
    except ImportError as exc:
        raise LiveChatError("Chay `python -m pip install -e .` truoc.") from exc
    return requests


def parse_api_error(response: Any, context: str) -> LiveChatError:
    reason = ""
    message = response.reason
    try:
        body = response.json()
        error = body.get("error", {}) if isinstance(body, dict) else {}
        message = str(error.get("message") or message)
        errors = error.get("errors")
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            reason = str(errors[0].get("reason") or "")
    except ValueError:
        pass
    error = LiveChatError(
        f"{context} tra HTTP {response.status_code}"
        + (f" ({reason})" if reason else "")
        + f": {message}"
    )
    error.reason = reason  # type: ignore[attr-defined]
    return error


def youtube_get(
    endpoint: str,
    *,
    api_key: str,
    params: dict[str, Any],
    timeout: int,
    context: str,
) -> dict[str, Any]:
    requests = requests_module()
    request_params = dict(params)
    request_params["key"] = api_key
    try:
        response = requests.get(
            f"{YOUTUBE_API_BASE}/{endpoint}",
            params=request_params,
            timeout=(10, timeout),
        )
    except requests.RequestException as exc:
        raise LiveChatError(f"{context} khong ket noi duoc YouTube: {exc}") from exc
    if response.status_code >= 400:
        raise parse_api_error(response, context)
    try:
        body = response.json()
    except ValueError as exc:
        raise LiveChatError(f"{context} khong tra JSON hop le.") from exc
    if not isinstance(body, dict):
        raise LiveChatError(f"{context} khong tra JSON object.")
    return body


def fetch_live_details(
    video_id: str,
    api_key: str,
    request_timeout: int,
) -> VideoLiveDetails:
    body = youtube_get(
        "videos",
        api_key=api_key,
        params={
            "part": "snippet,liveStreamingDetails",
            "id": video_id,
        },
        timeout=request_timeout,
        context="videos.list",
    )
    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise LiveChatError(
            f"Khong tim thay video {video_id}, hoac API key khong duoc phep xem."
        )
    item = items[0] if isinstance(items[0], dict) else {}
    snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
    live = (
        item.get("liveStreamingDetails")
        if isinstance(item.get("liveStreamingDetails"), dict)
        else {}
    )
    return VideoLiveDetails(
        video_id=video_id,
        title=str(snippet.get("title") or ""),
        channel_title=str(snippet.get("channelTitle") or ""),
        live_chat_id=str(live.get("activeLiveChatId") or ""),
        scheduled_start=str(live.get("scheduledStartTime") or ""),
        actual_start=str(live.get("actualStartTime") or ""),
        actual_end=str(live.get("actualEndTime") or ""),
    )


def explain_missing_live_chat(details: VideoLiveDetails) -> str:
    if details.actual_end:
        return (
            "Livestream da ket thuc; activeLiveChatId da bi go bo va API khong "
            "cho crawl live chat replay bang luong nay."
        )
    if details.scheduled_start and not details.actual_start:
        return (
            f"Livestream chua bat dau (scheduledStartTime="
            f"{details.scheduled_start})."
        )
    if details.actual_start:
        return "Livestream dang/da phat nhung live chat khong bat hoac khong cong khai."
    return "Video khong phai livestream dang hoat dong co live chat cong khai."


def message_text(item: dict[str, Any], include_events: bool) -> str:
    snippet = item.get("snippet")
    if not isinstance(snippet, dict):
        return ""
    display = snippet.get("displayMessage")
    if display is not None and str(display) != "":
        return str(display)
    details = snippet.get("textMessageDetails")
    if isinstance(details, dict) and details.get("messageText") is not None:
        return str(details.get("messageText"))
    details = snippet.get("superChatDetails")
    if isinstance(details, dict) and details.get("userComment") is not None:
        comment = str(details.get("userComment"))
        if comment:
            return comment
    details = snippet.get("memberMilestoneChatDetails")
    if isinstance(details, dict) and details.get("userComment") is not None:
        comment = str(details.get("userComment"))
        if comment:
            return comment
    if not include_events:
        return ""
    message_type = str(snippet.get("type") or "unknownEvent")
    return f"[YouTube live event: {message_type}]"


def normalize_messages(
    items: Any,
    *,
    details: VideoLiveDetails,
    source_url: str,
    category: str,
    include_events: bool,
    seen: set[tuple[str, str]],
    remaining: int | None,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows: list[dict[str, str]] = []
    stats = {"items": 0, "duplicates": 0, "without_text": 0, "kept": 0}
    if not isinstance(items, list):
        raise LiveChatError("liveChatMessages.list tra items khong hop le.")
    for item in items:
        if remaining is not None and len(rows) >= remaining:
            break
        if not isinstance(item, dict):
            continue
        stats["items"] += 1
        message_id = str(item.get("id") or "")
        snippet = item.get("snippet")
        author_details = item.get("authorDetails")
        if not isinstance(snippet, dict):
            snippet = {}
        if not isinstance(author_details, dict):
            author_details = {}
        if not message_id:
            stats["without_text"] += 1
            continue
        key = (details.video_id, message_id)
        if key in seen:
            stats["duplicates"] += 1
            continue
        text = message_text(item, include_events)
        if not text:
            stats["without_text"] += 1
            seen.add(key)
            continue
        message_type = str(snippet.get("type") or "unknown")
        rows.append(
            {
                "platform": "youtube",
                "category": category,
                "query_type": f"live_chat_{message_type}",
                "keyword": source_url,
                "content_id": details.video_id,
                "video_id": details.video_id,
                "title": details.title,
                "comment_id": message_id,
                "author": str(author_details.get("displayName") or ""),
                "published_at": str(snippet.get("publishedAt") or ""),
                "comment": text,
            }
        )
        seen.add(key)
        stats["kept"] += 1
    return rows, stats


def print_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        published = row["published_at"]
        author = row["author"] or "(khong ro)"
        text = row["comment"].replace("\r", " ").replace("\n", " ")
        print(f"[{published}] {author}: {text}")


def crawl_live_chat(args: argparse.Namespace) -> int:
    details = fetch_live_details(
        args.video_id,
        args.api_key,
        args.request_timeout,
    )
    if not details.live_chat_id:
        raise LiveChatError(explain_missing_live_chat(details))

    source_url = f"https://www.youtube.com/watch?v={details.video_id}"
    seen = prepare_comment_csv(args.output)
    page_token: str | None = None
    started = time.monotonic()
    total_new = 0
    total_items = 0
    total_duplicates = 0
    poll_number = 0

    print(f"Video: {details.title}")
    print(f"Kenh: {details.channel_title}")
    print(f"Video ID: {details.video_id}")
    print(f"Live chat ID: {details.live_chat_id}")
    print(f"Output: {args.output}")
    print("Dang theo doi live chat. Nhan Ctrl+C de dung an toan.")

    while True:
        if args.max_messages and total_new >= args.max_messages:
            print(f"Dat --max-messages={args.max_messages}, dung.")
            break
        if (
            args.duration_minutes
            and time.monotonic() - started >= args.duration_minutes * 60
        ):
            print(f"Dat --duration-minutes={args.duration_minutes:g}, dung.")
            break

        params: dict[str, Any] = {
            "part": "id,snippet,authorDetails",
            "liveChatId": details.live_chat_id,
            "maxResults": args.max_results,
            "hl": "vi",
        }
        if page_token:
            params["pageToken"] = page_token
        try:
            body = youtube_get(
                "liveChat/messages",
                api_key=args.api_key,
                params=params,
                timeout=args.request_timeout,
                context="liveChatMessages.list",
            )
        except LiveChatError as exc:
            reason = str(getattr(exc, "reason", ""))
            if reason in TERMINAL_CHAT_REASONS:
                print(f"Live chat da ket thuc ({reason}).")
                break
            raise

        remaining = (
            args.max_messages - total_new if args.max_messages else None
        )
        rows, stats = normalize_messages(
            body.get("items"),
            details=details,
            source_url=source_url,
            category=args.category,
            include_events=args.include_events,
            seen=seen,
            remaining=remaining,
        )
        append_comment_rows(args.output, rows)
        if rows and not args.quiet:
            print_rows(rows)
        total_new += len(rows)
        total_items += stats["items"]
        total_duplicates += stats["duplicates"]
        poll_number += 1
        print(
            f"Poll {poll_number}: API items={stats['items']}, "
            f"moi={len(rows)}, trung={stats['duplicates']}, "
            f"tong moi={total_new}"
        )

        page_token = str(body.get("nextPageToken") or "") or page_token
        if body.get("offlineAt"):
            print(f"Livestream offline luc {body['offlineAt']}, dung.")
            break
        if args.max_messages and total_new >= args.max_messages:
            continue

        polling_ms = body.get("pollingIntervalMillis")
        try:
            wait_seconds = max(1.0, float(polling_ms) / 1000)
        except (TypeError, ValueError):
            wait_seconds = 5.0
        if args.duration_minutes:
            remaining_seconds = args.duration_minutes * 60 - (
                time.monotonic() - started
            )
            if remaining_seconds <= 0:
                continue
            wait_seconds = min(wait_seconds, remaining_seconds)
        time.sleep(wait_seconds)

    print(
        f"HOAN THANH: da doc {total_items} API item, "
        f"them {total_new} chat moi, gap {total_duplicates} dong trung."
    )
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    if args.dry_run:
        print("Dry run: khong goi YouTube API.")
        print(f"Video ID: {args.video_id}")
        print(f"Output: {args.output}")
        return 0
    if not args.api_key:
        print(
            "Thieu API key. Dat YOUTUBE_API_KEY hoac dung --api-key.",
            file=sys.stderr,
        )
        return 1
    try:
        return crawl_live_chat(args)
    except KeyboardInterrupt:
        print("\nDa dung bang Ctrl+C. Cac chat da ghi van duoc giu.")
        return 130
    except (LiveChatError, OSError, RuntimeError) as exc:
        print(f"Dung crawl YouTube live chat: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
