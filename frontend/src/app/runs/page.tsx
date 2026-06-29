"use client";

import Link from "next/link";
import { Fragment, useEffect, useState } from "react";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { PageHeader, GlassCard, EmptyState } from "@/components/ui";
import { ApiError, fetchRuns } from "@/lib/api";
import type { SynthesisRun } from "@/lib/types";
import { formatDate, formatNumber, runStatusColor } from "@/lib/utils";

export default function RunsPage() {
  const { dataGeneration } = useInsightsData();
  const [runs, setRuns] = useState<SynthesisRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compare, setCompare] = useState<string[]>([]);

  useEffect(() => {
    fetchRuns()
      .then((data) => setRuns(data.runs))
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Failed to load runs"),
      );
  }, [dataGeneration]);

  if (error) {
    return (
      <div className="p-10">
        <EmptyState icon="history" title="Cannot load run history" description={error} />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-10 max-w-[1600px] mx-auto w-full">
      <header className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
        <div>
          <h2 className="text-[24px] md:text-[32px] font-semibold tracking-tight text-on-surface mb-2">Run History</h2>
          <p className="text-[18px] font-medium leading-relaxed text-text-muted">Review past syntheses and monitor active background jobs.</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer group">
            <span className="text-[12px] font-semibold uppercase tracking-wider text-on-surface-variant group-hover:text-on-surface transition-colors">Compare Mode</span>
            <div className="relative inline-block w-10 h-6">
              <input
                className="peer sr-only"
                type="checkbox"
                checked={compareMode}
                onChange={(e) => {
                  setCompareMode(e.target.checked);
                  if (!e.target.checked) setCompare([]);
                }}
              />
              <div className="block w-full h-full bg-surface-container-high border border-border-subtle rounded-full peer-checked:bg-primary transition-colors" />
              <div className="absolute left-1 top-1 bg-on-surface w-4 h-4 rounded-full transition-transform peer-checked:translate-x-4 peer-checked:bg-on-primary-fixed" />
            </div>
          </label>
          {compareMode && (
            <button
              type="button"
              disabled={compare.length < 2}
              className="bg-surface-high border border-border-subtle text-on-surface text-[12px] font-semibold uppercase tracking-wider px-4 py-2 rounded-full hover:bg-surface-variant hover:border-primary/50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[14px]">compare_arrows</span>
              Compare Selected
            </button>
          )}
        </div>
      </header>

      <div className="bg-surface-low border border-border-subtle rounded-xl flex-1 overflow-hidden flex flex-col relative">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border-subtle bg-surface-container-lowest">
                {compareMode && (
                  <th className="py-4 border-r border-border-subtle/50 w-12 text-center">
                    <span className="sr-only">Select</span>
                  </th>
                )}
                <th className="text-[13px] text-text-muted py-4 px-6 font-medium whitespace-nowrap">Run ID / Date</th>
                <th className="text-[13px] text-text-muted py-4 px-6 font-medium">Status</th>
                <th className="text-[13px] text-text-muted py-4 px-6 font-medium text-right">Reviews Analyzed</th>
                <th className="text-[13px] text-text-muted py-4 px-6 font-medium text-right">Tokens Used</th>
                <th className="text-[13px] text-text-muted py-4 px-6 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {runs.map((run) => (
                <Fragment key={run.id}>
                  <tr className="hover:bg-surface-high transition-colors group">
                    {compareMode && (
                      <td className="py-4 border-r border-border-subtle/50 bg-surface-low group-hover:bg-surface-high text-center">
                        <input
                          type="checkbox"
                          disabled={run.status !== "success"}
                          checked={compare.includes(run.id)}
                          onChange={() =>
                            setCompare((prev) =>
                              prev.includes(run.id)
                                ? prev.filter((id) => id !== run.id)
                                : prev.length < 2
                                  ? [...prev, run.id]
                                  : [prev[1], run.id],
                            )
                          }
                          className="rounded border-border-subtle bg-surface-container-lowest checked:bg-primary checked:border-primary disabled:opacity-50"
                        />
                      </td>
                    )}
                    <td className="py-4 px-6">
                      <div className="flex flex-col">
                        <span className="text-[15px] text-on-surface">SYN-{run.id.slice(0, 5)}</span>
                        <span className="text-[13px] text-text-muted">{formatDate(run.started_at)}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-semibold uppercase tracking-wider ${
                          run.status === "success"
                            ? "bg-primary/10 border-primary/20 text-primary"
                            : run.status === "running"
                              ? "bg-secondary-container/10 border-secondary-container/20 text-secondary-container animate-pulse"
                              : "bg-status-error/10 border-status-error/20 text-status-error"
                        }`}
                      >
                        {run.status === "running" ? (
                          <span className="material-symbols-outlined text-[12px] animate-spin">sync</span>
                        ) : (
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              run.status === "success" ? "bg-primary" : "bg-status-error"
                            }`}
                          />
                        )}
                        {run.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right text-[13px] text-on-surface-variant">
                      {run.clean_items_analyzed ? formatNumber(run.clean_items_analyzed) : "--"}
                    </td>
                    <td className="py-4 px-6 text-right text-[13px] text-on-surface-variant">
                      {run.tokens_used ? formatNumber(run.tokens_used) : "--"}
                    </td>
                    <td className="py-4 px-6 text-right">
                      {run.status === "success" ? (
                        <Link
                          href={`/?run=${run.id}`}
                          className="inline-flex items-center gap-1 text-[12px] font-semibold uppercase tracking-wider text-on-surface-variant hover:text-primary transition-colors"
                        >
                          View Results
                          <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                        </Link>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setExpanded(expanded === run.id ? null : run.id)}
                          className="inline-flex items-center gap-1 text-[12px] font-semibold uppercase tracking-wider text-on-surface-variant hover:text-primary transition-colors"
                        >
                          Details
                          <span className="material-symbols-outlined text-[16px]">
                            {expanded === run.id ? "expand_less" : "expand_more"}
                          </span>
                        </button>
                      )}
                    </td>
                  </tr>
                  {expanded === run.id && (
                    <tr className="bg-surface-container-low">
                      <td colSpan={compareMode ? 6 : 5} className="p-6 text-[13px] text-on-surface-variant">
                        <p>Run ID: {run.id}</p>
                        <p>Completed: {formatDate(run.completed_at)}</p>
                        {run.error_message && (
                          <div className="mt-4 p-4 rounded-lg bg-status-error/10 border border-status-error/20">
                            <p className="text-status-error font-semibold mb-2">Error Details:</p>
                            <pre className="text-status-error/80 whitespace-pre-wrap font-mono text-[11px] overflow-x-auto">
                              {run.error_message}
                            </pre>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {compare.length === 2 && (
        <GlassCard className="mt-6 p-6">
          <h3 className="text-[16px] font-semibold mb-2">Comparing 2 runs</h3>
          <p className="text-[14px] text-text-muted">
            {formatDate(runs.find((r) => r.id === compare[0])?.started_at)} vs{" "}
            {formatDate(runs.find((r) => r.id === compare[1])?.started_at)}
          </p>
        </GlassCard>
      )}
    </div>
  );
}
