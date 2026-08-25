"""Capture comments from a TikTok LIVE stream with TikTokLive.

The crawler accepts either a creator username or a TikTok LIVE URL and appends
each received comment immediately to the project's canonical TikTok CSV.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from comment_crawler.paths import TIKTOK_COMMENTS_CSV
from comment_crawler.storage import append_comment_rows, prepare_comment_csv

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]+$")


class TikTokLiveCrawlerError(RuntimeError):
    """Expected crawler failure with a concise user-facing message."""


def parse_creator(value: str) -> str:
    """Return a TikTok username without the leading @."""
    raw = value.strip()
    if not raw:
        raise argparse.ArgumentTypeError("Username/link TikTok LIVE khong duoc rong.")

    if "://" in raw:
        parts = urlsplit(raw)
        hostname = (parts.hostname or "").lower()
        if (
            parts.scheme not in {"http", "https"}
            or (hostname != "tiktok.com" and not hostname.endswith(".tiktok.com"))
        ):
            raise argparse.ArgumentTypeError("Link phai thuoc tiktok.com.")
        path_parts = [unquote(part) for part in parts.path.split("/") if part]
        username_part = next(
            (part for part in path_parts if part.startswith("@") and len(part) > 1),
            "",
        )
        if not username_part:
            raise argparse.ArgumentTypeError(
                "Khong tim thay @username trong link. Hay dung link dang "
                "https://www.tiktok.com/@username/live."
            )
        raw = username_part

    username = raw.lstrip("@").strip().rstrip("/")
    if not USERNAME_PATTERN.fullmatch(username):
        raise argparse.ArgumentTypeError(
            "Username TikTok chi duoc gom chu cai, chu so, dau cham va dau gach duoi."
        )
    return username


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Crawl comment dang phat sinh tu TikTok LIVE bang TikTokLive va "
            "ghi noi vao CSV TikTok hien tai."
        )
    )
    parser.add_argument(
        "creator",
        type=parse_creator,
        help="@username, username, hoac link https://www.tiktok.com/@username/live",
    )
    parser.add_argument(
        "--category",
        default="TikTok live",
        help="Gia tri category ghi vao CSV (mac dinh: TikTok live).",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=0,
        help="Dung sau N comment moi; 0 la khong gioi han (mac dinh: 0).",
    )
    parser.add_argument(
        "--duration-minutes",
        type=float,
        default=0,
        help="Dung sau N phut; 0 la chay den khi LIVE ket thuc/Ctrl+C.",
    )
    parser.add_argument("--output", type=Path, default=TIKTOK_COMMENTS_CSV)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Khong in tung comment ra terminal.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kiem tra dau vao, khong ket noi TikTok va khong ghi file.",
    )
    args = parser.parse_args()
    if args.max_comments < 0:
        parser.error("--max-comments khong duoc am.")
    if args.duration_minutes < 0:
        parser.error("--duration-minutes khong duoc am.")
    return args


def nested_value(obj: Any, *paths: str) -> Any:
    """Return the first non-empty value found in dotted attribute paths."""
    for path in paths:
        current = obj
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            if current is None:
                break
        if current not in (None, ""):
            return current
    return None


def iso_timestamp(value: Any, fallback: str) -> str:
    if value in (None, ""):
        return fallback
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric > 10_000_000_000:
        numeric /= 1_000
    try:
        return (
            datetime.fromtimestamp(numeric, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OverflowError, OSError, ValueError):
        return fallback


def stable_comment_id(
    event: Any,
    content_id: str,
    author: str,
    text: str,
    received_ns: int,
) -> str:
    message_id = nested_value(
        event,
        "msg_id",
        "message_id",
        "id",
        "common.msg_id",
        "common.message_id",
    )
    if message_id not in (None, ""):
        return f"live-{message_id}"

    event_time = nested_value(
        event,
        "create_time",
        "timestamp",
        "common.create_time",
    )
    # TikTokLive does not guarantee a public comment ID on every event version.
    # The receive timestamp keeps repeated identical comments as separate rows.
    raw = f"{content_id}|{author}|{text}|{event_time or received_ns}"
    return "live-generated-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def load_tiktok_live() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import (
            CommentEvent,
            ConnectEvent,
            DisconnectEvent,
            LiveEndEvent,
        )
    except ImportError as exc:
        raise TikTokLiveCrawlerError(
            "Chua cai TikTokLive. Chay `python -m pip install -e .` truoc."
        ) from exc
    return (
        TikTokLiveClient,
        ConnectEvent,
        CommentEvent,
        DisconnectEvent,
        LiveEndEvent,
    )


@dataclass
class CaptureState:
    username: str
    output: Path
    category: str
    max_comments: int
    quiet: bool
    seen: set[tuple[str, str]] = field(default_factory=set)
    room_id: str = ""
    saved: int = 0
    duplicates: int = 0
    empty: int = 0
    stopping: bool = False
    stop_reason: str = ""

    @property
    def content_id(self) -> str:
        room_part = self.room_id or f"@{self.username}"
        return f"tiktok-live-{room_part}"


async def capture(args: argparse.Namespace) -> CaptureState:
    (
        TikTokLiveClient,
        ConnectEvent,
        CommentEvent,
        DisconnectEvent,
        LiveEndEvent,
    ) = load_tiktok_live()

    state = CaptureState(
        username=args.creator,
        output=args.output.resolve(),
        category=args.category,
        max_comments=args.max_comments,
        quiet=args.quiet,
        seen=prepare_comment_csv(args.output),
    )
    client = TikTokLiveClient(unique_id=f"@{args.creator}")
    disconnect_task: asyncio.Task[Any] | None = None

    async def disconnect_safely() -> None:
        try:
            await client.disconnect()
        except Exception:
            # A disconnect event or LIVE end may have closed the client first.
            pass

    def request_stop(reason: str) -> None:
        nonlocal disconnect_task
        if state.stopping:
            return
        state.stopping = True
        state.stop_reason = reason
        print(f"Dang dung: {reason}")
        disconnect_task = asyncio.create_task(disconnect_safely())

    async def on_connect(event: Any) -> None:
        state.room_id = str(getattr(client, "room_id", "") or "")
        print(
            f"Da ket noi TikTok LIVE @{state.username}"
            + (f" (room_id={state.room_id})" if state.room_id else "")
        )

    async def on_comment(event: Any) -> None:
        if state.stopping:
            return
        text = str(getattr(event, "comment", "") or "")
        if not text.strip():
            state.empty += 1
            return

        received_ns = time.time_ns()
        received_at = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        author = str(
            nested_value(
                event,
                "user.display_id",
                "user.unique_id",
                "user.nickname",
                "user.id",
                "user.user_id",
            )
            or ""
        )
        published_at = iso_timestamp(
            nested_value(
                event,
                "create_time",
                "timestamp",
                "common.create_time",
            ),
            received_at,
        )
        content_id = state.content_id
        comment_id = stable_comment_id(
            event,
            content_id,
            author,
            text,
            received_ns,
        )
        key = (content_id, comment_id)
        if key in state.seen:
            state.duplicates += 1
            return

        row = {
            "platform": "tiktok",
            "category": state.category,
            "query_type": "tiktok_live_comment",
            "keyword": f"https://www.tiktok.com/@{state.username}/live",
            "content_id": content_id,
            "video_id": content_id,
            "title": f"TikTok LIVE @{state.username}",
            "comment_id": comment_id,
            "author": author,
            "published_at": published_at,
            "comment": text,
        }
        append_comment_rows(state.output, [row])
        state.seen.add(key)
        state.saved += 1

        if not state.quiet:
            preview = " ".join(text.split())
            if len(preview) > 120:
                preview = preview[:117] + "..."
            print(f"[{state.saved}] {author or '(khong ro)'}: {preview}")

        if state.max_comments and state.saved >= state.max_comments:
            request_stop(f"da dat --max-comments {state.max_comments}")

    async def on_live_end(event: Any) -> None:
        request_stop("LIVE da ket thuc")

    async def on_disconnect(event: Any) -> None:
        if not state.stop_reason:
            state.stop_reason = "mat ket noi hoac server dong ket noi"

    client.add_listener(ConnectEvent, on_connect)
    client.add_listener(CommentEvent, on_comment)
    client.add_listener(LiveEndEvent, on_live_end)
    client.add_listener(DisconnectEvent, on_disconnect)

    async def duration_timer() -> None:
        await asyncio.sleep(args.duration_minutes * 60)
        request_stop(f"da chay {args.duration_minutes:g} phut")

    timer_task: asyncio.Task[Any] | None = None
    if args.duration_minutes:
        timer_task = asyncio.create_task(duration_timer())

    try:
        await client.connect()
    finally:
        if timer_task is not None:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass
        if disconnect_task is not None:
            await disconnect_task
        elif not state.stopping:
            await disconnect_safely()
    return state


def main() -> int:
    args = parse_args()
    live_url = f"https://www.tiktok.com/@{args.creator}/live"
    print(f"Nguon: {live_url}")
    print(f"Output: {args.output.resolve()}")
    if args.dry_run:
        print(
            "DRY RUN: dau vao hop le; khong ket noi TikTok va khong ghi du lieu."
        )
        return 0

    try:
        state = asyncio.run(capture(args))
    except KeyboardInterrupt:
        print("\nDa dung bang Ctrl+C. Cac comment da crawl van duoc luu.")
        return 130
    except TikTokLiveCrawlerError as exc:
        print(f"LOI: {exc}")
        return 2
    except Exception as exc:
        print(
            "LOI ket noi TikTok LIVE. Kiem tra username, kenh dang LIVE, "
            f"mang va phien ban TikTokLive.\nChi tiet: {exc}"
        )
        return 1

    print(
        "HOAN THANH: "
        f"{state.saved} comment moi, {state.duplicates} trung, "
        f"{state.empty} rong. Ly do dung: {state.stop_reason or 'ket noi ket thuc'}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
