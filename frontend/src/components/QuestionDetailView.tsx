"use client";

import Link from "next/link";
import { memo, useEffect, useMemo, useState, useTransition, type CSSProperties } from "react";
import { QuoteCard, QuoteModal } from "@/components/QuoteCard";
import { SourceMixDonut } from "@/components/SourceMixDonut";
import { GlassCard } from "@/components/ui";
import {
  RESEARCH_QUESTIONS,
  SOURCE_LABELS,
  type QuestionAnswer,
  type TopTheme,
} from "@/lib/types";
import {
  filterQuotes,
  formatNumber,
  getThemes,
  lowConfidenceSource,
  starRatingDistribution,
} from "@/lib/utils";

const SOURCES = ["google_play", "app_store", "reddit", "community_forum", "social_media"];

const QuoteList = memo(function QuoteList({
  quotes,
  onExpand,
}: {
  quotes: QuestionAnswer["evidence_quotes"];
  onExpand: (index: number) => void;
}) {
  if (quotes.length === 0) {
    return <p className="text-text-muted text-[15px]">No quotes match the current filters.</p>;
  }

  return (
    <>
      {quotes.map((q, i) => (
        <div key={`${q.source}-${q.text.slice(0, 24)}-${i}`} className="snap-center">
          <QuoteCard quote={q} onExpand={() => onExpand(i)} />
        </div>
      ))}
    </>
  );
});

