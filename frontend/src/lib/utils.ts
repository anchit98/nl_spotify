import { QUESTION_IDS, type QuestionAnswer, type QuestionStats, type TopTheme } from "./types";

export function getThemes(answer: QuestionAnswer): TopTheme[] {
  return (
    answer.top_themes ??
    answer.stats?.top_themes ??
    []
  );
}

export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function avgRatingAcross(answers: QuestionAnswer[]): number | null {
  const ratings = answers
    .map((a) => a.stats?.avg_rating)
    .filter((r): r is number => r != null);
  if (!ratings.length) return null;
  return Math.round((ratings.reduce((s, r) => s + r, 0) / ratings.length) * 10) / 10;
}

export function aggregateBySource(
  answers: QuestionAnswer[],
): Record<string, number> {
  const totals: Record<string, number> = {};
  for (const answer of answers) {
    const bySource = answer.stats?.by_source ?? {};
    for (const [source, count] of Object.entries(bySource)) {
      totals[source] = (totals[source] ?? 0) + count;
    }
  }
  return totals;
}

export function filterQuotes(
  quotes: QuestionAnswer["evidence_quotes"],
  source: string | null,
  lowRatingOnly: boolean,
) {
  return quotes.filter((q) => {
    if (source && q.source !== source) return false;
    if (lowRatingOnly && (q.rating == null || q.rating > 3)) return false;
    return true;
  });
}

export function lowConfidenceSource(stats: QuestionStats, source: string): boolean {
  const count = stats.by_source?.[source] ?? 0;
  return count > 0 && count < 20;
}

export function starRatingDistribution(
  distribution: Record<string, number> | undefined,
): Record<string, number> {
  const stars = ["1", "2", "3", "4", "5"];
  return Object.fromEntries(
    stars.map((star) => [star, Number(distribution?.[star] ?? 0)]),
  );
}

export function countAnsweredQuestions(answers: QuestionAnswer[]): number {
  return answers.filter((a) => QUESTION_IDS.includes(a.question_id)).length;
}

export function runStatusColor(status: string): string {
  switch (status) {
    case "success":
      return "text-primary";
    case "running":
      return "text-status-warning";
    case "failed":
      return "text-status-error";
    default:
      return "text-text-muted";
  }
}
