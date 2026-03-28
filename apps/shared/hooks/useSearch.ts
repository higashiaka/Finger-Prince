import { useState, useCallback } from "react";
import type { PostData } from "../components/DCPost.js";

export interface RAGResult {
  posts: PostData[];
  synthesizedAnswer: string | null;
  persona: string;
  queryTime: number;
}

export interface SmartSearchResult extends RAGResult {
  discoveredGalls: string[];
  postsCrawled: number;
}

interface SearchState {
  data: SmartSearchResult | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * 스마트 검색 훅:
 * 구글 검색 → 갤러리 자동 발견 → 크롤링 → 시맨틱 검색 + RAG 답변
 * Electron IPC와 웹 REST 양쪽을 자동으로 처리합니다.
 */
export function useSearch(apiBase = "/api") {
  const [state, setState] = useState<SearchState>({
    data: null,
    isLoading: false,
    error: null,
  });

  const search = useCallback(
    async (query: string, topK = 5) => {
      if (!query.trim()) return;

      setState({ data: null, isLoading: true, error: null });

      try {
        // Electron bridge
        if (typeof window !== "undefined" && (window as any).fingerPrince) {
          const result = await (window as any).fingerPrince.search(query, topK);
          setState({ data: result, isLoading: false, error: null });
          return;
        }

        // 웹: /api/smart-search 호출
        const response = await fetch(`${apiBase}/smart-search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            top_k: topK,
            google_results: 10,
            gallery_pages: 2,
          }),
        });

        if (!response.ok) {
          const body = await response.text();
          throw new Error(`검색 실패 (${response.status}): ${body}`);
        }

        const json = await response.json();

        // snake_case → camelCase 변환
        const data: SmartSearchResult = {
          posts: json.posts,
          synthesizedAnswer: json.synthesized_answer,
          persona: json.persona,
          queryTime: json.query_time,
          discoveredGalls: json.discovered_galls ?? [],
          postsCrawled: json.posts_crawled ?? 0,
        };

        setState({ data, isLoading: false, error: null });
      } catch (err) {
        setState({
          data: null,
          isLoading: false,
          error: err instanceof Error ? err.message : "알 수 없는 오류",
        });
      }
    },
    [apiBase]
  );

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return { ...state, search, reset };
}
