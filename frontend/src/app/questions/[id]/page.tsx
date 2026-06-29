import { QuestionPageClient } from "./QuestionPageClient";
import { QUESTION_IDS } from "@/lib/types";

export function generateStaticParams() {
  return QUESTION_IDS.map((id) => ({ id }));
}

export default function QuestionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <QuestionPageClient params={params} />;
}
