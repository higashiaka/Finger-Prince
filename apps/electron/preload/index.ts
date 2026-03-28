import { contextBridge, ipcRenderer } from "electron";

/**
 * Exposes a safe, typed API to the renderer (React) process via contextBridge.
 * The renderer accesses this as `window.fingerPrince`.
 */
contextBridge.exposeInMainWorld("fingerPrince", {
  /**
   * Trigger a DCInside gallery crawl.
   * @returns Promise resolving to { postsIndexed, message }
   */
  crawl: (gallId: string, maxPages = 5) =>
    ipcRenderer.invoke("crawl:start", { gallId, maxPages }),

  /**
   * Perform a semantic search against the local vector DB.
   * @returns Promise resolving to RAGResult
   */
  search: (query: string, topK = 5) =>
    ipcRenderer.invoke("search:query", { query, topK }),

  /**
   * Get current crawl/sidecar status.
   */
  getStatus: () => ipcRenderer.invoke("crawl:status"),

  /**
   * Subscribe to backend log lines (e.g., for a dev console panel).
   */
  onBackendLog: (callback: (line: string) => void) => {
    const handler = (_event: Electron.IpcRendererEvent, line: string) =>
      callback(line);
    ipcRenderer.on("backend:log", handler);
    // Return an unsubscribe function
    return () => ipcRenderer.removeListener("backend:log", handler);
  },
});

// TypeScript augmentation for window.fingerPrince
export type FingerPrinceAPI = {
  crawl: (gallId: string, maxPages?: number) => Promise<{ postsIndexed: number; message: string }>;
  search: (query: string, topK?: number) => Promise<unknown>;
  getStatus: () => Promise<{ sidecarRunning: boolean }>;
  onBackendLog: (callback: (line: string) => void) => () => void;
};

declare global {
  interface Window {
    fingerPrince: FingerPrinceAPI;
  }
}
