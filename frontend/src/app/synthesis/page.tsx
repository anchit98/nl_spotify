"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { fetchSynthesisStatus } from "@/lib/api";
import type { PipelinePhase } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const STEPS: { id: PipelinePhase; label: string; detail: string }[] = [
  {
    id: "collecting",
    label: "Collecting feedback",
    detail: "Incremental pull since last successful run per source",
  },
  {
    id: "cleaning",
    label: "Cleaning new reviews",
    detail: "Process only newly collected raw items",
  },
  {
    id: "synthesizing",
    label: "Synthesizing insights",
    detail: "Re-analyze full corpus with Groq (~5–8 minutes)",
  },
];

function stepIndex(phase: PipelinePhase | null | undefined): number {
  if (!phase) return 0;
  const idx = STEPS.findIndex((s) => s.id === phase);
  return idx >= 0 ? idx + 1 : 0;
}

export default function SynthesisPage() {
  const router = useRouter();
  const { refreshAll } = useInsightsData();
  const [activeStep, setActiveStep] = useState(1);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [runDate, setRunDate] = useState<string | null>(null);

  useEffect(() => {
    const tick = async () => {
      try {
        const status = await fetchSynthesisStatus();
        if (status.started_at) {
          setRunDate(status.started_at);
        } else if (status.run?.started_at) {
          setRunDate(status.run.started_at);
        }
        if (status.message) {
          setStatusMessage(status.message);
        }
        if (status.phase) {
          setActiveStep(stepIndex(status.phase));
        } else if (status.in_progress) {
          setActiveStep(1);
        }
        if (!status.in_progress) {
          clearInterval(intervalId);
          await refreshAll();
          router.push("/");
          router.refresh();
        }
      } catch {
        /* keep polling */
      }
    };

    const intervalId = setInterval(tick, 4000);
    tick();
    return () => clearInterval(intervalId);
  }, [router, refreshAll]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-10">
      <div className="glass-panel rounded-2xl p-10 max-w-lg w-full text-center relative overflow-hidden">
        <div className="absolute -right-10 -top-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10">
          <svg className="w-20 h-20 mx-auto mb-6 animate-spin" viewBox="0 0 50 50">
            <circle
              className="opacity-20"
              cx="25"
              cy="25"
              r="20"
              fill="none"
              stroke="#1DB954"
              strokeWidth="4"
            />
            <circle
              cx="25"
              cy="25"
              r="20"
              fill="none"
              stroke="#1DB954"
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray="90, 150"
            />
          </svg>
          <h1 className="text-2xl font-semibold mb-2">Pipeline in progress</h1>
          <p className="text-[15px] text-on-surface-variant mb-8">
            Collecting new reviews, cleaning them, then synthesizing insights across the full dataset.
          </p>
          <div className="space-y-3 text-left mb-8">
            {STEPS.map((step, i) => {
              const stepNum = i + 1;
              const done = stepNum < activeStep;
              const current = stepNum === activeStep;
              return (
                <div
                  key={step.id}
                  className={`flex items-start gap-3 text-[14px] ${
                    done || current ? "text-primary" : "text-text-muted"
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px] shrink-0 mt-0.5">
                    {done ? "check_circle" : current ? "sync" : "radio_button_unchecked"}
                  </span>
                  <div>
                    <p className="font-medium">{step.label}</p>
                    <p className="text-[12px] text-text-muted mt-0.5">{step.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
          {statusMessage && (
            <p className="text-[13px] text-text-muted mb-4">{statusMessage}</p>
          )}
          {runDate && (
            <p className="text-[13px] text-text-muted mb-4">Started {formatDate(runDate)}</p>
          )}
          <Link href="/" className="text-[13px] text-primary hover:underline">
            Return to dashboard (pipeline continues in background)
          </Link>
        </div>
      </div>
    </div>
  );
}
