"""
Finger-Prince API routes.

POST /api/crawl         — 수동으로 갤러리 크롤링 & 인덱싱
POST /api/search        — 크롤링된 데이터에서 시맨틱 검색
POST /api/smart-search  — 구글 검색 → 갤러리 자동 발견 → 크롤링 → 시맨틱 검색 (원스톱)
GET  /api/health        — 서버 상태 확인
"""

from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from crawler.dc_crawler import DCCrawler
from crawler.google_discovery import discover_from_google
from engine.embedding import EmbeddingFactory
from engine.vector_db import VectorDB
from engine.persona_prompt import build_rag_prompt, PERSONAS

router = APIRouter()

# ── Shared singletons (created once on import) ────────────────────────────────
_embedding = EmbeddingFactory.create()
_vector_db = VectorDB()


# ── Request / Response models ─────────────────────────────────────────────────

class CrawlRequest(BaseModel):
    gall_id: str = Field(..., examples=["programming"], description="DCInside 갤러리 ID")
    max_pages: int = Field(default=5, ge=1, le=50)
    is_mgall: bool = Field(default=False, description="마이너 갤러리 여부")


class CrawlResponse(BaseModel):
    posts_indexed: int
    message: str
    elapsed_seconds: float


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["파이썬 비동기 처리 방법"])
    top_k: int = Field(default=5, ge=1, le=20)
    persona: str = Field(default="aggressive_helper")
    gall_id: str | None = Field(default=None, description="검색 범위를 특정 갤러리로 제한")


class SmartSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["엘든링 현재 메타"])
    top_k: int = Field(default=5, ge=1, le=20)
    persona: str = Field(default="aggressive_helper")
    google_results: int = Field(default=10, ge=3, le=20, description="구글 검색 결과 수")
    gallery_pages: int = Field(default=2, ge=1, le=10, description="갤러리당 추가 크롤링 페이지 수")


class CommentOut(BaseModel):
    id: str
    author: str
    text: str
    date: str
    persona: str | None = None
    is_ai: bool = False
    replies: list["CommentOut"] = []


class PostOut(BaseModel):
    id: str
    gall_id: str
    title: str
    body: str
    author: str
    date: str
    views: int
    upvotes: int
    score: float
    comments: list[CommentOut] = []
    source_url: str | None = None


class SearchResponse(BaseModel):
    posts: list[PostOut]
    synthesized_answer: str | None
    persona: str
    query_time: int  # milliseconds


class SmartSearchResponse(BaseModel):
    posts: list[PostOut]
    synthesized_answer: str | None
    persona: str
    query_time: int
    discovered_galls: list[str]  # 구글로 발견된 갤러리 목록
    posts_crawled: int           # 이번 검색에서 새로 크롤링된 게시물 수


# ── 공통 헬퍼 ─────────────────────────────────────────────────────────────────

def _run_llm(prompt: str) -> str | None:
    """Groq LLM 호출. 실패해도 None 반환 (검색 결과는 유지)."""
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.8,
        )
        return completion.choices[0].message.content
    except Exception as exc:
        print(f"[llm] 호출 실패: {exc}")
        return None


def _results_to_posts_out(raw_results: list[dict[str, Any]], fallback_gall: str = "") -> list[PostOut]:
    posts_out: list[PostOut] = []
    for r in raw_results:
        posts_out.append(
            PostOut(
                id=r.get("id", ""),
                gall_id=r.get("gall_id", fallback_gall),
                title=r.get("title", ""),
                body=r.get("body", ""),
                author=r.get("author", ""),
                date=r.get("date", ""),
                views=r.get("views", 0),
                upvotes=r.get("upvotes", 0),
                score=r.get("score", 0.0),
                comments=[
                    CommentOut(
                        id=c.get("id", f"c{i}"),
                        author=c.get("author", ""),
                        text=c.get("text", ""),
                        date=c.get("date", r.get("date", "")),
                    )
                    for i, c in enumerate(r.get("comments", []))
                ],
                source_url=r.get("source_url"),
            )
        )
    return posts_out


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "finger-prince-backend"}


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest) -> CrawlResponse:
    """수동으로 갤러리를 크롤링하고 ChromaDB에 인덱싱합니다."""
    start = time.perf_counter()

    crawler = DCCrawler(gall_id=req.gall_id, delay=1.0, is_mgall=req.is_mgall)
    posts: list[dict[str, Any]] = []

    for page in range(1, req.max_pages + 1):
        page_posts = crawler.crawl_post_list(page)
        for stub in page_posts:
            try:
                detail = crawler.crawl_post_detail(stub["id"])
                posts.append({**stub, **detail})
            except Exception as exc:
                print(f"[crawl] 게시물 {stub['id']} 스킵: {exc}")

    if not posts:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다. 갤러리 ID를 확인하세요.")

    _vector_db.upsert_posts(posts, embedding_provider=_embedding)

    elapsed = time.perf_counter() - start
    return CrawlResponse(
        posts_indexed=len(posts),
        message=f"{req.gall_id} 갤러리 {len(posts)}개 게시물 인덱싱 완료",
        elapsed_seconds=round(elapsed, 2),
    )


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """이미 인덱싱된 데이터에서 시맨틱 검색 + RAG 답변을 반환합니다."""
    start_ms = int(time.time() * 1000)

    if req.persona not in PERSONAS:
        req.persona = "aggressive_helper"

    raw_results = _vector_db.search(
        query=req.query,
        top_k=req.top_k,
        embedding_provider=_embedding,
        gall_id=req.gall_id,
    )

    if not raw_results:
        return SearchResponse(
            posts=[],
            synthesized_answer="관련 게시물이 없습니다. 먼저 갤러리를 크롤링하거나 스마트 검색을 사용해주세요.",
            persona=req.persona,
            query_time=int(time.time() * 1000) - start_ms,
        )

    prompt = build_rag_prompt(req.query, raw_results, persona=req.persona)
    synthesized = _run_llm(prompt)

    return SearchResponse(
        posts=_results_to_posts_out(raw_results, req.gall_id or ""),
        synthesized_answer=synthesized,
        persona=req.persona,
        query_time=int(time.time() * 1000) - start_ms,
    )