export function QuestionDetailView({
  answer,
}: {
  answer: QuestionAnswer;
}) {
  const meta = RESEARCH_QUESTIONS[answer.question_id];
  const themes = getThemes(answer);
  const maxMentions = themes[0]?.mention_count ?? 1;

  const [selectedIdx, setSelectedIdx] = useState(0);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [lowRatingOnly, setLowRatingOnly] = useState(false);
  const [narrativeExpanded, setNarrativeExpanded] = useState(false);
  const [modalIndex, setModalIndex] = useState<number | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setSelectedIdx(0);
    setSourceFilter(null);
    setLowRatingOnly(false);
    setNarrativeExpanded(false);
    setModalIndex(null);
  }, [answer.question_id]);

  const selectedTheme: TopTheme | undefined = themes[selectedIdx];

  const quotes = answer.evidence_quotes ?? [];

  const filteredQuotes = useMemo(
    () => filterQuotes(quotes, sourceFilter, lowRatingOnly),
    [quotes, sourceFilter, lowRatingOnly],
  );

  const ratingDist = starRatingDistribution(answer.stats.rating_distribution);
  const maxRating = Math.max(...Object.values(ratingDist), 1);

  function copyText(text: string) {
    void navigator.clipboard.writeText(text);
  }

  function setSource(source: string | null) {
    startTransition(() => setSourceFilter(source));
  }

  function toggleLowRatingOnly() {
    startTransition(() => setLowRatingOnly((v) => !v));
  }

  return (
    <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-text-muted text-[13px] mb-2">
          <Link href="/" className="hover:text-primary transition-colors">
            Questions
          </Link>
          <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          <span className="text-on-surface">Q{meta.order} Details</span>
        </div>
        <h2 className="text-[24px] md:text-[32px] font-semibold tracking-tight text-on-surface max-w-3xl mb-4">
          {answer.question_text}
        </h2>

        <GlassCard className="p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4">
            <span className="material-symbols-outlined text-primary opacity-50">auto_awesome</span>
          </div>
          <h3 className="text-[13px] text-text-muted mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">summarize</span>
            Synthesized Answer
          </h3>
          <div
            className={`space-y-4 text-[15px] leading-relaxed text-on-surface-variant ${
              narrativeExpanded ? "" : "max-h-40 overflow-hidden relative"
            }`}
          >
            {answer.answer_narrative.split("\n\n").map((p) => (
              <p key={p.slice(0, 40)}>{p}</p>
            ))}
            {!narrativeExpanded && (
              <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-[#1C1C1E] to-transparent" />
            )}
          </div>
          <div className="flex gap-4 mt-4">
            <button
              type="button"
              onClick={() => setNarrativeExpanded((v) => !v)}
              className="text-primary text-[13px] flex items-center gap-1 hover:underline"
            >
              {narrativeExpanded ? "Collapse" : "Expand"} Synthesis
              <span className="material-symbols-outlined text-[16px]">expand_more</span>
            </button>
            <button
              type="button"
              onClick={() => copyText(answer.answer_narrative)}
              className="text-text-muted text-[13px] hover:text-primary"
            >
              Copy narrative
            </button>
          </div>
        </GlassCard>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 mb-8 items-start">
        <div className="w-full lg:w-[40%] flex flex-col gap-4">
          <div className="flex justify-between items-end">
            <h3 className="text-[20px] font-semibold">Top Themes</h3>
            <span className="text-[13px] text-text-muted">Sorted by mentions</span>
          </div>
          <div className="space-y-3 pr-2">
            {themes.length === 0 ? (
              <p className="text-text-muted text-[15px]">Not enough data for this question.</p>
            ) : (
              themes.map((theme, idx) => (
                <button
                  key={theme.theme}
                  type="button"
                  onClick={() => setSelectedIdx(idx)}
                  className={`glass-panel p-4 rounded-lg text-left w-full interactive-card relative overflow-hidden ${
                    selectedIdx === idx
                      ? "bg-surface-high border-l-2 border-l-primary"
                      : ""
                  }`}
                >
                  <div className="flex justify-between items-start mb-2 relative z-10 gap-2">
                    <p
                      className={`text-[18px] font-medium leading-snug pr-8 ${
                        selectedIdx === idx ? "text-on-surface" : "text-on-surface-variant"
                      }`}
                    >
                      {theme.theme}
                    </p>
                    <span
                      className={`text-[13px] shrink-0 px-2 py-1 rounded ${
                        selectedIdx === idx
                          ? "text-primary bg-primary/10"
                          : "text-text-muted bg-surface-container-highest"
                      }`}
                    >
                      {formatNumber(theme.mention_count)}
                    </span>
                  </div>
                  <div className={`absolute bottom-0 left-0 h-1 w-full ${selectedIdx === idx ? "bg-primary/20" : "bg-surface-container-highest"}`}>
                    <div
                      className={`h-full progress-bar-fill ${
                        selectedIdx === idx ? "bg-primary" : "bg-surface-tint opacity-50"
                      }`}
                      style={
                        {
                          "--target-width": `${(theme.mention_count / maxMentions) * 100}%`,
                        } as CSSProperties
                      }
                    />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        <GlassCard className="w-full lg:w-[60%] p-6 flex flex-col bg-surface-low h-fit">
          {selectedTheme ? (
            <>
              <p className="text-[12px] uppercase tracking-wider text-text-muted mb-2">
                Selected theme deep dive
              </p>
              <h3 className="text-[20px] font-semibold mb-4">{selectedTheme.theme}</h3>
              <p className="text-[15px] text-on-surface-variant mb-4">{selectedTheme.summary}</p>
              {selectedTheme.example_quote && (
                <div className="glass-panel p-6 rounded-lg bg-surface-high border-l-4 border-l-status-warning relative">
                  <span className="material-symbols-outlined absolute top-4 right-4 text-text-muted opacity-20 text-4xl">
                    format_quote
                  </span>
                  <p className="text-[15px] italic leading-relaxed pr-8">
                    &ldquo;{selectedTheme.example_quote}&rdquo;
                  </p>
                </div>
              )}
              <button
                type="button"
                onClick={() => copyText(selectedTheme.theme + "\n\n" + selectedTheme.summary)}
                className="mt-4 text-[13px] text-primary hover:underline self-start"
              >
                Copy theme
              </button>
            </>
          ) : (
            <p className="text-text-muted">Select a theme to see details.</p>
          )}
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <GlassCard className="p-6 h-64 flex flex-col">
          <h3 className="text-[13px] text-text-muted mb-4">Rating distribution</h3>
          <div className="flex-1 min-h-0 flex items-end gap-2">
            {["1", "2", "3", "4", "5"].map((star) => {
              const count = ratingDist[star] ?? 0;
              const barHeight = maxRating ? Math.max((count / maxRating) * 100, count > 0 ? 8 : 0) : 0;
              return (
                <button
                  key={star}
                  type="button"
                  onClick={() => startTransition(() => setLowRatingOnly(star <= "3"))}
                  className="flex-1 h-full flex flex-col items-center justify-end gap-1 group"
                  title={`${formatNumber(count)} reviews`}
                >
                  <span className="text-[11px] text-text-muted">{formatNumber(count)}</span>
                  <div
                    className={`w-full rounded-t transition-all ${
                      star <= "2" ? "bg-status-error/80" : star === "3" ? "bg-status-warning/80" : "bg-surface-container-highest"
                    }`}
                    style={{ height: `${barHeight}%`, minHeight: count > 0 ? "8px" : "0" }}
                  />
                  <span className="text-[11px] text-text-muted">{star}★</span>
                </button>
              );
            })}
          </div>
        </GlassCard>

        <GlassCard className="p-6 h-64 flex flex-col min-w-0 overflow-hidden">
          <SourceMixDonut
            bySource={answer.stats.by_source ?? {}}
            total={answer.stats.total_mentions}
            onSourceClick={setSource}
            activeSource={sourceFilter}
          />
        </GlassCard>
      </div>

      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <h3 className="text-[20px] font-semibold">User quotes</h3>
          <div className={`flex flex-wrap gap-2 ${isPending ? "opacity-80" : ""}`}>
            <button
              type="button"
              onClick={() => setSource(null)}
              className={`px-4 py-1.5 rounded-full text-[12px] font-semibold uppercase tracking-wider border transition-colors ${
                !sourceFilter
                  ? "bg-primary/10 text-primary border-primary"
                  : "bg-surface-low text-text-muted border-border-subtle hover:bg-surface-high"
              }`}
            >
              All Sources
            </button>
            {SOURCES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSource(s)}
                className={`px-4 py-1.5 rounded-full text-[12px] font-semibold uppercase tracking-wider border transition-colors ${
                  sourceFilter === s
                    ? "bg-primary/10 text-primary border-primary"
                    : "bg-surface-low text-text-muted border-border-subtle hover:bg-surface-high"
                }`}
              >
                {SOURCE_LABELS[s]}
                {lowConfidenceSource(answer.stats, s) && (
                  <span className="ml-1 text-status-warning" title="Low confidence sample">
                    !
                  </span>
                )}
              </button>
            ))}
            <div className="w-px h-6 bg-border-subtle mx-2 self-center hidden sm:block" />
            <button
              type="button"
              onClick={toggleLowRatingOnly}
              className={`px-4 py-1.5 rounded-full text-[12px] font-semibold uppercase tracking-wider border flex items-center gap-1 transition-colors ${
                lowRatingOnly
                  ? "bg-primary/10 text-primary border-primary"
                  : "bg-surface-low text-text-muted border-border-subtle hover:bg-surface-high"
              }`}
            >
              1–3 Stars <span className="material-symbols-outlined text-[14px]">star</span>
            </button>
          </div>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory">
          <QuoteList quotes={filteredQuotes} onExpand={setModalIndex} />
        </div>
      </div>

      {modalIndex != null && (
        <QuoteModal
          quotes={filteredQuotes}
          index={modalIndex}
          onClose={() => setModalIndex(null)}
          onNavigate={setModalIndex}
        />
      )}

    </div>
  );
}
