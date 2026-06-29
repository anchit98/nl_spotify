from __future__ import annotations

import argparse
import sys
import traceback

from phase3_insights.aggregation import build_bundles
from phase3_insights.config import Settings
from phase3_insights.db import Database
from phase3_insights.groq_client import GroqClient, GroqError
from phase3_insights.preflight import run_preflight
from phase3_insights.prompts import build_executive_summary_prompt, build_question_prompt
from phase3_insights.questions import RESEARCH_QUESTIONS
from phase3_insights.rate_limiter import GroqDailyBudgetExceeded, GroqRateLimiter
from phase3_insights.validation import ExecutiveSummaryResult, QuestionAnswerResult, TopTheme
from pydantic import ValidationError


def run_synthesis(*, probe: bool = False) -> None:
    settings = Settings.from_env()
    run_preflight(settings)

    db = Database(settings)
    daily_requests, daily_tokens = db.get_daily_usage()
    rate_limiter = GroqRateLimiter(
        settings.groq_limits,
        daily_requests=daily_requests,
        daily_tokens=daily_tokens,
        safety_margin=settings.rate_limit_safety_margin,
    )
    groq = GroqClient(settings, rate_limiter)

    if not rate_limiter.can_complete_synthesis_run():
        print(
            f"Insufficient Groq quota for a full synthesis run today. {rate_limiter.summary()}",
            flush=True,
        )
        sys.exit(0)

    print(f"Model: {settings.groq_model}", flush=True)
    print(f"Groq usage today (before run): {rate_limiter.summary()}", flush=True)

    clean_items = db.fetch_all_clean_items()
    if not clean_items:
        print("No clean items found. Run Phase 2 cleaning first.", flush=True)
        sys.exit(1)

    if probe:
        clean_items = clean_items[:200]
        print(f"Probe mode: aggregating {len(clean_items)} clean items", flush=True)
    else:
        print(f"Aggregating {len(clean_items)} clean items in Python (no Groq cost)", flush=True)

    bundles = build_bundles(clean_items)
    question_ids = list(RESEARCH_QUESTIONS.keys())
    if probe:
        question_ids = question_ids[:2]

    run_id = db.start_run(
        metadata={
            "probe": probe,
            "model": settings.groq_model,
            "clean_items": len(clean_items),
        }
    )

    tokens_used = 0
    answers_for_summary: list[dict] = []
    questions_answered = 0
    groq_calls = 0

    try:
        for qid in question_ids:
            if not rate_limiter.can_make_request():
                print(f"Daily quota reached before {qid}. {rate_limiter.summary()}", flush=True)
                break

            bundle = bundles[qid]
            print(
                f"Synthesizing {qid}: {bundle.stats.total_mentions} mentions, "
                f"{len(bundle.quotes)} quotes, {len(bundle.theme_counts)} themes",
                flush=True,
            )

            if bundle.stats.total_mentions == 0:
                result = QuestionAnswerResult(
                    answer_narrative=(
                        f"No reviews in the current dataset matched topics for this question "
                        f"({bundle.question_text}). Re-run after more data is collected or "
                        f"broaden Phase 2 topic filters."
                    ),
                    top_themes=[],
                    key_findings=[],
                )
                tokens = 0
            else:
                completion = groq.complete_json(build_question_prompt(bundle))
                result = QuestionAnswerResult.model_validate(completion.data)
                if not result.top_themes and bundle.theme_counts:
                    result = QuestionAnswerResult(
                        **result.model_dump(exclude={"top_themes"}),
                        top_themes=[
                            TopTheme(
                                theme=t.label,
                                mention_count=t.mention_count,
                                summary=(
                                    f"This came up in {t.mention_count} reviews."
                                    + (
                                        f' For example: "{t.sample_quotes[0]["text"][:120]}"'
                                        if t.sample_quotes
                                        else ""
                                    )
                                ),
                                example_quote=(
                                    t.sample_quotes[0]["text"] if t.sample_quotes else ""
                                ),
                            )
                            for t in bundle.theme_counts[:5]
                        ],
                    )
                tokens = completion.tokens_used
                tokens_used += tokens

            db.save_question_answer(
                run_id,
                {
                    "question_id": qid,
                    "question_text": bundle.question_text,
                    "answer_narrative": result.answer_narrative,
                    "top_themes": [t.model_dump() for t in result.top_themes],
                    "key_findings": [f.model_dump() for f in result.key_findings],
                    "evidence_quotes": [q.to_dict() for q in bundle.quotes],
                    "stats": bundle.stats.to_dict(),
                    "model_version": settings.groq_model,
                },
            )
            answers_for_summary.append(
                {
                    "question_id": qid,
                    "question": bundle.question_text,
                    "answer": result.answer_narrative,
                    "top_themes": [t.model_dump() for t in result.top_themes],
                    "stats": bundle.stats.to_dict(),
                }
            )
            questions_answered += 1
            groq_calls += 1

        if (
            not probe
            and not settings.skip_executive_summary
            and questions_answered == len(RESEARCH_QUESTIONS)
            and rate_limiter.can_make_request()
        ):
            print("Synthesizing executive summary...", flush=True)
            completion = groq.complete_json(build_executive_summary_prompt(answers_for_summary))
            summary = ExecutiveSummaryResult.model_validate(completion.data)
            tokens_used += completion.tokens_used
            db.save_executive_summary(
                run_id,
                {
                    "summary_text": summary.summary_text,
                    "top_pain_points": summary.top_pain_points,
                    "top_opportunities": summary.top_opportunities,
                    "model_version": settings.groq_model,
                },
            )
            groq_calls += 1

        status = "success" if questions_answered > 0 else "failed"
        db.finish_run(
            run_id,
            status,
            len(clean_items),
            questions_answered,
            tokens_used,
            metadata={"probe": probe, "groq_calls": groq_calls},
        )
        print(
            f"Synthesis complete. Clean items: {len(clean_items)}, "
            f"Questions answered: {questions_answered}, Groq calls: {groq_calls}, tokens: {tokens_used}. "
            f"Quota after run: {rate_limiter.summary()}",
            flush=True,
        )

    except (GroqDailyBudgetExceeded, GroqError, ValidationError) as exc:
        err = traceback.format_exc()
        db.finish_run(
            run_id,
            "failed",
            len(clean_items),
            questions_answered,
            tokens_used,
            error_message=str(exc) + "\n" + err,
        )
        print(f"Synthesis failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3: Insight synthesis (SQL + Groq)")
    parser.add_argument("--probe", action="store_true", help="2 questions, 200 clean items max")
    args = parser.parse_args()
    run_synthesis(probe=args.probe)
