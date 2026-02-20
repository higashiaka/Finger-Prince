/**
 * DC-style date formatting utilities.
 * DCInside shows relative time for recent posts and absolute date for older ones.
 */

export function formatDCDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);

  if (diffMinutes < 1) return "방금 전";
  if (diffMinutes < 60) return `${diffMinutes}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;

  // Older than a day: show MM/DD HH:mm in Korean time
  return date.toLocaleDateString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatViewCount(views: number): string {
  if (views >= 10_000) return `${(views / 10_000).toFixed(1)}만`;
  if (views >= 1_000) return `${(views / 1_000).toFixed(1)}천`;
  return String(views);
}