@router.post("/smart-search", response_model=SmartSearchResponse)
async def smart_search(req: SmartSearchRequest) -> SmartSearchResponse:
    """
    원스톱 스마트 검색:
      1단계) 구글에서 "site:gall.dcinside.com {query}" 검색
      2단계) 발견된 게시물 URL에서 갤러리 ID 추출 & 목록 저장
      3단계) 구글에서 찾은 게시물 직접 크롤링 (seed 게시물)
      4단계) 발견된 갤러리에서 추가 페이지 크롤링
      5단계) 전체 크롤링 결과 ChromaDB에 인덱싱
      6단계) 시맨틱 검색 + Groq RAG 답변 생성
    """
    start_ms = int(time.time() * 1000)

    if req.persona not in PERSONAS:
        req.persona = "aggressive_helper"

    # ── 1단계: 구글 검색으로 갤러리 & 게시물 발견 ────────────────────────────
    discovery = discover_from_google(req.query, num_results=req.google_results)
    discovered_galls: list[str] = discovery["gall_ids"]
    found_posts_meta: list[dict[str, Any]] = discovery["posts"]

    all_posts: list[dict[str, Any]] = []

    # ── 2단계: 구글에서 찾은 게시물 직접 크롤링 ──────────────────────────────
    for post_meta in found_posts_meta:
        gall_id = post_meta["gall_id"]
        post_id = post_meta["post_id"]
        is_mgall = post_meta.get("is_mgall", False)

        if not post_id:
            continue

        try:
            crawler = DCCrawler(gall_id=gall_id, delay=1.0, is_mgall=is_mgall)
            detail = crawler.crawl_post_detail(post_id)
            all_posts.append(detail)
            print(f"[smart-search] 시드 게시물 크롤링 완료: {gall_id}/{post_id}")
        except Exception as exc:
            print(f"[smart-search] 시드 게시물 스킵 {gall_id}/{post_id}: {exc}")

    # ── 3단계: 발견된 갤러리에서 추가 페이지 크롤링 ──────────────────────────
    for gall_id in discovered_galls:
        is_mgall = any(
            p["is_mgall"] for p in found_posts_meta if p["gall_id"] == gall_id
        )
        try:
            crawler = DCCrawler(gall_id=gall_id, delay=1.0, is_mgall=is_mgall)
            for page in range(1, req.gallery_pages + 1):
                stubs = crawler.crawl_post_list(page)
                for stub in stubs:
                    try:
                        detail = crawler.crawl_post_detail(stub["id"])
                        all_posts.append({**stub, **detail})
                    except Exception as exc:
                        print(f"[smart-search] 갤 게시물 스킵 {stub['id']}: {exc}")
            print(f"[smart-search] 갤러리 크롤링 완료: {gall_id} ({req.gallery_pages}페이지)")
        except Exception as exc:
            print(f"[smart-search] 갤러리 스킵 {gall_id}: {exc}")

    posts_crawled = len(all_posts)

    # ── 4단계: ChromaDB에 인덱싱 ─────────────────────────────────────────────
    if all_posts:
        _vector_db.upsert_posts(all_posts, embedding_provider=_embedding)
        print(f"[smart-search] {posts_crawled}개 게시물 인덱싱 완료")

    # ── 5단계: 시맨틱 검색 ───────────────────────────────────────────────────
    raw_results = _vector_db.search(
        query=req.query,
        top_k=req.top_k,
        embedding_provider=_embedding,
    )

    if not raw_results:
        return SmartSearchResponse(
            posts=[],
            synthesized_answer="관련 정보를 찾지 못했습니다. 다른 검색어를 시도해보세요.",
            persona=req.persona,
            query_time=int(time.time() * 1000) - start_ms,
            discovered_galls=discovered_galls,
            posts_crawled=posts_crawled,
        )

    # ── 6단계: Groq RAG 답변 생성 ────────────────────────────────────────────
    prompt = build_rag_prompt(req.query, raw_results, persona=req.persona)
    synthesized = _run_llm(prompt)

    return SmartSearchResponse(
        posts=_results_to_posts_out(raw_results),
        synthesized_answer=synthesized,
        persona=req.persona,
        query_time=int(time.time() * 1000) - start_ms,
        discovered_galls=discovered_galls,
        posts_crawled=posts_crawled,
    )
