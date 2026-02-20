import React from "react";
import { formatDCDate, formatViewCount } from "../utils/dateFormatter.js";
import { DCComment, type CommentData } from "./DCComment.js";

export interface PostData {
  id: string;
  gallId: string;
  title: string;
  body: string;
  author: string;
  date: string;
  views: number;
  upvotes: number;
  /** Relevance score from vector search (0–1) */
  score?: number;
  comments: CommentData[];
  sourceUrl?: string;
}

interface DCPostProps {
  post: PostData;
  /** Show full body or collapsed preview */
  expanded?: boolean;
  onExpand?: () => void;
}

export function DCPost({ post, expanded = false, onExpand }: DCPostProps) {
  const previewBody = post.body.slice(0, 280);
  const isTruncated = post.body.length > 280;

  return (
    <article className="bg-dc-surface border border-dc-border rounded-dc mb-2 font-dc text-dc-text">
      {/* Post header */}
      <div className="px-3 py-2 border-b border-dc-border flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <h2 className="text-dc-text text-base font-bold leading-snug truncate">
            {post.title}
          </h2>
          <div className="flex items-center gap-2 mt-0.5 text-dc-muted text-xs">
            <span>{post.gallId}</span>
            <span>|</span>
            <span>{post.author}</span>
            <span>|</span>
            <span>{formatDCDate(post.date)}</span>
            <span>|</span>
            <span>조회 {formatViewCount(post.views)}</span>
            <span>|</span>
            <span className="text-dc-gold">추천 {post.upvotes}</span>
          </div>
        </div>
        {post.score !== undefined && (
          <div
            className="text-xs text-dc-gold border border-dc-gold px-1.5 py-0.5 rounded-dc whitespace-nowrap"
            title="벡터 유사도 점수"
          >
            {(post.score * 100).toFixed(0)}% 일치
          </div>
        )}
      </div>

      {/* Post body */}
      <div className="px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap">
        {expanded ? post.body : previewBody}
        {!expanded && isTruncated && (
          <button
            onClick={onExpand}
            className="ml-1 text-dc-gold text-xs hover:underline"
          >
            ...더 보기
          </button>
        )}
      </div>

      {/* Comments */}
      {expanded && post.comments.length > 0 && (
        <div className="border-t border-dc-border">
          <div className="px-3 py-1 text-xs text-dc-muted bg-dc-bg/30">
            댓글 {post.comments.length}개
          </div>
          {post.comments.map((c) => (
            <DCComment key={c.id} comment={c} />
          ))}
        </div>
      )}

      {/* Footer */}
      {post.sourceUrl && (
        <div className="px-3 py-1.5 border-t border-dc-border text-right">
          <a
            href={post.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-dc-muted hover:text-dc-gold transition-colors"
          >
            원문 보기 →
          </a>
        </div>
      )}
    </article>
  );
}
