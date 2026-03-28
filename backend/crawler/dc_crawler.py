"""
DCInside Crawler
~~~~~~~~~~~~~~~~
Scrapes post lists, post bodies, and comment threads from DCInside galleries.

Design principles
-----------------
- Rate-limited: enforces a configurable delay between HTTP requests.
- Respectful:   uses a realistic User-Agent and honours HTTP error codes.
- Structured:   returns clean Python dicts ready for the vector embedding pipeline.

Usage
-----
    crawler = DCCrawler(gall_id="programming", delay=1.2)
    stubs   = crawler.crawl_post_list(page=1)
    detail  = crawler.crawl_post_detail(stubs[0]["id"])
"""

from __future__ import annotations

import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

# ── Constants ─────────────────────────────────────────────────────────────────

_BASE_URL = "https://gall.dcinside.com"

_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# ── Types ─────────────────────────────────────────────────────────────────────

PostStub = dict[str, Any]   # Lightweight: id, title, author, date, views
PostDetail = dict[str, Any]  # Full: + body, upvotes, comments


# ── Crawler ───────────────────────────────────────────────────────────────────

class DCCrawler:
    """Scrapes a single DCInside gallery (일반갤/마이너갤/미니갤 supported)."""

    def __init__(self, gall_id: str, delay: float = 1.0, is_mgall: bool = False) -> None:
        self.gall_id = gall_id.strip()
        self.delay = max(0.5, delay)  # Minimum 0.5 s between requests
        self.is_mgall = is_mgall      # 마이너갤 여부
        self._session = requests.Session()
        self._session.headers.update({
            "Referer": self._list_url(1),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        })

    # ── Public API ─────────────────────────────────────────────────────────

    def crawl_post_list(self, page: int = 1) -> list[PostStub]:
        """
        Returns a list of post stubs from a gallery listing page.

        Each stub:
            {id, title, author, date, views, gall_id, source_url}
        """
        url = self._list_url(page)
        soup = self._get(url)
        return self._parse_post_list(soup)

    def crawl_post_detail(self, post_id: str) -> PostDetail:
        """
        Returns the full content of a single post.

        Result includes:
            {title, body, author, date, views, upvotes, comments, source_url}

        ``comments`` is a list of:
            {id, author, text, date, replies: [...]}
        """
        url = self._detail_url(post_id)
        soup = self._get(url)
        return self._parse_post_detail(soup, post_id)

    # ── Private helpers ────────────────────────────────────────────────────

    def _get(self, url: str) -> BeautifulSoup:
        """Performs an HTTP GET with rate limiting and UA rotation."""
        self._session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        time.sleep(self.delay + random.uniform(0, 0.3))

        response = self._session.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _list_url(self, page: int) -> str:
        if self.is_mgall:
            return f"{_BASE_URL}/mgallery/board/lists/?id={self.gall_id}&page={page}"
        return f"{_BASE_URL}/board/lists/?id={self.gall_id}&page={page}"

    def _detail_url(self, post_id: str) -> str:
        if self.is_mgall:
            return f"{_BASE_URL}/mgallery/board/view/?id={self.gall_id}&no={post_id}"
        return f"{_BASE_URL}/board/view/?id={self.gall_id}&no={post_id}"

    # ── Parsers ────────────────────────────────────────────────────────────

    def _parse_post_list(self, soup: BeautifulSoup) -> list[PostStub]:
        stubs: list[PostStub] = []
        rows = soup.select("tr.ub-content")

        for row in rows:
            try:
                # Skip notice rows and ad rows
                if "공지" in (row.get("class") or []):
                    continue

                post_id_el = row.select_one("td.gall_num")
                title_el = row.select_one("td.gall_tit > a")
                author_el = row.select_one("td.gall_writer")
                date_el = row.select_one("td.gall_date")
                views_el = row.select_one("td.gall_count")

                if not (post_id_el and title_el):
                    continue

                post_id = post_id_el.get_text(strip=True)
                if not post_id.isdigit():
                    continue  # Skip sticky/notice posts

                stubs.append({
                    "id": post_id,
                    "gall_id": self.gall_id,
                    "title": title_el.get_text(strip=True),
                    "author": author_el.get_text(strip=True) if author_el else "익명",
                    "date": date_el.get("title") or (date_el.get_text(strip=True) if date_el else ""),
                    "views": int(views_el.get_text(strip=True).replace(",", "") or 0) if views_el else 0,
                    "source_url": self._detail_url(post_id),
                })
            except (AttributeError, ValueError):
                continue

        return stubs

    def _parse_post_detail(self, soup: BeautifulSoup, post_id: str) -> PostDetail:
        # ── Title ──
        title_el = soup.select_one("span.title_subject")
        title = title_el.get_text(strip=True) if title_el else ""

        # ── Author & date ──
        writer_el = soup.select_one("div.fl > span.gall_writer")
        author = writer_el.get("data-nick", "익명") if writer_el else "익명"

        date_el = soup.select_one("span.gall_date")
        date = date_el.get("title") or (date_el.get_text(strip=True) if date_el else "")

        # ── View count ──
        views_el = soup.select_one("span.gall_count")
        views = int(views_el.get_text(strip=True).replace(",", "").replace("조회", "").strip() or 0) if views_el else 0

        # ── Upvotes ──
        upvote_el = soup.select_one("p.up_num")
        upvotes = int(upvote_el.get_text(strip=True) or 0) if upvote_el else 0

        # ── Body ──
        body_el = soup.select_one("div.write_div")
        body = body_el.get_text(separator="\n", strip=True) if body_el else ""

        # ── Comments ──
        comments = self._parse_comments(soup)

        return {
            "id": post_id,
            "gall_id": self.gall_id,
            "title": title,
            "body": body,
            "author": author,
            "date": date,
            "views": views,
            "upvotes": upvotes,
            "comments": comments,
            "source_url": self._detail_url(post_id),
        }

    def _parse_comments(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parses comment threads including nested replies."""
        comments: list[dict[str, Any]] = []
        comment_els = soup.select("li.ub-content[data-no]")

        comment_map: dict[str, dict[str, Any]] = {}

        for el in comment_els:
            cid = el.get("data-no", "")
            parent_id = el.get("data-parent", "")

            author_el = el.select_one("span.nick")
            text_el = el.select_one("p.usertxt")
            date_el = el.select_one("span.date_time")

            comment: dict[str, Any] = {
                "id": cid,
                "author": author_el.get_text(strip=True) if author_el else "익명",
                "text": text_el.get_text(strip=True) if text_el else "",
                "date": date_el.get_text(strip=True) if date_el else "",
                "replies": [],
            }
            comment_map[cid] = comment

            if parent_id and parent_id in comment_map:
                comment_map[parent_id]["replies"].append(comment)
            else:
                comments.append(comment)

        return comments
