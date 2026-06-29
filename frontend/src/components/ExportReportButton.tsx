"use client";

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { ReportExportPages } from "@/components/report/ReportExportPages";
import { fetchTrends } from "@/lib/api";
import { exportPagesToPdf, reportFilename } from "@/lib/exportReport";
import type { ReviewTrends } from "@/lib/types";

export function ExportReportButton({ className = "" }: { className?: string }) {
  const { bundle, trends: cachedTrends } = useInsightsData();
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [renderExport, setRenderExport] = useState(false);
  const [trends, setTrends] = useState<ReviewTrends | null>(null);

  const runExport = useCallback(async (container: HTMLElement) => {
      const pages = Array.from(
        container.querySelectorAll<HTMLElement>("[data-export-page]"),
      );
      if (pages.length === 0) {
        throw new Error("No report pages to export");
      }
    await exportPagesToPdf(pages, reportFilename());
  }, []);

  async function handleExport() {
    if (!bundle || exporting) return;

    setError(null);
    setExporting(true);

    try {
      let trendsData = cachedTrends;
      if (!trendsData) {
        trendsData = await fetchTrends();
      }
      setTrends(trendsData);
      setRenderExport(true);

      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      });
      await document.fonts.ready;
      await new Promise((r) => setTimeout(r, 900));

      const container = document.getElementById("report-export-root");
      if (!container) {
        throw new Error("Export renderer failed to mount");
      }
      await runExport(container);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to export report");
    } finally {
      setRenderExport(false);
      setExporting(false);
    }
  }

  return (
    <>
      <div className={className}>
        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={!bundle || exporting}
          className="h-10 px-6 rounded-full border border-border-subtle bg-surface-low hover:bg-surface-high text-[12px] font-semibold uppercase tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {exporting ? (
            <>
              <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
              Exporting…
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[16px]">download</span>
              Export Report
            </>
          )}
        </button>
        {error && <p className="text-status-error text-[12px] mt-2">{error}</p>}
      </div>

      {renderExport &&
        bundle &&
        createPortal(
          <div
            id="report-export-root"
            aria-hidden
            className="fixed left-[-10000px] top-0 z-[-1] opacity-100 pointer-events-none"
          >
            <ReportExportPages bundle={bundle} trends={trends ?? cachedTrends} />
          </div>,
          document.body,
        )}
    </>
  );
}
