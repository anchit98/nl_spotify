export const RESEARCH_QUESTIONS: Record<
  string,
  { short: string; title: string; order: number }
> = {
  q1_discovery_barriers: {
    order: 1,
    short: "Discovery barriers",
    title: "Why do users struggle to discover new music?",
  },
  q2_recommendation_frustrations: {
    order: 2,
    short: "Recommendation frustrations",
    title: "What are the most common frustrations with recommendations?",
  },
  q3_listening_goals: {
    order: 3,
    short: "Listening goals",
    title: "What listening behaviors are users trying to achieve?",
  },
  q4_repetitive_listening: {
    order: 4,
    short: "Repetitive listening",
    title: "What causes users to repeatedly listen to the same content?",
  },
  q5_segment_differences: {
    order: 5,
    short: "Segment differences",
    title: "Which user segments experience different discovery challenges?",
  },
  q6_unmet_needs: {
    order: 6,
    short: "Unmet needs",
    title: "What unmet needs emerge consistently across reviews?",
  },
};

export const QUESTION_IDS = Object.keys(RESEARCH_QUESTIONS).sort(
  (a, b) => RESEARCH_QUESTIONS[a].order - RESEARCH_QUESTIONS[b].order,
);

export const SOURCE_LABELS: Record<string, string> = {
  google_play: "Google Play",
  app_store: "App Store",
  reddit: "Reddit",
  community_forum: "Community Forum",
  social_media: "Social Media",
  unknown: "Unknown",
};

export interface TopTheme {
  theme: string;
  mention_count: number;
  summary: string;
  example_quote?: string;
}

export interface EvidenceQuote {
  text: string;
  source: string;
  rating?: number | null;
  posted_at?: string | null;
}

export interface QuestionStats {
  total_mentions?: number;
  avg_rating?: number | null;
  low_rating_count?: number;
  by_source?: Record<string, number>;
  rating_distribution?: Record<string, number>;
  top_themes?: TopTheme[];
}

export interface QuestionAnswer {
  id: string;
  question_id: string;
  question_text: string;
  answer_narrative: string;
  key_findings: { finding: string; evidence: string }[];
  top_themes?: TopTheme[];
  evidence_quotes: EvidenceQuote[];
  stats: QuestionStats;
  model_version: string;
}

export interface ExecutiveSummary {
  summary_text: string;
  top_pain_points: string[];
  top_opportunities: string[];
  model_version: string;
}

export type PipelinePhase = "collecting" | "cleaning" | "synthesizing";

export interface SynthesisStatus {
  in_progress: boolean;
  phase: PipelinePhase | null;
  message: string | null;
  started_at: string | null;
  run: SynthesisRun | null;
}

export interface SynthesisRun {
  id: string;
  started_at: string;
  completed_at?: string | null;
  status: string;
  clean_items_analyzed?: number;
  questions_answered?: number;
  tokens_used?: number;
  error_message?: string | null;
  metadata?: Record<string, unknown>;
}

export interface DatasetStats {
  total_reviews: number;
  avg_rating?: number | null;
  rated_review_count?: number;
  discovery_review_count?: number;
  discovery_avg_rating?: number | null;
  discovery_rated_count?: number;
  store_avg_rating?: number | null;
  store_rated_count?: number;
  rating_distribution?: Record<string, number>;
  by_source?: Record<string, number>;
}

export interface InsightsBundle {
  run: SynthesisRun;
  question_answers: QuestionAnswer[];
  executive_summary: ExecutiveSummary | null;
  dataset_stats?: DatasetStats;
}

export interface ReviewTrendPeriod {
  period: string;
  label: string;
  review_count: number;
  rated_count: number;
  avg_rating: number | null;
  sentiment_score: number | null;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
}

export type TrendGranularity = "week" | "month" | "year";

export interface ReviewTrends {
  granularity: TrendGranularity;
  range_start: string | null;
  range_end: string | null;
  /** Latest review post date present in the corpus (may be before range_end). */
  data_through?: string | null;
  total_reviews: number;
  skipped_no_date: number;
  periods: ReviewTrendPeriod[];
}

export interface PmBuddyChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface PmBuddyChatResponse {
  reply: string;
  tokens_used: number;
  context_snapshot: {
    total_reviews?: number;
    repetitive_mention_count?: number;
    synthesis_run_id?: string | null;
  };
}
