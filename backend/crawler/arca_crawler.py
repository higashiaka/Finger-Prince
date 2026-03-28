"""
ArcaLive Crawler (Stub)
~~~~~~~~~~~~~~~~~~~~~~~
Placeholder implementation matching the same interface as DCCrawler.
Implement when ArcaLive support is added.
"""

from __future__ import annotations

from typing import Any


class ArcaCrawler:
    """Crawls ArcaLive channels. Currently a stub — not yet implemented."""

    def __init__(self, channel_id: str, delay: float = 1.0) -> None:
        self.channel_id = channel_id.strip()
        self.delay = delay

    def crawl_post_list(self, page: int = 1) -> list[dict[str, Any]]:
        # TODO: Implement ArcaLive post list scraper
        # ArcaLive URL pattern: https://arca.live/b/{channel_id}?p={page}
        raise NotImplementedError(
            "ArcaLive crawler is not yet implemented. "
            "See: https://arca.live/b/{channel_id}"
        )

    def crawl_post_detail(self, post_id: str) -> dict[str, Any]:
        # TODO: Implement ArcaLive post detail scraper
        # ArcaLive URL pattern: https://arca.live/b/{channel_id}/{post_id}
        raise NotImplementedError(
            "ArcaLive post detail scraper is not yet implemented."
        )
