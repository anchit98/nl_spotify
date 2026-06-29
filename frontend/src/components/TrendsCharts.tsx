"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { GlassCard } from "@/components/ui";
import { ApiError, fetchTrends } from "@/lib/api";
import { filterTrendsForChart } from "@/lib/trends";
import type { ReviewTrends, TrendGranularity } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

const CHART_COLORS = {
  sentiment: "#53e076",
  rating: "#00f1fe",
  grid: "rgba(255,255,255,0.08)",
  axis: "#8e8e93",
};

const GRANULARITY_OPTIONS: { id: TrendGranularity; label: string }[] = [
  { id: "week", label: "Weekly" },
  { id: "month", label: "Monthly" },
  { id: "year", label: "Yearly" },
];

const GRANULARITY_SUBTITLE: Record<TrendGranularity, string> = {
  week: "Net sentiment (line) and average star rating (bars) per week",
  month: "Net sentiment (line) and average star rating (bars) per month",
  year: "Net sentiment (line) and average star rating (bars) per year",
};

type Props = {
  initialTrends?: ReviewTrends;
  refreshKey?: number;
};

export function TrendsCharts({ initialTrends, refreshKey = 0 }: Props) {
  const [granularity, setGranularity] = useState<TrendGranularity>(
    initialTrends?.granularity ?? "month",
  );
  const [trends, setTrends] = useState<ReviewTrends | null>(
    initialTrends ? filterTrendsForChart(initialTrends) : null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartReady, setChartReady] = useState(false);

  const monthTrendsRef = useRef(initialTrends);
  if (initialTrends?.granularity === "month") {
    monthTrendsRef.current = filterTrendsForChart(initialTrends);
  }

  useEffect(() => {
    const el = chartRef.current;
    if (!el) return;

    const update = () => {
      const ready = el.clientWidth > 0 && el.clientHeight > 0;
      setChartReady((prev) => (prev === ready ? prev : ready));
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (initialTrends) {
      setTrends(filterTrendsForChart(initialTrends));
      if (initialTrends.granularity === "month") {
        monthTrendsRef.current = filterTrendsForChart(initialTrends);
      }
    }
  }, [initialTrends, refreshKey]);

  useEffect(() => {
    if (
      granularity === "month" &&
      monthTrendsRef.current?.granularity === "month" &&
      refreshKey === 0
    ) {
      setTrends(monthTrendsRef.current);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchTrends(granularity)
      .then((data) => {
        if (!cancelled) {
          const filtered = filterTrendsForChart(data);
          setTrends(filtered);
          if (data.granularity === "month") {
            monthTrendsRef.current = filtered;
          }
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof ApiError ? e.message : "Failed to load trends");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [granularity, refreshKey]);

  const data =
    trends?.periods.map((p) => ({
      label: p.label,
      sentiment: p.sentiment_score ?? undefined,
      avgRating: p.avg_rating ?? undefined,
      reviews: p.review_count,
      rated: p.rated_count,
      positivePct: p.positive_pct,
      negativePct: p.negative_pct,
    })) ?? [];

  if (!trends && loading) {
    return (
      <GlassCard className="p-6">
        <div className="h-[420px] skeleton rounded-lg" />
      </GlassCard>
    );
  }

  if (!trends || data.length === 0) {
    return (
      <p className="text-text-muted text-[15px]">
        No dated reviews found. Trends appear once reviews have a posted date.
      </p>
    );
  }

  return (
    <GlassCard className="p-6">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-6">
        <div>
          <h3 className="text-[20px] font-semibold text-on-surface">Sentiment &amp; ratings</h3>
          <p className="text-[13px] text-text-muted mt-1">{GRANULARITY_SUBTITLE[granularity]}</p>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex flex-wrap gap-2">
            {GRANULARITY_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setGranularity(opt.id)}
                disabled={loading}
                className={`px-4 py-1.5 rounded-full text-[12px] font-semibold uppercase tracking-wider border transition-colors ${
                  granularity === opt.id
                    ? "bg-primary/10 text-primary border-primary"
                    : "bg-surface-low text-text-muted border-border-subtle hover:bg-surface-high"
                } disabled:opacity-60`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="text-[12px] text-text-muted uppercase tracking-wider shrink-0">
            {formatNumber(trends.total_reviews)} reviews
          </p>
        </div>
      </div>

      {error && <p className="text-status-error text-[13px] mb-4">{error}</p>}

      <div
        ref={chartRef}
        className={`h-[380px] w-full min-w-0 transition-opacity ${loading ? "opacity-50" : "opacity-100"}`}
      >
        {chartReady && (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart key={granularity} data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: CHART_COLORS.axis, fontSize: 11 }}
                axisLine={{ stroke: CHART_COLORS.grid }}
                tickLine={false}
                interval="preserveStartEnd"
                minTickGap={24}
              />
              <YAxis
                yAxisId="sentiment"
                domain={[-100, 100]}
                tick={{ fill: CHART_COLORS.sentiment, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}%`}
                label={{
                  value: "Sentiment",
                  angle: -90,
                  position: "insideLeft",
                  fill: CHART_COLORS.sentiment,
                  fontSize: 11,
                  offset: 10,
                }}
              />
              <YAxis
                yAxisId="rating"
                orientation="right"
                domain={[1, 5]}
                ticks={[1, 2, 3, 4, 5]}
                tick={{ fill: CHART_COLORS.rating, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                label={{
                  value: "Avg rating",
                  angle: 90,
                  position: "insideRight",
                  fill: CHART_COLORS.rating,
                  fontSize: 11,
                  offset: 10,
                }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const row = payload[0]?.payload as (typeof data)[0];
                  return (
                    <div className="glass-panel rounded-lg px-3 py-2 border border-border-subtle text-[13px]">
                      <p className="text-on-surface font-medium mb-2">{label}</p>
                      <p style={{ color: CHART_COLORS.sentiment }}>
                        Net sentiment:{" "}
                        {row.sentiment != null ? `${row.sentiment.toFixed(1)}%` : "—"}
                      </p>
                      <p style={{ color: CHART_COLORS.rating }}>
                        Avg rating: {row.avgRating != null ? row.avgRating.toFixed(2) : "—"}
                      </p>
                      <p className="text-text-muted mt-1">
                        {formatNumber(row.rated)} rated / {formatNumber(row.reviews)} total
                      </p>
                    </div>
                  );
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: CHART_COLORS.axis, paddingTop: 12 }} />
              <ReferenceLine
                yAxisId="sentiment"
                y={0}
                stroke={CHART_COLORS.axis}
                strokeDasharray="4 4"
              />
              <Bar
                yAxisId="rating"
                dataKey="avgRating"
                name="Avg rating"
                fill={CHART_COLORS.rating}
                fillOpacity={0.35}
                stroke={CHART_COLORS.rating}
                strokeWidth={1}
                radius={[4, 4, 0, 0]}
                maxBarSize={granularity === "week" ? 24 : 40}
              />
              <Line
                yAxisId="sentiment"
                type="monotone"
                dataKey="sentiment"
                name="Net sentiment"
                stroke={CHART_COLORS.sentiment}
                strokeWidth={2.5}
                dot={{ r: granularity === "year" ? 5 : 4, fill: CHART_COLORS.sentiment, strokeWidth: 0 }}
                activeDot={{ r: 6 }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="text-[12px] text-text-muted mt-4">
        Sentiment: 4–5★ positive · 3★ neutral · 1–2★ negative. Unrated reviews are excluded from
        sentiment and rating averages but included in volume.
      </p>
    </GlassCard>
  );
}
