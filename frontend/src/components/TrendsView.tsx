"use client";

import { TrendsCharts } from "@/components/TrendsCharts";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { EmptyState, PageHeader } from "@/components/ui";
import { formatDate } from "@/lib/utils";

export function TrendsView() {
  const { trends, trendsLoading, dataGeneration } = useInsightsData();

  if (trendsLoading && !trends) {
    return (
      <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full space-y-4">
        <div className="h-10 w-48 skeleton rounded-lg" />
        <div className="h-80 skeleton rounded-xl" />
      </div>
    );
  }

  if (!trends || trends.periods.length === 0) {
    return (
      <div className="p-4 md:p-10">
        <PageHeader
          title="Review Trends"
          subtitle="Sentiment and rating movement across the review corpus."
        />
        <EmptyState
          icon="trending_up"
          title="No trend data yet"
          description="Reviews need a posted date to appear on the timeline. Data updates automatically as new reviews are ingested."
        />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full">
      <PageHeader
        title="Review Trends"
        subtitle="Live sentiment and average ratings from Jan 2026 onward — timeline extends through the current week."
        meta={
          trends.data_through ? (
            <span className="text-text-muted text-[13px]">
              Review data through {formatDate(trends.data_through)}
              {trends.range_end && trends.data_through !== trends.range_end
                ? ` · chart through ${formatDate(trends.range_end)}`
                : ""}
            </span>
          ) : undefined
        }
      />
      <TrendsCharts key={dataGeneration} refreshKey={dataGeneration} initialTrends={trends} />
    </div>
  );
}
