"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { ApiError, triggerSynthesis } from "@/lib/api";

type Props = {
  className?: string;
  compact?: boolean;
  fullWidth?: boolean;
};

export function SynthesizeButton({ className = "", compact = false, fullWidth = false }: Props) {
  const router = useRouter();
  const { synthesisInProgress } = useInsightsData();
  const [, startTransition] = useTransition();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (synthesisInProgress || loading) return;
    setError(null);
    setLoading(true);
    try {
      await triggerSynthesis();
      startTransition(() => router.push("/synthesis"));
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        startTransition(() => router.push("/synthesis"));
      } else {
        setError(e instanceof Error ? e.message : "Failed to start synthesis");
      }
    } finally {
      setLoading(false);
    }
  }

  const disabled = synthesisInProgress || loading;

  return (
    <div className={className}>
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        title={synthesisInProgress ? "Synthesis in progress" : undefined}
        className={`rounded-full bg-primary-container text-on-primary-container text-[12px] font-semibold uppercase tracking-wider hover:bg-primary transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(29,185,84,0.3)] disabled:opacity-60 disabled:cursor-not-allowed ${
          compact ? "h-9 px-4" : "h-10 px-6"
        } ${fullWidth ? "w-full py-3" : ""}`}
      >
        <span className="material-symbols-outlined text-[18px] filled">
          {synthesisInProgress ? "sync" : "auto_awesome"}
        </span>
        {synthesisInProgress ? "Synthesizing…" : loading ? "Starting…" : "Synthesize now"}
      </button>
      {error && <p className="text-status-error text-[13px] mt-2">{error}</p>}
    </div>
  );
}
