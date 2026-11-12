export const API_URL = (() => {
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return window.location.port === "3000" ? "http://127.0.0.1:8005/api" : "/api";
    }
    // Production cloud domain: always communicate directly with production backend
    return process.env.NEXT_PUBLIC_API_URL || "https://api-jobs.dealos.in/api";
  }
  return process.env.NEXT_PUBLIC_API_URL || "https://api-jobs.dealos.in/api";
})();

export async function getApiError(response: Response, fallback: string): Promise<string> {
  const data = await response.json().catch(() => null) as { detail?: unknown; error?: unknown; message?: unknown } | null;
  if (response.status === 429) return "You’ve tried this too many times. Please wait a while and try again.";
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.message === "string") return data.message;
  if (typeof data?.error === "string") return data.error;
  if (response.status >= 500) return "Something went wrong on our side. Please try again shortly.";
  if (!response.ok) return fallback;
  return fallback;
}
