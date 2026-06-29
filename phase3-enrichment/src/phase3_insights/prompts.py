from __future__ import annotations

import json

from phase3_insights.questions import QuestionBundle

SYSTEM_PROMPT = """You are a senior user-research analyst for Spotify music discovery.
You write in plain English that any product manager can understand — no jargon, no analyst shorthand.
Use ONLY the statistics and quotes provided — do not invent data.
Every claim must be supported by the stats or a quoted review.
Return ONLY valid JSON."""


def build_question_prompt(bundle: QuestionBundle) -> str:
    payload = json.dumps(bundle.to_dict(), indent=2)
    return f"""Answer this research question using the aggregated data below.

Question: {bundle.question_text}

Aggregated data (stats + sample quotes):
{payload}

Return JSON:
{{
  "answer_narrative": "<2-4 paragraphs answering the question in plain English>",
  "top_themes": [
    {{
      "theme": "<one clear sentence in plain English explaining what users mean — not a 3-word label; use the computed_themes label as a starting point and refine it>",
      "mention_count": <integer from computed_themes — do not invent counts>,
      "summary": "<one extra sentence adding a concrete detail from the quotes or stats, if helpful>",
      "example_quote": "<verbatim quote from sample_quotes or quotes, or empty if none>"
    }}
  ],
  "key_findings": [
    {{"finding": "<short finding>", "evidence": "<count or quote reference>"}}
  ],
  "top_pain_points": ["<only for frustration/discovery questions, else empty>"],
  "top_opportunities": ["<actionable opportunities, else empty>"]
}}

Rules:
- Return exactly 5 top_themes when computed_themes has 5+ themes; otherwise return all themes from computed_themes
- Order top_themes by mention_count descending (most common first)
- Each theme must be a full sentence a non-technical reader understands on its own (roughly 12–30 words)
- Use computed_themes counts as the source of truth for mention_count
- Do not shorten themes to title-case labels like "Poor recommendation quality" — explain what users actually experience
- Cite specific numbers from stats
- Reference at least 2 real user quotes verbatim where possible
- If sample is small or segment data is thin, say so explicitly
- Do not fabricate artists, features, or statistics"""


def build_executive_summary_prompt(answers: list[dict]) -> str:
    condensed = json.dumps(answers, indent=2)
    return f"""Synthesize an executive summary across all six research questions below.

Each question already has a Groq-generated narrative, top themes, and stats. Your job is to
integrate those findings into one cohesive leadership brief — not to repeat each question
verbatim, but to surface cross-cutting patterns, tensions, and priorities.

Question answers (narratives + themes + stats):
{condensed}

Return JSON:
{{
  "summary_text": "<2-4 paragraphs in plain English, separated by blank lines (use \\n\\n between paragraphs). Paragraph 1: headline insight across all questions with cited review counts. Paragraph 2: the biggest user frustrations and where they overlap. Paragraph 3: what users value and where discovery works. Paragraph 4 (optional): segment differences or unmet needs worth acting on.>",
  "top_pain_points": [
    "<full sentence describing a cross-cutting pain point — not a 3-word label; cite mention counts or sources where possible>"
  ],
  "top_opportunities": [
    "<full sentence describing an actionable product opportunity grounded in the evidence>"
  ]
}}

Rules:
- Write for a non-technical product leader — no jargon, no analyst shorthand
- Use ONLY the provided narratives, themes, and stats — do not invent data
- Cite specific numbers from stats (mentions, ratings, source counts) in summary_text
- Return exactly 3 top_pain_points and 3 top_opportunities, ordered by impact
- Each pain point and opportunity must be a complete sentence (12+ words)
- summary_text must be at least 4 sentences across 2+ paragraphs
- Do not list questions as Q1/Q2 — synthesize themes across the whole dataset"""


def extract_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)
