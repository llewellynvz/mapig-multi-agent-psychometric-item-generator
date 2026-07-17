"""Qualitative question generator: open-ended cognitive-interview probes.

Generates 5-10 open-ended questions grounded in the facet mapping and
evidence, for construct pre-testing interviews alongside the quantitative
items. Self-contained quality gate: an LLM critique-and-revise pass against
the open-ended-question rubric, then deterministic post-checks (question mark,
no Likert stems, no closed yes/no openers outside the standard probe-stem
whitelist). Dropped questions are surfaced as warnings, never hidden.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import (
    EvidenceChunk,
    FacetMapperResponse,
    QualitativeQuestion,
    UserRequest,
)
from backend.settings import settings

logger = logging.getLogger("mapig.qualitative_generator")

PROBE_TYPES = ("comprehension", "elaboration", "example", "contrast", "process")

_YES_NO_OPENER = re.compile(
    r"^(do|does|did|is|are|was|were|have|has|had|will|would|can|could|should|shall|may|might)\b",
    re.IGNORECASE,
)
_OPEN_PROBE_WHITELIST = re.compile(
    r"^(can|could|would|may|might)\s+you\s*(,[^,?]{1,40},)?\s*(please\s+)?"
    r"(describe|tell|explain|walk\s+(me|us)\s+through|talk\s+about|share|elaborate)\b",
    re.IGNORECASE,
)
_LIKERT_STEM = re.compile(
    r"\b(strongly agree|strongly disagree|agree or disagree|on a scale|rate (the|your|how)|1\s*[-–]\s*\d)\b",
    re.IGNORECASE,
)


class _DraftQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_text: str = Field(..., min_length=10, max_length=400)
    facet: str = Field(..., min_length=1, max_length=120)
    probe_type: str = Field(..., min_length=3, max_length=30)
    rationale: str = Field(..., min_length=5, max_length=400)


class _QualitativeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questions: List[_DraftQuestion] = Field(..., min_length=1, max_length=15)


class _ReviewVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_index: int = Field(..., ge=0)
    verdict: str = Field(..., min_length=3, max_length=10)
    revised_text: Optional[str] = Field(default=None, min_length=10, max_length=400)
    reason: str = Field(default="", max_length=300)


class _ReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdicts: List[_ReviewVerdict] = Field(default_factory=list)


def check_question(question_text: str) -> Optional[str]:
    """Deterministic rubric check. Returns a failure reason, or None if the
    question passes. The opener and Likert patterns are English-only; for
    non-Latin text only the question-mark and length rules apply."""
    text = question_text.strip()
    if len(text) < 10:
        return "too short to be a usable interview question"
    if not text.endswith("?") and not text.endswith("？"):
        return "does not end with a question mark"
    if _LIKERT_STEM.search(text):
        return "contains Likert/rating language"
    if _YES_NO_OPENER.match(text) and not _OPEN_PROBE_WHITELIST.match(text):
        return "closed yes/no opener outside the open-probe whitelist"
    return None


def _mock_questions(
    request: UserRequest, facet_names: List[str]
) -> List[QualitativeQuestion]:
    construct = request.construct_name
    questions = [
        QualitativeQuestion(
            question_text=f"What does {construct.lower()} mean to you in your daily life?",
            facet=construct,
            probe_type="comprehension",
            rationale="Surfaces the respondent's own definition of the construct.",
        ),
        QualitativeQuestion(
            question_text=f"Can you describe a recent time when you experienced {construct.lower()}?",
            facet=facet_names[0] if facet_names else construct,
            probe_type="example",
            rationale="Anchors the construct in a concrete lived episode.",
        ),
        QualitativeQuestion(
            question_text=f"How does {construct.lower()} show up differently at work compared to at home?",
            facet=facet_names[0] if facet_names else construct,
            probe_type="contrast",
            rationale="Explores situational boundaries of the construct.",
        ),
        QualitativeQuestion(
            question_text=f"Walk me through what happens for you when {construct.lower()} starts to change?",
            facet=facet_names[-1] if facet_names else construct,
            probe_type="process",
            rationale="Traces the temporal unfolding of the experience.",
        ),
        QualitativeQuestion(
            question_text=f"Tell me more about which parts of your life {construct.lower()} touches most?",
            facet=facet_names[-1] if facet_names else construct,
            probe_type="elaboration",
            rationale="Invites depth on the construct's most salient domain.",
        ),
    ]
    return questions


def _build_generation_messages(
    request: UserRequest,
    facet_mapping: Optional[FacetMapperResponse],
    evidence: List[EvidenceChunk],
) -> list:
    system = load_prompt("qualitative_generator.md")
    facets = (
        [
            {"facet_name": f.facet_name, "facet_description": f.facet_description}
            for f in facet_mapping.facets
        ]
        if facet_mapping
        else []
    )
    evidence_excerpts = [
        {"source": chunk.title, "quote": chunk.quote}
        for chunk in evidence[:8]
    ]
    payload = {
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "target_population": request.target_population,
        "cultural_group": request.cultural_group,
        "language": request.language,
        "facets": facets,
        "evidence_excerpts": evidence_excerpts,
    }
    human = (
        f"Generate 5-10 open-ended interview questions for this construct, "
        f"following the rubric and coverage rules exactly. Valid probe_type "
        f"values: {', '.join(PROBE_TYPES)}.\n\nINPUT:\n{payload}"
    )
    return [("system", system), ("human", human)]


def _self_review(
    request: UserRequest,
    questions: List[_DraftQuestion],
) -> Tuple[List[_DraftQuestion], TokenUsage]:
    """One critique-and-revise pass against the rubric. Returns the revised
    question list; on review failure, returns the originals unchanged."""
    system = (
        "You are an expert in qualitative interviewing and survey pre-testing. "
        "Audit each question below against this rubric: genuinely open-ended "
        "(no yes/no answers; the probe stems 'Can you describe / Could you "
        "tell me / Would you walk me through' are acceptable), one question "
        "at a time (no double-barreled), non-leading (no presupposed "
        "experience or valence), no Likert/rating language, plain wording "
        "for the target population, ends with a question mark. "
        "For each question return verdict 'keep', 'revise' (with revised_text "
        "fixing the flaw), or 'drop' (unfixable), plus a short reason. "
        "Respond with JSON only."
    )
    human = (
        f"Target population: {request.target_population}. "
        f"Construct: {request.construct_name}.\n\nQUESTIONS:\n"
        + "\n".join(
            f"{i}: {question.question_text}" for i, question in enumerate(questions)
        )
    )
    try:
        review, usage = invoke_structured_with_usage(
            _ReviewOutput,
            [("system", system), ("human", human)],
            agent_name="qualitative_generator",
            model_provider=request.model_provider,
        )
    except Exception as exc:
        logger.warning("QUALITATIVE self-review failed (%s); keeping originals", exc)
        return questions, TokenUsage()

    revised: List[_DraftQuestion] = []
    by_index = {verdict.question_index: verdict for verdict in review.verdicts}
    for i, question in enumerate(questions):
        verdict = by_index.get(i)
        if verdict is None or verdict.verdict == "keep":
            revised.append(question)
        elif verdict.verdict == "revise" and verdict.revised_text:
            revised.append(
                question.model_copy(update={"question_text": verdict.revised_text})
            )
        elif verdict.verdict == "drop":
            logger.info(
                "QUALITATIVE self-review dropped question %d: %s", i, verdict.reason
            )
        else:
            revised.append(question)
    return revised, usage


def generate_qualitative_questions(
    request: UserRequest,
    facet_mapping: Optional[FacetMapperResponse],
    evidence: List[EvidenceChunk],
) -> Tuple[List[QualitativeQuestion], List[str], TokenUsage]:
    """Generate open-ended probes with a critique-and-revise gate.

    Returns (questions, warnings, usage). Warnings name every question the
    deterministic post-checks dropped."""
    facet_names = (
        [f.facet_name for f in facet_mapping.facets] if facet_mapping else []
    )
    if settings.APP_MODE == "mock":
        return _mock_questions(request, facet_names), [], TokenUsage()

    total_usage = TokenUsage(model_name="qualitative_generator")
    try:
        draft, usage = invoke_structured_with_usage(
            _QualitativeDraft,
            _build_generation_messages(request, facet_mapping, evidence),
            agent_name="qualitative_generator",
            model_provider=request.model_provider,
        )
    except Exception as exc:
        logger.error("QUALITATIVE generation failed: %s", exc, exc_info=True)
        return [], [f"Qualitative question generation failed ({type(exc).__name__})."], total_usage
    total_usage.input_tokens += usage.input_tokens
    total_usage.output_tokens += usage.output_tokens
    total_usage.total_tokens += usage.total_tokens

    reviewed, review_usage = _self_review(request, draft.questions)
    total_usage.input_tokens += review_usage.input_tokens
    total_usage.output_tokens += review_usage.output_tokens
    total_usage.total_tokens += review_usage.total_tokens

    questions: List[QualitativeQuestion] = []
    warnings: List[str] = []
    for question in reviewed:
        failure = check_question(question.question_text)
        if failure:
            warnings.append(
                f"Dropped qualitative question ({failure}): "
                f"\"{question.question_text[:80]}\""
            )
            continue
        probe_type = (
            question.probe_type.lower()
            if question.probe_type.lower() in PROBE_TYPES
            else "elaboration"
        )
        try:
            questions.append(
                QualitativeQuestion(
                    question_text=question.question_text.strip(),
                    facet=question.facet,
                    probe_type=probe_type,
                    rationale=question.rationale,
                )
            )
        except Exception as exc:
            warnings.append(
                f"Dropped qualitative question (failed schema validation: "
                f"{type(exc).__name__}): \"{question.question_text[:80]}\""
            )

    logger.info(
        "QUALITATIVE done kept=%d dropped=%d", len(questions), len(warnings)
    )
    return questions, warnings, total_usage
