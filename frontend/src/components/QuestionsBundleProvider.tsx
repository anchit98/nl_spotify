"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useInsightsData } from "@/components/InsightsDataProvider";
import { EmptyState } from "@/components/ui";
import type { InsightsBundle } from "@/lib/types";

const BundleContext = createContext<InsightsBundle | null>(null);

export function QuestionsBundleProvider({ children }: { children: ReactNode }) {
  const { bundle, bundleLoading, bundleError } = useInsightsData();

  if (bundle) {
    return <BundleContext.Provider value={bundle}>{children}</BundleContext.Provider>;
  }

  if (bundleLoading) {
    return (
      <div className="p-6 md:p-10 space-y-4 max-w-[1600px] mx-auto">
        <div className="h-8 w-72 skeleton rounded-lg" />
        <div className="h-[480px] skeleton rounded-xl" />
      </div>
    );
  }

  return (
    <div className="p-10">
      <EmptyState
        icon="cloud_off"
        title="Cannot load questions"
        description={`${bundleError ?? "Backend unavailable"} Run Synthesize now from the home page when the API is available.`}
      />
    </div>
  );
}

export function useQuestionsBundle(): InsightsBundle {
  const bundle = useContext(BundleContext);
  if (!bundle) {
    throw new Error("useQuestionsBundle must be used within QuestionsBundleProvider");
  }
  return bundle;
}
