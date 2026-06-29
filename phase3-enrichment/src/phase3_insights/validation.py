from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class KeyFinding(BaseModel):
    finding: str
    evidence: str


class TopTheme(BaseModel):
    theme: str
    mention_count: int = Field(ge=0)
    summary: str
    example_quote: str = ""

    @field_validator("theme", "summary")
    @classmethod
    def not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value

    @field_validator("theme")
    @classmethod
    def theme_is_explanatory(cls, value: str) -> str:
        if len(value.split()) < 8:
            raise ValueError("theme must be a full explanatory sentence, not a short label")
        return value


class QuestionAnswerResult(BaseModel):
    answer_narrative: str
    top_themes: list[TopTheme] = Field(default_factory=list, max_length=5)
    key_findings: list[KeyFinding] = Field(default_factory=list)
    top_pain_points: list[str] = Field(default_factory=list)
    top_opportunities: list[str] = Field(default_factory=list)

    @field_validator("answer_narrative")
    @classmethod
    def narrative_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer_narrative cannot be empty")
        return value.strip()


class ExecutiveSummaryResult(BaseModel):
    summary_text: str
    top_pain_points: list[str] = Field(default_factory=list, min_length=1, max_length=3)
    top_opportunities: list[str] = Field(default_factory=list, min_length=1, max_length=3)

    @field_validator("summary_text")
    @classmethod
    def summary_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary_text cannot be empty")
        sentences = [s.strip() for s in value.replace("\n", " ").split(".") if s.strip()]
        if len(sentences) < 4:
            raise ValueError("summary_text must be at least 4 sentences")
        return value

    @field_validator("top_pain_points", "top_opportunities")
    @classmethod
    def items_are_explanatory(cls, values: list[str]) -> list[str]:
        cleaned = [v.strip() for v in values if v.strip()]
        for item in cleaned:
            if len(item.split()) < 8:
                raise ValueError("each item must be a full explanatory sentence, not a short label")
        return cleaned
