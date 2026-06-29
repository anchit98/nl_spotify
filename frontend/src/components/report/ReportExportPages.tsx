"use client";

import { SourceMixDonut } from "@/components/SourceMixDonut";
import { TrendsCharts } from "@/components/TrendsCharts";
import { GlassCard } from "@/components/ui";
import { SourceBadge, StarRating } from "@/components/QuoteCard";
import {
  QUESTION_IDS,
  RESEARCH_QUESTIONS,
  type InsightsBundle,
  type QuestionAnswer,
  type ReviewTrends,
} from "@/lib/types";
import {
  aggregateBySource,
  countAnsweredQuestions,
  formatDate,
  formatNumber,
  getThemes,
  starRatingDistribution,
} from "@/lib/utils";

const exportPageClass =
  "w-[1100px] bg-[#0a0a0b] text-on-surface p-10 box-border";

function ExportPageTitle({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-8 border-b border-border-subtle pb-6">
      <p className="text-[12px] uppercase tracking-wider text-primary font-semibold mb-2">
        Music Discovery Insights
      </p>
      <h1 className="text-[28px] font-semibold tracking-tight text-on-surface">{title}</h1>
      {subtitle && (
        <p className="text-[15px] text-on-surface-variant mt-2 max-w-3xl">{subtitle}</p>
      )}
    </div>
  );
}

