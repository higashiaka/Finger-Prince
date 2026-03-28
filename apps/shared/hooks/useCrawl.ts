import { useState, useCallback } from "react";

export type CrawlStatus = "idle" | "running" | "done" | "error";

interface CrawlState {
  status: CrawlStatus;
  message: string;
  postsIndexed: number;
  error: string | null;
}

/**
 * Triggers a DCInside gallery crawl via Electron IPC or REST.
 * Returns live status updates as the Python sidecar runs.
 */
export function useCrawl(apiBase = "/api") {
  const [state, setState] = useState<CrawlState>({
    status: "idle",
    message: "",
    postsIndexed: 0,
    error: null,
  });

  const startCrawl = useCallback(
    async (gallId: string, maxPages = 5) => {
      if (!gallId.trim()) return;

      setState({ status: "running", message: "크롤링 시작...", postsIndexed: 0, error: null });

      try {
        // Electron bridge
        if (typeof window !== "undefined" && (window as any).fingerPrince) {
          const result = await (window as any).fingerPrince.crawl(gallId, maxPages);
          setState({
            status: "done",
            message: `완료: ${result.postsIndexed}개 게시물 인덱싱`,
            postsIndexed: result.postsIndexed,
            error: null,
          });
          return;
        }

        // Web REST fallback
        const response = await fetch(`${apiBase}/crawl`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ gall_id: gallId, max_pages: maxPages }),
        });

        if (!response.ok) {
          const body = await response.text();
          throw new Error(`Crawl failed (${response.status}): ${body}`);
        }

        const json = await response.json() as { posts_indexed: number; message: string };
        setState({
          status: "done",
          message: json.message,
          postsIndexed: json.posts_indexed,
          error: null,
        });
      } catch (err) {
        setState({
          status: "error",
          message: "",
          postsIndexed: 0,
          error: err instanceof Error ? err.message : "크롤링 실패",
        });
      }
    },
    [apiBase]
  );

  const reset = useCallback(() => {
    setState({ status: "idle", message: "", postsIndexed: 0, error: null });
  }, []);

  return { ...state, startCrawl, reset };
}
