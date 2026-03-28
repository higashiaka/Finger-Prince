import React, { useState } from "react";
import { DCPost, type PostData } from "./DCPost.js";

interface DCBoardProps {
  gallId: string;
  title: string;
  posts: PostData[];
  isLoading?: boolean;
  query?: string;
}

export function DCBoard({ gallId, title, posts, isLoading = false, query }: DCBoardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="bg-dc-bg min-h-screen font-dc text-dc-text">
      {/* Board header — mimics DC gallery header */}
      <div className="bg-dc-surface border-b border-dc-border px-4 py-2 flex items-center gap-3">
        <span className="text-dc-gold font-bold text-lg">👑</span>
        <div>
          <h1 className="text-dc-text font-bold text-base">{title}</h1>
          <p className="text-dc-muted text-xs">{gallId} · 핑거 프린스 검색 결과</p>
        </div>
        {query && (
          <div className="ml-auto text-dc-muted text-xs">
            <span className="text-dc-gold">"{query}"</span> 검색 결과 {posts.length}건
          </div>
        )}
      </div>

      {/* Post list */}
      <div className="max-w-4xl mx-auto px-2 py-3">
        {isLoading ? (
          <LoadingSkeleton />
        ) : posts.length === 0 ? (
          <EmptyState query={query} />
        ) : (
          posts.map((post) => (
            <DCPost
              key={post.id}
              post={post}
              expanded={expandedId === post.id}
              onExpand={() => setExpandedId(expandedId === post.id ? null : post.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="bg-dc-surface border border-dc-border rounded-dc p-3 animate-pulse"
        >
          <div className="h-4 bg-dc-border rounded w-3/4 mb-2" />
          <div className="h-3 bg-dc-border rounded w-1/3" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ query }: { query?: string }) {
  return (
    <div className="text-center py-16 text-dc-muted">
      <p className="text-4xl mb-3">🤔</p>
      <p className="text-base font-bold text-dc-text">결과가 없습니다</p>
      {query ? (
        <p className="text-sm mt-1">
          "<span className="text-dc-gold">{query}</span>"에 대한 게시물을 찾을 수 없어요.
        </p>
      ) : (
        <p className="text-sm mt-1">검색어를 입력하거나 갤러리를 크롤링해보세요.</p>
      )}
    </div>
  );
}
