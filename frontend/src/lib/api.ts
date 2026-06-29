import type { InsightsBundle, PmBuddyChatResponse, PmBuddyChatTurn, ReviewTrends, SynthesisStatus, SynthesisRun, TrendGranularity } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Cannot reach the insights API. Check that the backend is running.",
      0,
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      (body as { detail?: string }).detail ?? response.statusText,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

export async function fetchLatestInsights(): Promise<InsightsBundle> {
  return request<InsightsBundle>("/api/insights/latest");
}

export async function fetchRun(runId: string): Promise<InsightsBundle> {
  return request<InsightsBundle>(`/api/insights/runs/${runId}`);
}

export async function fetchRuns(): Promise<{ runs: SynthesisRun[] }> {
  return request<{ runs: SynthesisRun[] }>("/api/insights/runs");
}

export async function fetchTrends(granularity: TrendGranularity = "month"): Promise<ReviewTrends> {
  return request<ReviewTrends>(`/api/insights/trends?granularity=${granularity}`);
}

export async function sendPmBuddyMessage(
  message: string,
  history: PmBuddyChatTurn[],
): Promise<PmBuddyChatResponse> {
  return request<PmBuddyChatResponse>("/api/pm-buddy/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
}

export async function fetchSynthesisStatus(): Promise<SynthesisStatus> {
  return request("/api/synthesis/status");
}

export async function triggerSynthesis(): Promise<{ started: boolean; message?: string }> {
  return request("/api/synthesize", { method: "POST" });
}

export async function invalidateServerCache(): Promise<void> {
  await request("/api/cache/invalidate", { method: "POST" });
}

export { ApiError };