export function HomeExportPage({ bundle }: { bundle: InsightsBundle }) {
  const { run, question_answers, executive_summary, dataset_stats } = bundle;
  const totalReviews = dataset_stats?.total_reviews ?? run.clean_items_analyzed ?? 0;
  const avgRating =
    dataset_stats?.discovery_avg_rating ?? dataset_stats?.store_avg_rating ?? dataset_stats?.avg_rating ?? null;
  const questionsAnswered = countAnsweredQuestions(question_answers);
  const bySource = dataset_stats?.by_source ?? aggregateBySource(question_answers);
  const themeCount = question_answers.reduce((n, a) => n + getThemes(a).length, 0);

  return (
    <div data-export-page className={exportPageClass}>
      <ExportPageTitle
        title="Executive Overview"
        subtitle={`${formatNumber(totalReviews)} reviews · Last updated ${formatDate(run.completed_at ?? run.started_at)}`}
      />

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Reviews", value: formatNumber(totalReviews) },
          { label: "Core Questions", value: `${questionsAnswered}/${QUESTION_IDS.length}` },
          { label: "Extracted Themes", value: String(themeCount) },
          { label: "Avg Rating", value: avgRating?.toFixed(1) ?? "—" },
        ].map((m) => (
          <GlassCard key={m.label} className="p-4">
            <p className="text-[12px] text-text-muted mb-1">{m.label}</p>
            <p className="text-[28px] font-semibold">{m.value}</p>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {executive_summary && (
          <GlassCard className="p-6 col-span-1">
            <h3 className="text-[18px] font-semibold mb-4">Executive Summary</h3>
            <div className="text-[14px] leading-relaxed text-on-surface-variant text-justify space-y-3">
              {executive_summary.summary_text
                .split(/\n\n+/)
                .filter((p) => p.trim())
                .map((p, i) => (
                  <p key={i}>{p.trim()}</p>
                ))}
            </div>
          </GlassCard>
        )}
        <GlassCard className="p-6 col-span-1">
          <SourceMixDonut bySource={bySource} total={totalReviews} title="Source Mix" />
        </GlassCard>
      </div>

      {executive_summary && executive_summary.top_pain_points.length > 0 && (
        <GlassCard className="p-6 mb-6">
          <h3 className="text-[18px] font-semibold mb-4">Top Pain Points</h3>
          <ul className="space-y-2 text-[14px] text-on-surface-variant list-disc pl-5">
            {executive_summary.top_pain_points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </GlassCard>
      )}

      <h3 className="text-[18px] font-semibold mb-4">Question Synthesis Overview</h3>
      <div className="grid grid-cols-2 gap-3">
        {QUESTION_IDS.map((id) => {
          const answer = question_answers.find((a) => a.question_id === id);
          const meta = RESEARCH_QUESTIONS[id];
          const top = answer ? getThemes(answer)[0] : null;
          return (
            <GlassCard key={id} className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-text-muted mb-1">
                Q{meta.order} · {meta.short}
              </p>
              <p className="text-[15px] font-medium text-on-surface">{meta.title}</p>
              {top && (
                <p className="text-[13px] text-secondary-container mt-2 line-clamp-2">
                  Top theme: {top.theme} (n={formatNumber(top.mention_count)})
                </p>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}

export function QuestionExportPage({ answer }: { answer: QuestionAnswer }) {
  const meta = RESEARCH_QUESTIONS[answer.question_id];
  const themes = getThemes(answer);
  const ratingDist = starRatingDistribution(answer.stats.rating_distribution);
  const maxRating = Math.max(...Object.values(ratingDist), 1);
  const quotes = (answer.evidence_quotes ?? []).slice(0, 6);

  return (
    <div data-export-page className={exportPageClass}>
      <ExportPageTitle
        title={`Q${meta.order}: ${meta.title}`}
        subtitle={answer.question_text}
      />

      <GlassCard className="p-6 mb-6">
        <h3 className="text-[13px] uppercase tracking-wider text-text-muted mb-3">
          Synthesized Answer
        </h3>
        <div className="text-[14px] leading-relaxed text-on-surface-variant space-y-3">
          {answer.answer_narrative.split("\n\n").map((p) => (
            <p key={p.slice(0, 48)}>{p}</p>
          ))}
        </div>
      </GlassCard>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <GlassCard className="p-6">
          <h3 className="text-[16px] font-semibold mb-4">Top Themes</h3>
          <div className="space-y-3">
            {themes.slice(0, 5).map((theme) => (
              <div key={theme.theme} className="border-b border-border-subtle pb-3 last:border-0">
                <div className="flex justify-between gap-2 mb-1">
                  <p className="text-[15px] font-medium text-on-surface">{theme.theme}</p>
                  <span className="text-[12px] text-text-muted shrink-0">
                    n={formatNumber(theme.mention_count)}
                  </span>
                </div>
                <p className="text-[13px] text-on-surface-variant">{theme.summary}</p>
              </div>
            ))}
          </div>
        </GlassCard>

        <div className="space-y-4">
          <GlassCard className="p-6 h-56 flex flex-col">
            <h3 className="text-[13px] text-text-muted mb-4">Rating distribution</h3>
            <div className="flex-1 flex items-end gap-2">
              {["1", "2", "3", "4", "5"].map((star) => {
                const count = ratingDist[star] ?? 0;
                const barHeight = maxRating
                  ? Math.max((count / maxRating) * 100, count > 0 ? 8 : 0)
                  : 0;
                return (
                  <div key={star} className="flex-1 flex flex-col items-center justify-end gap-1">
                    <span className="text-[10px] text-text-muted">{formatNumber(count)}</span>
                    <div
                      className={`w-full rounded-t ${
                        star <= "2"
                          ? "bg-status-error/80"
                          : star === "3"
                            ? "bg-status-warning/80"
                            : "bg-surface-container-highest"
                      }`}
                      style={{ height: `${barHeight}%`, minHeight: count > 0 ? "8px" : "0" }}
                    />
                    <span className="text-[10px] text-text-muted">{star}★</span>
                  </div>
                );
              })}
            </div>
          </GlassCard>
          <GlassCard className="p-6 h-56 flex flex-col min-w-0 overflow-hidden">
            <SourceMixDonut
              bySource={answer.stats.by_source ?? {}}
              total={answer.stats.total_mentions}
            />
          </GlassCard>
        </div>
      </div>

      <GlassCard className="p-6">
        <h3 className="text-[16px] font-semibold mb-4">User Quotes</h3>
        <div className="grid grid-cols-2 gap-3">
          {quotes.map((q, i) => (
            <div
              key={`${q.source}-${i}`}
              className="glass-panel p-4 rounded-lg border border-border-subtle"
            >
              <div className="flex items-center justify-between mb-2 gap-2">
                <SourceBadge source={q.source} />
                <StarRating rating={q.rating} />
              </div>
              <p className="text-[13px] leading-relaxed text-on-surface-variant line-clamp-5">
                &ldquo;{q.text}&rdquo;
              </p>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

export function TrendsExportPage({ trends }: { trends: ReviewTrends }) {
  return (
    <div data-export-page className={exportPageClass}>
      <ExportPageTitle
        title="Review Trends"
        subtitle={
          trends.range_start && trends.range_end
            ? `${formatDate(trends.range_start)} — ${formatDate(trends.range_end)} · ${formatNumber(trends.total_reviews)} reviews`
            : `Sentiment and average ratings across ${formatNumber(trends.total_reviews)} reviews`
        }
      />
      <div className="h-[420px]">
        <TrendsCharts initialTrends={trends} />
      </div>
    </div>
  );
}

export function ReportExportPages({
  bundle,
  trends,
}: {
  bundle: InsightsBundle;
  trends: ReviewTrends | null;
}) {
  const sortedAnswers = [...bundle.question_answers].sort(
    (a, b) =>
      RESEARCH_QUESTIONS[a.question_id].order - RESEARCH_QUESTIONS[b.question_id].order,
  );

  return (
    <>
      <HomeExportPage bundle={bundle} />
      {sortedAnswers.map((answer) => (
        <QuestionExportPage key={answer.question_id} answer={answer} />
      ))}
      {trends && trends.periods.length > 0 && <TrendsExportPage trends={trends} />}
    </>
  );
}
