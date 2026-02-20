import { ipcMain, BrowserWindow } from "electron";
import { isSidecarRunning } from "../python-bridge/sidecar.js";

const BACKEND_BASE = "http://localhost:8000";

async function fetchBackend<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const response = await fetch(`${BACKEND_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend error (${response.status}): ${text}`);
  }
  return response.json() as Promise<T>;
}

/**
 * Registers all IPC handlers for the main process.
 * Must be called after app.whenReady().
 */
export function registerIpcHandlers(win: BrowserWindow): void {
  // ── crawl:start ────────────────────────────────────────────────────────
  ipcMain.handle(
    "crawl:start",
    async (_event, { gallId, maxPages }: { gallId: string; maxPages: number }) => {
      win.webContents.send("backend:log", `[IPC] crawl:start gall=${gallId} pages=${maxPages}`);
      return fetchBackend<{ posts_indexed: number; message: string }>("/api/crawl", {
        gall_id: gallId,
        max_pages: maxPages,
      }).then((r) => ({ postsIndexed: r.posts_indexed, message: r.message }));
    }
  );

  // ── search:query ────────────────────────────────────────────────────────
  ipcMain.handle(
    "search:query",
    async (_event, { query, topK }: { query: string; topK: number }) => {
      win.webContents.send("backend:log", `[IPC] search:query "${query}" top_k=${topK}`);
      return fetchBackend("/api/search", { query, top_k: topK });
    }
  );

  // ── crawl:status ────────────────────────────────────────────────────────
  ipcMain.handle("crawl:status", async () => ({
    sidecarRunning: isSidecarRunning(),
  }));
}
