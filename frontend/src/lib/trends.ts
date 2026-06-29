import type { ReviewTrends, TrendGranularity } from "./types";

/** Earliest period shown on the trends chart x-axis. */
export const TRENDS_CHART_START_ISO = "2026-01-01T00:00:00Z";

const CHART_PERIOD_FLOOR: Record<TrendGranularity, string> = {
  week: "2026-W01",
  month: "2026-01",
  year: "2026",
};

/** Drop pre-2026 buckets so the chart x-axis always starts in Jan 2026. */
export function filterTrendsForChart(trends: ReviewTrends): ReviewTrends {
  const floor = CHART_PERIOD_FLOOR[trends.granularity];
  const periods = trends.periods.filter((p) => p.period >= floor);
  return {
    ...trends,
    periods,
    range_start: TRENDS_CHART_START_ISO,
    total_reviews: periods.reduce((sum, p) => sum + p.review_count, 0),
  };
}
