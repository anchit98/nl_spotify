"use client";

import Link from "next/link";
import { ExportReportButton } from "@/components/ExportReportButton";
import { SynthesizeButton } from "@/components/SynthesizeButton";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { EmptyState, GlassCard, PageHeader } from "@/components/ui";
import {
  QUESTION_IDS,
  RESEARCH_QUESTIONS,
  SOURCE_LABELS,
  type QuestionAnswer,
} from "@/lib/types";
import {
  aggregateBySource,
  countAnsweredQuestions,
  formatDate,
  formatNumber,
  getThemes,
} from "@/lib/utils";

function QuestionPreviewCard({ answer }: { answer: QuestionAnswer }) {
  const meta = RESEARCH_QUESTIONS[answer.question_id];
  const themes = getThemes(answer);
  const top = themes[0];

  return (
    <Link
      href={`/questions/${answer.question_id}`}
      prefetch
      className="bg-surface-low border border-border-subtle rounded-xl p-5 hover:bg-surface-high hover:-translate-y-1 hover-inner-glow transition-all duration-200 group flex flex-col h-full"
    >
      <div className="flex justify-between items-start mb-3">
        <span className="text-[12px] font-semibold uppercase tracking-wider text-text-muted bg-surface-dim px-2 py-1 rounded border border-border-subtle">
          Q{meta.order}
        </span>
        <span className="text-[13px] text-primary flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          Explore <span className="material-symbols-outlined text-[14px]">arrow_outward</span>
        </span>
      </div>
      <h4 className="text-[18px] font-medium leading-snug text-on-surface mb-2 line-clamp-2">
        {meta.title}
      </h4>
      <div className="mt-auto pt-4 flex items-end justify-between border-t border-border-subtle border-opacity-50">
        <div className="flex flex-col">
          <span className="text-[13px] text-text-muted mb-1">Top Theme</span>
          <span className="text-[14px] text-secondary-container line-clamp-1">
            &ldquo;{top ? top.theme : "No themes found"}&rdquo;
          </span>
        </div>
        {top && (
          <div className="bg-surface-dim px-2 py-1 rounded text-xs text-text-muted border border-border-subtle shrink-0 ml-2">
            n={formatNumber(top.mention_count)}
          </div>
        )}
      </div>
    </Link>
  );
}

