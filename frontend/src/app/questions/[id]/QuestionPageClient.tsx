"use client";

import { notFound } from "next/navigation";
import { use } from "react";
import { QuestionDetailView } from "@/components/QuestionDetailView";
import { useQuestionsBundle } from "@/components/QuestionsBundleProvider";
import { EmptyState } from "@/components/ui";
import { QUESTION_IDS } from "@/lib/types";

export function QuestionPageClient({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const bundle = useQuestionsBundle();

  if (!QUESTION_IDS.includes(id)) notFound();

  const answer = bundle.question_answers.find((a) => a.question_id === id);
  if (!answer) {
    return (
      <div className="p-10">
        <EmptyState
          icon="help"
          title="Not enough data"
          description="This question has no answers in the latest synthesis run. Run Synthesize now from the home page."
        />
      </div>
    );
  }

  return <QuestionDetailView answer={answer} />;
}
