import React, { useState } from "react";
import { DCBoard } from "../../shared/components/DCBoard.js";
import { useSearch } from "../../shared/hooks/useSearch.js";
import { useCrawl } from "../../shared/hooks/useCrawl.js";

export default function App() {
  const [query, setQuery] = useState("");
  const [gallId, setGallId] = useState("programming");
  const [showCrawlPanel, setShowCrawlPanel] = useState(false);

  const { data, isLoading, error, search, reset } = useSearch();
  const {
    status: crawlStatus,
    message: crawlMessage,
    error: crawlError,
    startCrawl,
    reset: resetCrawl,
  } = useCrawl();

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) search(query);
  }

  return (
    <div className="min-h-screen bg-dc-bg font-dc text-dc-text">
      {/* Top navigation bar */}
      <nav className="bg-dc-surface border-b border-dc-border px-4 py-2 flex items-center gap-3 sticky top-0 z-10">
        <span className="text-dc-gold font-bold text-xl select-none">👑</span>
        <span className="text-dc-text font-bold text-base hidden sm:block">핑거 프린스</span>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex-1 flex gap-2 max-w-2xl mx-auto">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="뭐가 궁금하세요? 구글에서 찾아서 DC로 답해드립니다"
            className="flex-1 bg-dc-bg border border-dc-border text-dc-text placeholder-dc-muted text-sm px-3 py-1.5 rounded-dc focus:outline-none focus:border-dc-gold transition-colors"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="bg-dc-gold text-dc-bg font-bold text-sm px-4 py-1.5 rounded-dc hover:bg-dc-gold-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "검색 중..." : "검색"}
          </button>
          {data && (
            <button
              type="button"
              onClick={reset}
              className="text-dc-muted text-xs hover:text-dc-text px-2"
            >
              초기화
            </button>
          )}
        </form>

        <button
          onClick={() => setShowCrawlPanel(!showCrawlPanel)}
          className="text-dc-muted text-xs hover:text-dc-gold transition-colors whitespace-nowrap"
        >
          수동 크롤
        </button>
      </nav>

      {/* 수동 크롤 패널 (접힘) */}
      {showCrawlPanel && (
        <div className="bg-dc-surface border-b border-dc-border px-4 py-3 flex flex-wrap items-center gap-3">
          <span className="text-dc-muted text-xs">갤러리 직접 크롤링:</span>
          <input
            type="text"
            value={gallId}
            onChange={(e) => setGallId(e.target.value)}
            placeholder="갤러리 ID (예: programming)"
            className="bg-dc-bg border border-dc-border text-dc-text text-sm px-3 py-1 rounded-dc focus:outline-none focus:border-dc-gold w-48"
          />
          <button
            onClick={() => { resetCrawl(); startCrawl(gallId); }}
            disabled={crawlStatus === "running"}
            className="bg-dc-gold/20 border border-dc-gold text-dc-gold text-xs font-bold px-3 py-1 rounded-dc hover:bg-dc-gold hover:text-dc-bg disabled:opacity-50 transition-colors"
          >
            {crawlStatus === "running" ? "크롤링 중..." : "크롤 시작"}
          </button>
          {crawlMessage && <span className="text-dc-green text-xs">{crawlMessage}</span>}
          {crawlError && <span className="text-dc-red text-xs">{crawlError}</span>}
        </div>
      )}

      {/* 스마트 검색 진행 상황 */}
      {isLoading && (
        <div className="max-w-4xl mx-auto px-2 pt-4">
          <div className="bg-dc-surface border border-dc-border rounded-dc px-4 py-3 text-dc-muted text-xs space-y-1">
            <p>🔍 구글에서 관련 DC 게시물 검색 중...</p>
            <p>🕷️ 발견된 갤러리 크롤링 + 인덱싱 중...</p>
            <p className="text-dc-gold">⏳ 처음 검색은 1~2분 소요될 수 있습니다</p>
          </div>
        </div>
      )}

      {/* 발견된 갤러리 배지 */}
      {data && data.discoveredGalls && data.discoveredGalls.length > 0 && (
        <div className="max-w-4xl mx-auto px-2 pt-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-dc-muted text-xs">발견된 갤러리:</span>
            {data.discoveredGalls.map((gall) => (
              <span
                key={gall}
                className="text-xs bg-dc-border text-dc-gold px-2 py-0.5 rounded-dc"
              >
                {gall}
              </span>
            ))}
            <span className="text-dc-muted text-xs ml-auto">
              {data.postsCrawled}개 게시물 크롤링 · {data.queryTime}ms
            </span>
          </div>
        </div>
      )}

      {/* AI 요약 답변 */}
      {data?.synthesizedAnswer && (
        <div className="max-w-4xl mx-auto px-2 pt-3">
          <div className="bg-dc-surface border border-dc-gold/40 rounded-dc p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-dc-gold text-xs font-bold">✦ AI 요약 답변</span>
              <span className="text-dc-muted text-xs">({data.persona} 페르소나)</span>
            </div>
            <p className="text-dc-text text-sm leading-relaxed whitespace-pre-wrap">
              {data.synthesizedAnswer}
            </p>
          </div>
        </div>
      )}

      {/* 오류 */}
      {error && (
        <div className="max-w-4xl mx-auto px-2 pt-4">
          <div className="bg-dc-red/10 border border-dc-red rounded-dc p-3 text-dc-red text-sm">
            오류: {error}
          </div>
        </div>
      )}

      {/* 결과 게시판 */}
      <DCBoard
        gallId="smart"
        title="핑거 프린스 검색 결과"
        posts={data?.posts ?? []}
        isLoading={isLoading}
        query={query}
      />
    </div>
  );
}