export function HomeView() {
  const { bundle, bundleLoading, bundleError } = useInsightsData();

  if (bundleLoading && !bundle) {
    return (
      <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full space-y-4">
        <div className="h-10 w-64 skeleton rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 skeleton rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!bundle) {
    const message = bundleError ?? "Unable to load insights. Run Phase 3 synthesis first.";
    return (
      <div className="p-4 md:p-10 flex flex-col items-center justify-center min-h-[70vh]">
        <EmptyState
          icon="insights"
          title="No insights yet"
          description={message}
          action={<SynthesizeButton />}
        />
      </div>
    );
  }

  const { run, question_answers, executive_summary, dataset_stats } = bundle;
  const totalReviews = dataset_stats?.total_reviews ?? run.clean_items_analyzed ?? 0;
  const avgRating =
    dataset_stats?.discovery_avg_rating ?? dataset_stats?.store_avg_rating ?? dataset_stats?.avg_rating ?? null;
  const ratedCount =
    dataset_stats?.discovery_rated_count ??
    dataset_stats?.store_rated_count ??
    dataset_stats?.rated_review_count;
  const questionsAnswered = countAnsweredQuestions(question_answers);
  const bySource = dataset_stats?.by_source ?? aggregateBySource(question_answers);
  const totalSource = Object.values(bySource).reduce((a, b) => a + b, 0);
  const themeCount = question_answers.reduce((n, a) => n + getThemes(a).length, 0);
  const sortedAnswers = [...question_answers].sort(
    (a, b) =>
      RESEARCH_QUESTIONS[a.question_id].order - RESEARCH_QUESTIONS[b.question_id].order,
  );

  return (
    <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full">
      <PageHeader
        title="Music Discovery Insights"
        subtitle="Evidence from public user reviews & feedback."
        meta={
          <>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">forum</span>
              {formatNumber(totalReviews)} reviews
            </span>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">update</span>
              Last updated: {formatDate(run.completed_at ?? run.started_at)}
            </span>
          </>
        }
        actions={
          <div className="flex items-center gap-3">
            <ExportReportButton />
            <SynthesizeButton />
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        <div className="md:col-span-8 grid grid-cols-2 md:grid-cols-4 gap-4 items-stretch">
          {[
            { label: "Total Reviews", value: formatNumber(totalReviews), icon: "forum", sub: "Live count from database" },
            { label: "Core Questions", value: `${questionsAnswered}/${QUESTION_IDS.length}`, icon: "quiz", sub: questionsAnswered === QUESTION_IDS.length ? "Fully answered" : "Partial synthesis", highlight: "secondary" as const },
            { label: "Extracted Themes", value: String(themeCount), icon: "category", sub: "Across 6 categories" },
            { label: "Avg Rating", value: avgRating?.toFixed(1) ?? "—", icon: "star", sub: ratedCount ? `Discovery-related · ${formatNumber(ratedCount)} rated reviews` : "No ratings yet", highlight: avgRating != null && avgRating < 3.5 ? ("warning" as const) : undefined },
          ].map((m) => {
            const iconClass =
              m.highlight === "warning"
                ? "text-status-warning"
                : m.highlight === "secondary"
                  ? "text-secondary-container"
                  : "text-primary";
            const subClass =
              m.highlight === "warning"
                ? "text-status-error"
                : m.highlight === "secondary"
                  ? "text-on-surface-variant"
                  : "text-primary";

            return (
            <GlassCard key={m.label} className="p-5 flex flex-col h-full min-h-[148px] hover:bg-surface-high hover:-translate-y-0.5 hover-inner-glow transition-all duration-150 relative overflow-hidden">
              {m.highlight === "secondary" && (
                <div className="absolute right-0 top-0 w-24 h-24 bg-secondary-container/10 blur-xl rounded-full -translate-y-1/2 translate-x-1/4" />
              )}
              <div className="flex items-start justify-between gap-2 min-h-[40px] shrink-0 relative z-10">
                <span className="text-[13px] text-text-muted leading-tight">{m.label}</span>
                <span className={`material-symbols-outlined opacity-80 shrink-0 ${iconClass}`}>{m.icon}</span>
              </div>
              <div className="text-[32px] font-semibold text-on-surface leading-none tabular-nums h-9 flex items-end relative z-10">
                {m.value}
              </div>
              <p className={`text-[13px] mt-2 min-h-[2.75rem] line-clamp-2 leading-snug relative z-10 ${subClass}`}>
                {m.sub}
              </p>
            </GlassCard>
            );
          })}
        </div>

        <GlassCard className="md:col-span-4 p-6 relative overflow-hidden flex flex-col justify-between hover:bg-surface-high transition-colors">
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-primary text-[20px]">sync</span>
              <h3 className="text-[20px] font-semibold text-on-surface">Synthesis Status</h3>
            </div>
            <p className="text-[15px] text-on-surface-variant mb-6">
              The engine has ingested new reviews since the last full synthesis.
            </p>
          </div>
          <div className="flex items-center justify-between mt-auto">
            <div className="flex flex-col">
              <span className="text-[13px] text-text-muted">Engine Readiness</span>
              <span className="text-[12px] font-semibold uppercase tracking-wider text-primary flex items-center gap-2 mt-1">
                <span className="w-2 h-2 rounded-full bg-primary-container relative animate-pulse-ring" />
                Ready to Process
              </span>
            </div>
          </div>
        </GlassCard>

        {executive_summary && (
          <GlassCard className="md:col-span-6 p-6 flex flex-col hover-inner-glow transition-all">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[20px] font-semibold text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary-container text-[20px]">subject</span>
                Executive Summary
              </h3>
              <button type="button" className="text-on-surface-variant hover:text-on-surface p-1 rounded hover:bg-surface-high transition-colors" title="Copy Summary">
                <span className="material-symbols-outlined text-[18px]">content_copy</span>
              </button>
            </div>
            <div className="text-[15px] leading-relaxed text-on-surface-variant text-justify space-y-4 flex-1">
              {executive_summary.summary_text
                .split(/\n\n+/)
                .filter((p) => p.trim())
                .map((p, i) => (
                  <p key={i}>{p.trim()}</p>
                ))}
            </div>
          </GlassCard>
        )}

        <GlassCard className="md:col-span-6 p-6 flex flex-col hover-inner-glow transition-all">
          <h3 className="text-[20px] font-semibold text-on-surface flex items-center gap-2 mb-6">
            <span className="material-symbols-outlined text-primary text-[20px]">pie_chart</span>
            Source Mix
          </h3>
          <div className="flex-1 flex items-center gap-8">
            <div className="relative w-32 h-32 shrink-0">
              <div
                className="w-full h-full rounded-full"
                style={{
                  background: `conic-gradient(
                    var(--color-primary-container) 0% 45%, 
                    var(--color-secondary-container) 45% 75%, 
                    var(--color-surface-high) 75% 90%, 
                    var(--color-text-muted) 90% 100%
                  )`,
                }}
              />
              <div className="absolute inset-0 m-auto w-24 h-24 bg-surface-low rounded-full flex flex-col items-center justify-center border border-border-subtle shadow-inner">
                <span className="text-[13px] text-text-muted">Total</span>
                <span className="text-[20px] font-semibold text-on-surface leading-none">
                  {totalReviews >= 1000 ? `${(totalReviews / 1000).toFixed(1)}k` : formatNumber(totalReviews)}
                </span>
              </div>
            </div>
            <div className="flex-1 space-y-3">
              {Object.entries(bySource)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 4)
                .map(([source, count], i) => {
                  const pct = totalSource ? Math.round((count / totalSource) * 100) : 0;
                  const colors = ["bg-primary-container", "bg-secondary-container", "bg-surface-high border border-border-subtle", "bg-text-muted"];
                  return (
                    <div key={source} className="flex items-center justify-between group cursor-pointer">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-sm ${colors[i]}`} />
                        <span className="text-[15px] text-on-surface group-hover:text-primary-container transition-colors">
                          {SOURCE_LABELS[source] ?? source}
                        </span>
                      </div>
                      <span className="text-[13px] text-text-muted">{pct}% ({formatNumber(count)})</span>
                    </div>
                  );
                })}
            </div>
          </div>
        </GlassCard>

        <GlassCard className="col-span-1 md:col-span-12 p-6 hover-inner-glow transition-all">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-[20px] font-semibold text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-status-error text-[20px]">warning</span>
              Top Pain Points Ranking
            </h3>
            <span className="text-[13px] text-text-muted">By Mentions & Severity</span>
          </div>
          <div className="space-y-5">
            {(executive_summary?.top_pain_points ?? []).slice(0, 3).map((p, i) => {
              const width = 100 - i * 22;
              const impacts = ["High Impact", "Medium Impact", "Low Impact"];
              const colors = ["text-status-error", "text-status-warning", "text-text-muted"];
              const bgColors = ["bg-status-error", "bg-status-warning", "bg-surface-high border border-border-subtle"];
              return (
                <div key={p}>
                  <div className="flex justify-between text-[15px] mb-1">
                    <span className="text-on-surface">{p}</span>
                    <span className={`${colors[i]} font-medium`}>{impacts[i]}</span>
                  </div>
                  <div className="w-full bg-surface-dim h-2 rounded-full overflow-hidden border border-border-subtle">
                    <div className={`${bgColors[i]} h-full rounded-full`} style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>

        <div className="col-span-1 md:col-span-12 mt-4">
          <h2 className="text-[20px] font-semibold text-on-surface mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-text-muted">layers</span>
            Question Synthesis
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {QUESTION_IDS.map((id) => {
              const answer = sortedAnswers.find((a) => a.question_id === id);
              if (!answer) return null;
              return <QuestionPreviewCard key={id} answer={answer} />;
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
