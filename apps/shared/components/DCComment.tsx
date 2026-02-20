import React from "react";
import { formatDCDate } from "../utils/dateFormatter.js";

export type Persona = "aggressive_helper" | "fact_checker" | "meme_lord" | "helpful_sunbae";

const PERSONA_META: Record<Persona, { label: string; colorClass: string }> = {
  aggressive_helper: { label: "빡친도우미", colorClass: "bg-red-600 text-white" },
  fact_checker: { label: "팩트체커", colorClass: "bg-blue-600 text-white" },
  meme_lord: { label: "밈왕", colorClass: "bg-purple-600 text-white" },
  helpful_sunbae: { label: "개념글봇", colorClass: "bg-green-600 text-white" },
};

export interface CommentData {
  id: string;
  author: string;
  text: string;
  date: string;
  /** If set, this is an AI-generated comment with a DC persona */
  persona?: Persona;
  /** Nested replies */
  replies?: CommentData[];
  isAI?: boolean;
}

interface DCCommentProps {
  comment: CommentData;
  depth?: number;
}

export function DCComment({ comment, depth = 0 }: DCCommentProps) {
  const personaMeta = comment.persona ? PERSONA_META[comment.persona] : null;
  const isReply = depth > 0;

  return (
    <div
      className={`border-b border-dc-border text-dc-text font-dc text-sm ${
        isReply ? "ml-6 bg-dc-bg/50 pl-2" : "bg-dc-surface"
      }`}
    >
      <div className="flex items-center gap-2 px-3 py-1.5">
        {isReply && (
          <span className="text-dc-muted text-xs mr-1">└</span>
        )}

        {/* Author / persona badge */}
        {personaMeta ? (
          <span
            className={`text-xs px-1.5 py-0.5 rounded-dc font-bold ${personaMeta.colorClass}`}
          >
            {personaMeta.label}
          </span>
        ) : (
          <span className="text-dc-muted text-xs font-bold truncate max-w-[120px]">
            {comment.author}
          </span>
        )}

        {comment.isAI && (
          <span className="text-dc-gold text-xs">✦ AI</span>
        )}

        {/* Comment body */}
        <span className="flex-1 text-dc-text leading-relaxed">{comment.text}</span>

        {/* Timestamp */}
        <span className="text-dc-muted text-xs whitespace-nowrap ml-2">
          {formatDCDate(comment.date)}
        </span>
      </div>

      {/* Nested replies */}
      {comment.replies?.map((reply) => (
        <DCComment key={reply.id} comment={reply} depth={depth + 1} />
      ))}
    </div>
  );
}
