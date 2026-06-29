"use client";

import { SOURCE_LABELS, type EvidenceQuote } from "@/lib/types";

export function StarRating({ rating }: { rating?: number | null }) {
  if (rating == null) {
    return <span className="inline-block h-4 w-20 shrink-0" aria-hidden="true" />;
  }

  const stars = Math.max(1, Math.min(5, Math.round(rating)));
  return (
    <div className="flex text-status-warning text-[14px]">
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`material-symbols-outlined text-[16px] ${
            i <= stars ? "filled" : "text-surface-container-highest"
          }`}
        >
          star
        </span>
      ))}
    </div>
  );
}

export function SourceBadge({ source }: { source: string }) {
  const label = SOURCE_LABELS[source] ?? source;
  const icon =
    source === "google_play"
      ? "android"
      : source === "app_store"
        ? "phone_iphone"
        : source === "reddit"
          ? "forum"
          : "public";
  return (
    <span className="inline-flex items-center gap-1 text-[13px] text-text-muted">
      <span className="bg-surface-container-highest p-1 rounded">
        <span className="material-symbols-outlined text-[14px] text-primary">{icon}</span>
      </span>
      {label}
    </span>
  );
}

export function QuoteCard({
  quote,
  onExpand,
}: {
  quote: EvidenceQuote;
  onExpand?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onExpand}
      className="glass-panel rounded-lg p-4 text-left min-w-[280px] max-w-[360px] shrink-0 interactive-card"
    >
      <div className="flex items-center justify-between mb-3">
        <SourceBadge source={quote.source} />
        <StarRating rating={quote.rating} />
      </div>
      <p className="text-[15px] leading-relaxed text-on-surface line-clamp-4 italic">
        &ldquo;{quote.text}&rdquo;
      </p>
      {quote.posted_at && (
        <span className="text-[12px] text-text-muted mt-3 block">{quote.posted_at}</span>
      )}
    </button>
  );
}

export function QuoteModal({
  quotes,
  index,
  onClose,
  onNavigate,
}: {
  quotes: EvidenceQuote[];
  index: number;
  onClose: () => void;
  onNavigate: (next: number) => void;
}) {
  const quote = quotes[index];
  if (!quote) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
      role="dialog"
      aria-modal="true"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/75 backdrop-blur-md"
        onClick={onClose}
        aria-label="Close"
      />
      <div className="relative glass-panel rounded-2xl p-8 max-w-2xl w-full border border-border-subtle shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-text-muted hover:text-on-surface"
        >
          <span className="material-symbols-outlined">close</span>
        </button>
        <span className="material-symbols-outlined text-6xl text-text-muted/20 absolute top-4 left-6">
          format_quote
        </span>
        <div className="flex items-center gap-3 mb-6 mt-4">
          <SourceBadge source={quote.source} />
          <StarRating rating={quote.rating} />
        </div>
        <p className="text-xl md:text-2xl leading-relaxed text-on-surface italic relative z-10">
          &ldquo;{quote.text}&rdquo;
        </p>
        <div className="flex justify-between items-center mt-8 pt-4 border-t border-border-subtle">
          <button
            type="button"
            disabled={index <= 0}
            onClick={() => onNavigate(index - 1)}
            className="flex items-center gap-1 text-[13px] text-text-muted disabled:opacity-30 hover:text-primary"
          >
            <span className="material-symbols-outlined">chevron_left</span> Previous
          </button>
          <span className="text-[13px] text-text-muted">
            {index + 1} / {quotes.length}
          </span>
          <button
            type="button"
            disabled={index >= quotes.length - 1}
            onClick={() => onNavigate(index + 1)}
            className="flex items-center gap-1 text-[13px] text-text-muted disabled:opacity-30 hover:text-primary"
          >
            Next <span className="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </div>
    </div>
  );
}
