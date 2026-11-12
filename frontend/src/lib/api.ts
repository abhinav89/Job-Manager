export const API_URL =
  typeof window !== "undefined" && window.location.port === "3000"
    ? "http://127.0.0.1:8005/api"
    : process.env.NEXT_PUBLIC_API_URL || "/api";

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
