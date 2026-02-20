"""
Google Discovery
~~~~~~~~~~~~~~~~
구글 검색으로 DCInside 관련 게시물을 발견하고,
게시물 URL에서 갤러리 ID와 게시물 ID를 추출합니다.

흐름:
    1. Google에서 "site:gall.dcinside.com {query}" 검색
    2. 결과 URL에서 gall_id, post_id 파싱
    3. 발견된 고유 갤러리 ID 목록 반환
       → DCCrawler가 해당 갤러리들을 추가 크롤링
"""

from __future__ import annotations

import re
import time
from typing import Any

# DCInside URL 패턴
# 일반갤: gall.dcinside.com/board/view/?id=programming&no=12345
# 마이너갤: gall.dcinside.com/mgallery/board/view/?id=eldenring&no=12345
_DC_VIEW_PATTERN = re.compile(
    r"gall\.dcinside\.com/(mgallery/)?board/view/\?id=([a-zA-Z0-9_]+)&no=(\d+)"
)
_DC_LIST_PATTERN = re.compile(
    r"gall\.dcinside\.com/(mgallery/)?board/lists/\?id=([a-zA-Z0-9_]+)"
)


def discover_from_google(query: str, num_results: int = 10) -> dict[str, Any]:
    """
    구글에서 DCInside 관련 게시물을 검색하고 갤러리 정보를 추출합니다.

    Returns:
        {
            "gall_ids": ["programming", "eldenring", ...],   # 고유 갤러리 ID 목록
            "posts": [                                        # 발견된 게시물 목록
                {"gall_id": "...", "post_id": "...", "url": "...", "is_mgall": bool},
                ...
            ]
        }
    """
    try:
        from googlesearch import search
    except ImportError:
        raise RuntimeError(
            "googlesearch-python 패키지가 필요합니다: pip install googlesearch-python"
        )

    search_query = f"site:gall.dcinside.com {query}"
    print(f"[google_discovery] 검색 중: {search_query}")

    found_posts: list[dict[str, Any]] = []
    gall_ids: list[str] = []
    seen_galls: set[str] = set()

    try:
        for url in search(search_query, num_results=num_results, lang="ko", sleep_interval=1.5):
            url = str(url)

            # 게시물 URL (view) 우선 파싱
            view_match = _DC_VIEW_PATTERN.search(url)
            if view_match:
                is_mgall = bool(view_match.group(1))
                gall_id = view_match.group(2)
                post_id = view_match.group(3)

                found_posts.append({
                    "gall_id": gall_id,
                    "post_id": post_id,
                    "url": url,
                    "is_mgall": is_mgall,
                })
                if gall_id not in seen_galls:
                    seen_galls.add(gall_id)
                    gall_ids.append(gall_id)
                continue

            # 목록 URL (lists)에서 갤러리 ID만 추출
            list_match = _DC_LIST_PATTERN.search(url)
            if list_match:
                gall_id = list_match.group(2)
                if gall_id not in seen_galls:
                    seen_galls.add(gall_id)
                    gall_ids.append(gall_id)

    except Exception as exc:
        print(f"[google_discovery] 검색 실패: {exc}")

    print(
        f"[google_discovery] 완료 — 게시물 {len(found_posts)}개, "
        f"갤러리 {len(gall_ids)}개 발견: {gall_ids}"
    )
    return {"gall_ids": gall_ids, "posts": found_posts}
