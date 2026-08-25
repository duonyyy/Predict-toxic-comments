from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import merge_raw


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv(
    path: Path,
    columns: list[str],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class MergeRawTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ds108-preprocessing-")
        self.root = Path(self.temp.name)
        self.crawler_data = self.root / "crawler_data"
        self.output_dir = self.root / "output"
        self.config = self.root / "sources.json"
        self._create_fixtures()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create_fixtures(self) -> None:
        write_json(
            self.crawler_data / "facebook/group.json",
            {
                "facebook_total_threads": 1,
                "facebook_total_comments": 2,
                "facebook_threads": [
                    {
                        "url": "https://facebook.test/groups/g/posts/1",
                        "title": "Group title",
                        "total_comments": 2,
                        "comments": [
                            {
                                "post_id": "gp1",
                                "post_number": 1,
                                "username": "group author",
                                "datetime": "Hôm nay",
                                "comment": "Group post",
                                "page": 1,
                            },
                            {
                                "post_id": "gc1",
                                "post_number": 2,
                                "username": "group commenter",
                                "datetime": None,
                                "comment": "Group comment",
                                "page": 1,
                            },
                        ],
                    }
                ],
            },
        )
        write_json(
            self.crawler_data / "facebook/page.json",
            [
                {
                    "id": 10,
                    "url": "https://facebook.test/page/posts/10",
                    "title": "Page title",
                    "text": "Page post",
                    "username": "page author",
                    "datetime": None,
                    "total_comments": 1,
                    "comments": [
                        {
                            "post_id": "pc1",
                            "post_number": 1,
                            "username": "page commenter",
                            "datetime": "1 giờ",
                            "comment": "Page comment",
                            "page": 1,
                        }
                    ],
                }
            ],
        )
        write_json(
            self.crawler_data / "facebook/single.json",
            [
                {
                    "url": "https://facebook.test/single/posts/20",
                    "title": "Single title",
                    "total_comments": 2,
                    "comments": [
                        {
                            "post_id": "sp1",
                            "post_number": 1,
                            "username": "single author",
                            "datetime": "2026",
                            "comment": "Single post",
                            "page": 1,
                        },
                        {
                            "post_id": "sc1",
                            "post_number": 2,
                            "username": "single commenter",
                            "datetime": "2026",
                            "comment": "Single comment",
                            "page": 1,
                        },
                    ],
                }
            ],
        )
        write_csv(
            self.crawler_data / "threads/comments.csv",
            ["row_id", "platform", "title", "comment"],
            [
                {
                    "row_id": "1",
                    "platform": "threads",
                    "title": "Threads title",
                    "comment": "Threads comment",
                }
            ],
        )
        canonical_columns = [
            "platform",
            "category",
            "query_type",
            "keyword",
            "content_id",
            "video_id",
            "title",
            "comment_id",
            "author",
            "published_at",
            "comment",
        ]
        write_csv(
            self.crawler_data / "tiktok/comments.csv",
            canonical_columns,
            [
                {
                    "platform": "tiktok",
                    "category": "direct",
                    "query_type": "apify_post_url",
                    "keyword": "https://tiktok.test/video/1",
                    "content_id": "tk1",
                    "video_id": "tk1",
                    "title": "TikTok title",
                    "comment_id": "tkc1",
                    "author": "tk user",
                    "published_at": "2026-01-01",
                    "comment": "TikTok comment",
                },
                {
                    "platform": "tiktok",
                    "category": "direct",
                    "query_type": "apify_post_reply",
                    "keyword": "https://tiktok.test/video/1",
                    "content_id": "tk1",
                    "video_id": "tk1",
                    "title": "",
                    "comment_id": "tkr1",
                    "author": "reply user",
                    "published_at": "2026-01-02",
                    "comment": "TikTok reply",
                },
            ],
        )
        write_csv(
            self.crawler_data / "voz/comments.csv",
            [
                "title",
                "thread_url",
                "post_id",
                "username",
                "datetime",
                "comment",
                "page",
            ],
            [
                {
                    "title": "VOZ title",
                    "thread_url": "https://voz.test/t/1",
                    "post_id": "v1",
                    "username": "voz author",
                    "datetime": "2026",
                    "comment": "VOZ post",
                    "page": 1,
                },
                {
                    "title": "VOZ title",
                    "thread_url": "https://voz.test/t/1",
                    "post_id": "v2",
                    "username": "voz commenter",
                    "datetime": "",
                    "comment": "VOZ comment",
                    "page": 1,
                },
            ],
        )
        youtube_keyword_columns = [
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
        ]
        write_csv(
            self.crawler_data / "youtube/keywords.csv",
            youtube_keyword_columns,
            [
                {
                    "platform": "youtube",
                    "category": "test",
                    "query_type": "keyword",
                    "keyword": "query",
                    "video_id": "yt1",
                    "title": "YouTube title",
                    "comment_id": "ytc1",
                    "author": "yt user",
                    "published_at": "2026",
                    "comment": "YouTube keyword comment",
                }
            ],
        )
        write_csv(
            self.crawler_data / "youtube/links.csv",
            [
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
            ],
            [
                {
                    "video_id": "yt2",
                    "video_url": "https://youtube.test/watch?v=yt2",
                    "title": "Link title",
                    "channel_title": "Channel",
                    "comment_id": "ytc2",
                    "parent_id": "",
                    "is_reply": "False",
                    "comment": "Top-level comment",
                    "like_count": 3,
                    "published_at": "2026",
                    "updated_at": "2026",
                },
                {
                    "video_id": "yt2",
                    "video_url": "https://youtube.test/watch?v=yt2",
                    "title": "Link title",
                    "channel_title": "Channel",
                    "comment_id": "ytr2",
                    "parent_id": "ytc2",
                    "is_reply": "True",
                    "comment": "Reply comment",
                    "like_count": 1,
                    "published_at": "2026",
                    "updated_at": "2026",
                },
            ],
        )
        sources = [
            ("facebook_group", "facebook", "facebook_group_json", "facebook/group.json"),
            ("facebook_page", "facebook", "facebook_page_json", "facebook/page.json"),
            ("facebook_single_post", "facebook", "facebook_single_json", "facebook/single.json"),
            ("thread_city", "threads", "thread_city_csv", "threads/comments.csv"),
            ("tiktok", "tiktok", "tiktok_csv", "tiktok/comments.csv"),
            ("voz", "voz", "voz_csv", "voz/comments.csv"),
            ("youtube_keywords", "youtube", "youtube_keywords_csv", "youtube/keywords.csv"),
            ("youtube_links", "youtube", "youtube_links_csv", "youtube/links.csv"),
        ]
        write_json(
            self.config,
            {
                "version": 1,
                "sources": [
                    {
                        "name": name,
                        "platform": platform,
                        "adapter": adapter,
                        "path": path,
                    }
                    for name, platform, adapter, path in sources
                ],
            },
        )

    def merge(self) -> merge_raw.MergeResult:
        return merge_raw.merge_raw(
            crawler_data=self.crawler_data,
            output_dir=self.output_dir,
            sources_config=self.config,
        )

    def test_all_adapters_share_one_schema(self) -> None:
        result = self.merge()
        self.assertEqual(result.total_rows, 14)
        self.assertEqual(
            result.source_counts,
            {
                "facebook_group": 2,
                "facebook_page": 2,
                "facebook_single_post": 2,
                "thread_city": 1,
                "tiktok": 2,
                "voz": 2,
                "youtube_keywords": 1,
                "youtube_links": 2,
            },
        )
        with result.json_path.open(encoding="utf-8") as file:
            rows = json.load(file)
        self.assertTrue(all(list(row) == merge_raw.RAW_COLUMNS for row in rows))
        self.assertEqual(
            [row["row_id"] for row in rows],
            list(range(1, 15)),
        )
        self.assertEqual(
            {row["platform"] for row in rows},
            {"facebook", "threads", "tiktok", "voz", "youtube"},
        )
        self.assertTrue(all("comment" in row for row in rows))
        self.assertTrue(all("source_file" not in row for row in rows))

    def test_csv_json_parity_and_rebuild_are_deterministic(self) -> None:
        first = self.merge()
        first_csv = first.csv_path.read_bytes()
        first_json = first.json_path.read_bytes()
        second = self.merge()
        self.assertEqual(first_csv, second.csv_path.read_bytes())
        self.assertEqual(first_json, second.json_path.read_bytes())

        with second.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            csv_rows = list(csv.DictReader(file))
        with second.json_path.open("r", encoding="utf-8") as file:
            json_rows = json.load(file)
        self.assertEqual(
            [int(row["row_id"]) for row in csv_rows],
            [row["row_id"] for row in json_rows],
        )

    def test_invalid_source_keeps_previous_outputs(self) -> None:
        result = self.merge()
        old_csv = result.csv_path.read_bytes()
        old_json = result.json_path.read_bytes()
        (self.crawler_data / "facebook/page.json").write_text(
            "{invalid",
            encoding="utf-8",
        )
        with self.assertRaises(merge_raw.MergeError):
            self.merge()
        self.assertEqual(old_csv, result.csv_path.read_bytes())
        self.assertEqual(old_json, result.json_path.read_bytes())

    def test_source_outside_crawler_data_is_rejected(self) -> None:
        outside = self.root / "outside.csv"
        outside.write_text("a\n1\n", encoding="utf-8")
        write_json(
            self.config,
            {
                "version": 1,
                "sources": [
                    {
                        "name": "outside",
                        "platform": "test",
                        "adapter": "thread_city_csv",
                        "path": "../outside.csv",
                    }
                ],
            },
        )
        with self.assertRaisesRegex(merge_raw.MergeError, "ngoai Crawler/data"):
            self.merge()


class ProductionManifestTest(unittest.TestCase):
    def test_manifest_excludes_mirror_and_operational_files(self) -> None:
        config = json.loads(
            (PROJECT_DIR / "config" / "sources.json").read_text(encoding="utf-8")
        )
        paths = {source["path"] for source in config["sources"]}
        self.assertEqual(len(paths), 8)
        self.assertNotIn("voz/voz_comments.json", paths)
        self.assertNotIn("youtube/youtube_links/comments.jsonl", paths)
        self.assertTrue(all(not path.endswith(".bak") for path in paths))
        self.assertTrue(all("errors.csv" not in path for path in paths))


if __name__ == "__main__":
    unittest.main()
