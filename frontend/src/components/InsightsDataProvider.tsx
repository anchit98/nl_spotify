"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  fetchLatestInsights,
  fetchSynthesisStatus,
  fetchTrends,
  invalidateServerCache,
} from "@/lib/api";
import type { InsightsBundle, ReviewTrends } from "@/lib/types";
import { filterTrendsForChart } from "@/lib/trends";

type InsightsDataContextValue = {
  bundle: InsightsBundle | null;
  trends: ReviewTrends | null;
  bundleLoading: boolean;
  trendsLoading: boolean;
  bundleError: string | null;
  synthesisInProgress: boolean;
  /** Bumps after each full refresh — use as a React key to remount stale child views. */
  dataGeneration: number;
  refreshAll: () => Promise<void>;
  /** @deprecated Use refreshAll */
  refreshBundle: () => Promise<void>;
};

const InsightsDataContext = createContext<InsightsDataContextValue | null>(null);

let bundleCache: InsightsBundle | null = null;
let trendsCache: ReviewTrends | null = null;
let bundleInflight: Promise<InsightsBundle> | null = null;
let trendsInflight: Promise<ReviewTrends> | null = null;

function loadBundle(): Promise<InsightsBundle> {
  if (bundleCache) return Promise.resolve(bundleCache);
  if (!bundleInflight) {
    bundleInflight = fetchLatestInsights()
      .then((data) => {
        bundleCache = data;
        return data;
      })
      .finally(() => {
        bundleInflight = null;
      });
  }
  return bundleInflight;
}

function loadTrends(): Promise<ReviewTrends> {
  if (trendsCache) return Promise.resolve(trendsCache);
  if (!trendsInflight) {
    trendsInflight = fetchTrends()
      .then((data) => {
        trendsCache = filterTrendsForChart(data);
        return trendsCache;
      })
      .finally(() => {
        trendsInflight = null;
      });
  }
  return trendsInflight;
}

export function invalidateInsightsCache() {
  bundleCache = null;
  trendsCache = null;
  bundleInflight = null;
  trendsInflight = null;
}

export function InsightsDataProvider({ children }: { children: ReactNode }) {
  const [bundle, setBundle] = useState<InsightsBundle | null>(bundleCache);
  const [trends, setTrends] = useState<ReviewTrends | null>(trendsCache);
  const [bundleLoading, setBundleLoading] = useState(!bundleCache);
  const [trendsLoading, setTrendsLoading] = useState(!trendsCache);
  const [bundleError, setBundleError] = useState<string | null>(null);
  const [synthesisInProgress, setSynthesisInProgress] = useState(false);
  const [dataGeneration, setDataGeneration] = useState(0);
  const synthesisWasInProgress = useRef(false);
  const refreshInflight = useRef<Promise<void> | null>(null);

  const refreshAll = useCallback(async () => {
    if (refreshInflight.current) {
      await refreshInflight.current;
      return;
    }

    const job = (async () => {
      invalidateInsightsCache();
      setBundleLoading(true);
      setTrendsLoading(true);
      setBundleError(null);
      try {
        await invalidateServerCache();
      const [bundleData, trendsData] = await Promise.all([
        fetchLatestInsights(),
        fetchTrends("month"),
      ]);
      await fetchTrends("week");
      bundleCache = bundleData;
      trendsCache = filterTrendsForChart(trendsData);
      setBundle(bundleData);
      setTrends(trendsCache);
        setDataGeneration((g) => g + 1);
      } catch (e) {
        setBundleError(e instanceof ApiError ? e.message : "Failed to load insights");
      } finally {
        setBundleLoading(false);
        setTrendsLoading(false);
      }
    })();

    refreshInflight.current = job;
    try {
      await job;
    } finally {
      refreshInflight.current = null;
    }
  }, []);

  const refreshBundle = refreshAll;

  useEffect(() => {
    let cancelled = false;

    if (!bundleCache) {
      loadBundle()
        .then((data) => {
          if (!cancelled) setBundle(data);
        })
        .catch((e) => {
          if (!cancelled) {
            setBundleError(e instanceof ApiError ? e.message : "Failed to load insights");
          }
        })
        .finally(() => {
          if (!cancelled) setBundleLoading(false);
        });
    }

    if (!trendsCache) {
      loadTrends()
        .then((data) => {
          if (!cancelled) setTrends(data);
        })
        .finally(() => {
          if (!cancelled) setTrendsLoading(false);
        });
    }

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function pollSynthesis() {
      try {
        const status = await fetchSynthesisStatus();
        if (cancelled) return;

        const inProgress = status.in_progress;
        if (synthesisWasInProgress.current && !inProgress) {
          await refreshAll();
        }
        synthesisWasInProgress.current = inProgress;
        setSynthesisInProgress(inProgress);
      } catch {
        /* backend may be unavailable */
      }
    }

    pollSynthesis();
    const id = setInterval(pollSynthesis, 4000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [refreshAll]);

  return (
    <InsightsDataContext.Provider
      value={{
        bundle,
        trends,
        bundleLoading,
        trendsLoading,
        bundleError,
        synthesisInProgress,
        dataGeneration,
        refreshAll,
        refreshBundle,
      }}
    >
      {children}
    </InsightsDataContext.Provider>
  );
}

export function useInsightsData(): InsightsDataContextValue {
  const ctx = useContext(InsightsDataContext);
  if (!ctx) {
    throw new Error("useInsightsData must be used within InsightsDataProvider");
  }
  return ctx;
}
