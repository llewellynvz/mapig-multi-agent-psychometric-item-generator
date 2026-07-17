#!/usr/bin/env python3
"""Production evaluation script for MAPIG pipeline.

Runs live constructs against the production (or local) API via SSE streaming,
collects all events, and checks for warnings, regressions, and quality signals.

Usage:
    # Against production
    python scripts/production_eval.py

    # Against local dev server
    python scripts/production_eval.py --base-url http://localhost:8000

    # Single construct (fast check)
    python scripts/production_eval.py --construct "Cognitive Flexibility"

    # Skip analytics-heavy constructs
    python scripts/production_eval.py --skip-analytics
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Test constructs — curated for diverse pipeline exercise
# ---------------------------------------------------------------------------

TEST_CONSTRUCTS: list[dict[str, Any]] = [
    {
        "construct_name": "Cognitive Flexibility",
        "construct_definition": (
            "The mental ability to switch between thinking about two different "
            "concepts, or to think about multiple concepts simultaneously. It involves "
            "adapting cognitive processing strategies to face new and unexpected "
            "conditions in the environment, including the readiness to shift attention "
            "and change behavioral responses when demands change."
        ),
        "construct_exclusions": (
            "Not openness to experience, not curiosity, not creativity. "
            "Cognitive flexibility is about ADAPTING thought processes, not "
            "seeking novelty or generating ideas."
        ),
        "target_population": "Working adults",
        "response_scale": "7-point Likert (1=Strongly Disagree to 7=Strongly Agree)",
        "item_count": 7,
    },
    {
        "construct_name": "Emotional Intelligence",
        "construct_definition": (
            "The capacity to recognize, understand, manage, and effectively use "
            "one's own emotions and to recognize, understand, and influence the "
            "emotions of others. Encompasses self-awareness of emotional states, "
            "self-regulation of emotional responses, empathy, and social skill "
            "in managing relationships."
        ),
        "construct_exclusions": (
            "Not personality agreeableness, not social desirability, not empathy alone. "
            "Emotional intelligence is a multidimensional ability, not a single trait."
        ),
        "target_population": "Working adults",
        "response_scale": "5-point Likert (1=Strongly Disagree to 5=Strongly Agree)",
        "item_count": 7,
    },
    {
        "construct_name": "Growth Mindset",
        "construct_definition": (
            "The belief that one's abilities and intelligence can be developed "
            "through dedication, hard work, and learning from feedback. Contrasted "
            "with a fixed mindset that views abilities as innate and unchangeable. "
            "Encompasses beliefs about effort, learning from failure, and the "
            "malleability of personal qualities."
        ),
        "construct_exclusions": (
            "Not self-efficacy, not optimism, not resilience. "
            "Growth mindset is specifically about BELIEFS about ability malleability."
        ),
        "target_population": "University students",
        "response_scale": "6-point Likert (1=Strongly Disagree to 6=Strongly Agree)",
        "item_count": 5,
    },
    {
        "construct_name": "Job Satisfaction",
        "construct_definition": (
            "A pleasurable or positive emotional state resulting from the "
            "appraisal of one's job or job experiences. Encompasses overall "
            "affective evaluation of one's work, including satisfaction with "
            "work content, conditions, relationships, and outcomes."
        ),
        "construct_exclusions": (
            "Not work engagement, not organizational commitment, not career "
            "satisfaction. Job satisfaction is a present-state evaluation, "
            "not a motivational state or long-term attachment."
        ),
        "target_population": "Working adults",
        "cultural_group": "South African working adults",
        "response_scale": "5-point Likert (1=Strongly Disagree to 5=Strongly Agree)",
        "item_count": 7,
    },
]


# ---------------------------------------------------------------------------
# Data structures for collecting results
# ---------------------------------------------------------------------------


@dataclass
class SSEEvent:
    """A single parsed SSE event."""
    event_type: str
    data: dict[str, Any]
    raw: str = ""


@dataclass
class RunResult:
    """Result of a single construct run."""
    construct_name: str
    success: bool = False
    duration_s: float = 0.0
    events: list[SSEEvent] = field(default_factory=list)
    final_output: dict[str, Any] | None = None
    error: str | None = None

    # Quality signals
    item_count: int = 0
    unique_facets: int = 0
    mean_weighted_score: float = 0.0
    min_weighted_score: float = 0.0
    validation_attempts: int = 0
    iteration_count: int = 0
    stop_reason: str = ""
    content_comments: int = 0
    linguistic_comments: int = 0
    bias_comments: int = 0
    has_correlation_matrix: bool = False
    has_comparison_instruments: bool = False
    pseudo_alpha: float | None = None
    convergent_validity: float | None = None
    plagiarism_flags: int = 0

    # Warnings collected during analysis
    warnings: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    """Aggregated evaluation report across all constructs."""
    runs: list[RunResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    passed: bool = True


# ---------------------------------------------------------------------------
# SSE streaming client
# ---------------------------------------------------------------------------


def stream_construct(
    base_url: str,
    construct: dict[str, Any],
    timeout_s: int = 300,
) -> RunResult:
    """Run a single construct through the SSE streaming endpoint."""
    result = RunResult(construct_name=construct["construct_name"])
    url = f"{base_url}/v1/generate-items-stream"

    print(f"\n{'='*60}")
    print(f"  Running: {construct['construct_name']}")
    print(f"  Items: {construct['item_count']}, Scale: {construct['response_scale']}")
    print(f"{'='*60}")

    start = time.monotonic()
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_s, connect=30.0)) as client:
            with client.stream("POST", url, json=construct) as response:
                if response.status_code != 200:
                    result.error = f"HTTP {response.status_code}: {response.read().decode()[:500]}"
                    print(f"  ERROR: {result.error}")
                    return result

                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        event = _parse_sse_event(event_str)
                        if event:
                            result.events.append(event)
                            _print_progress(event)

    except httpx.TimeoutException:
        result.error = f"Timeout after {timeout_s}s"
        print(f"  TIMEOUT: {result.error}")
    except httpx.ConnectError as e:
        result.error = f"Connection failed: {e}"
        print(f"  CONNECTION ERROR: {result.error}")
    except Exception as e:
        result.error = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"  ERROR: {result.error}")

    result.duration_s = time.monotonic() - start

    # Extract final output or error from events
    for event in reversed(result.events):
        if event.event_type == "complete":
            # SSE complete event: {"type": "complete", "data": {final_output_dict}}
            fo = event.data.get("data") or event.data.get("final_output")
            if fo:
                result.final_output = fo
                result.success = True
                break
        if event.event_type == "error" and not result.error:
            result.error = (event.data.get("message") or event.data.get("error") or "Unknown SSE error")[:300]

    if result.success and result.final_output:
        _analyze_output(result)

    elapsed = f"{result.duration_s:.1f}s"
    status = "OK" if result.success else "FAILED"
    print(f"\n  [{status}] {construct['construct_name']} in {elapsed}")
    if result.warnings:
        for w in result.warnings:
            print(f"    WARNING: {w}")

    return result


def _parse_sse_event(raw: str) -> SSEEvent | None:
    """Parse a raw SSE event string."""
    data_line = None
    for line in raw.strip().split("\n"):
        if line.startswith("data: "):
            data_line = line[6:]

    if not data_line:
        return None

    try:
        data = json.loads(data_line)
    except json.JSONDecodeError:
        return SSEEvent(event_type="parse_error", data={"raw": data_line}, raw=raw)

    event_type = data.get("type", "unknown")
    return SSEEvent(event_type=event_type, data=data, raw=raw)


def _print_progress(event: SSEEvent) -> None:
    """Print compact progress line for an SSE event."""
    t = event.event_type
    d = event.data

    if t == "start":
        print(f"  -> Started (thread={d.get('thread_id', '?')[:8]}...)")
    elif t == "node_start":
        display = d.get("display_name", d.get("node", "?"))
        print(f"  -> {display}")
    elif t == "node_end":
        pass  # Already showed start
    elif t == "iteration":
        print(f"  -> Iteration {d.get('iteration', '?')}")
    elif t == "complete":
        print(f"  -> Complete")
    elif t == "error":
        msg = d.get("message") or d.get("error") or "?"
        print(f"  -> ERROR: {msg[:120]}")
    elif t == "log":
        level = d.get("level", "info")
        if level in ("warning", "error"):
            print(f"  -> LOG [{level}]: {d.get('message', '?')[:80]}")


# ---------------------------------------------------------------------------
# Output analysis — quality checks and warning detection
# ---------------------------------------------------------------------------


def _analyze_output(result: RunResult) -> None:
    """Analyze a successful run's output for quality signals and warnings."""
    fo = result.final_output
    if not fo:
        return

    # --- Item quality ---
    items = fo.get("final_items", [])
    result.item_count = len(items)

    facets = set()
    scores = []
    for item in items:
        if item.get("facet_name"):
            facets.add(item["facet_name"])

        vr = item.get("validation_result")
        if vr and isinstance(vr, dict):
            ws = vr.get("weighted_score", 0)
            scores.append(ws)

    result.unique_facets = len(facets)
    if scores:
        result.mean_weighted_score = sum(scores) / len(scores)
        result.min_weighted_score = min(scores)

    # --- Audit metadata ---
    audit = fo.get("audit", {})
    result.validation_attempts = audit.get("validation_attempts", 0)
    result.iteration_count = audit.get("iteration_count", 0)
    result.stop_reason = audit.get("stop_reason", "")

    # --- Reviewer comments ---
    result.content_comments = len(fo.get("content_feedback", []))
    result.linguistic_comments = len(fo.get("linguistic_feedback", []))
    result.bias_comments = len(fo.get("bias_feedback", []))

    # --- Analytics ---
    cm = fo.get("correlation_matrix")
    if cm and isinstance(cm, dict):
        result.has_correlation_matrix = True
        result.pseudo_alpha = cm.get("pseudo_alpha")
    result.has_comparison_instruments = len(fo.get("comparison_instruments", [])) > 0
    result.convergent_validity = fo.get("convergent_validity_score")
    result.plagiarism_flags = len(fo.get("plagiarism_flags") or {})

    # --- Warning checks ---
    _check_warnings(result, fo)


def _check_warnings(result: RunResult, fo: dict) -> None:
    """Check for quality warnings in the output."""
    items = fo.get("final_items", [])
    audit = fo.get("audit", {})

    # W1: Item count mismatch
    expected = 0
    ur = fo.get("user_request")
    if ur:
        expected = ur.get("item_count", 0)
    if expected and result.item_count != expected:
        result.warnings.append(
            f"Item count mismatch: expected {expected}, got {result.item_count}"
        )

    # W2: Low validation scores (any item < 5.0)
    for i, item in enumerate(items):
        vr = item.get("validation_result")
        if vr and isinstance(vr, dict):
            ws = vr.get("weighted_score", 0)
            if ws < 5.0:
                result.warnings.append(
                    f"Item {i+1} has low validation score: {ws:.2f}"
                )

    # W3: All validation scores identical (lazy LLM)
    scores = []
    for item in items:
        vr = item.get("validation_result")
        if vr and isinstance(vr, dict):
            dim_scores = vr.get("dimension_scores", [])
            for ds in dim_scores:
                if isinstance(ds, dict):
                    scores.append(ds.get("score", 0))
    if len(scores) > 4 and len(set(scores)) == 1:
        result.warnings.append(
            f"ALL validation dimension scores are identical ({scores[0]}) — likely lazy LLM evaluation"
        )

    # W4: Force-accept (hard stop)
    stop = audit.get("stop_reason", "")
    if "hard_stop" in stop.lower() or "force" in stop.lower():
        result.warnings.append(f"Pipeline force-accepted: stop_reason='{stop}'")

    # W5: High iteration count (max is 3)
    if result.iteration_count >= 3:
        result.warnings.append(
            f"Hit max iterations ({result.iteration_count})"
        )

    # W6: No facets assigned
    if result.unique_facets == 0 and result.item_count > 0:
        result.warnings.append("No facet_name assigned to any item")

    # W7: Low facet diversity (< 3 for items >= 5)
    if result.item_count >= 5 and 0 < result.unique_facets < 3:
        result.warnings.append(
            f"Low facet diversity: only {result.unique_facets} facets for {result.item_count} items"
        )

    # W8: Content reviewer found issues with all items
    content_comments = fo.get("content_feedback", [])
    item_indices_flagged = {c.get("item_index") for c in content_comments if c.get("severity", 0) >= 3}
    if result.item_count > 0 and len(item_indices_flagged) == result.item_count:
        result.warnings.append(
            "Content reviewer flagged ALL items at severity >= 3"
        )

    # W9: Reviewer suggests construct-shifting edit (our new guardrail should prevent this)
    for comment_list_key in ["linguistic_feedback", "bias_feedback"]:
        for comment in fo.get(comment_list_key, []):
            issue = (comment.get("issue") or "").lower()
            edit = (comment.get("suggested_edit") or "").lower()
            # Check if reviewer's edit tries to shift construct
            if "cannot be fixed without changing construct" in issue:
                pass  # This is expected from the guardrail
            elif any(phrase in issue for phrase in [
                "change the construct",
                "different construct",
                "measures something else",
            ]):
                result.warnings.append(
                    f"Reviewer ({comment_list_key}) suggests construct-shifting edit for item {comment.get('item_index', '?')}"
                )

    # W10: No evidence summary in iteration_history (can't check directly, but check SSE logs)
    log_events = [e for e in result.events if e.event_type == "log"]
    for le in log_events:
        msg = le.data.get("message", "")
        level = le.data.get("level", "info")
        if level in ("warning", "error"):
            # Deduplicate — only warn once per unique message
            short_msg = msg[:120]
            warning_text = f"Pipeline log [{level}]: {short_msg}"
            if warning_text not in result.warnings:
                result.warnings.append(warning_text)

    # W11: Plagiarism detected
    if result.plagiarism_flags > 0:
        result.warnings.append(
            f"Plagiarism detection flagged {result.plagiarism_flags} item(s)"
        )

    # W12: Correlation matrix issues
    cm = fo.get("correlation_matrix")
    if cm and isinstance(cm, dict):
        alpha = cm.get("pseudo_alpha")
        if alpha is not None and alpha < 0.5:
            result.warnings.append(f"Low pseudo-alpha (semantic): {alpha:.3f} (< 0.50)")
        elif alpha is None:
            result.warnings.append("Pseudo-alpha not estimable")
        flag = cm.get("internal_consistency_flag", "")
        if flag == "too_high":
            result.warnings.append("Internal consistency TOO HIGH — possible item redundancy")
        redundancy = cm.get("redundancy_flags") or []
        if redundancy:
            result.warnings.append(f"Redundancy flags: {', '.join(redundancy[:3])}")

        # Check for correlation > 1.0 (the IEEE 754 bug we fixed)
        for cell in cm.get("cells", []):
            if isinstance(cell, dict):
                corr = cell.get("correlation", 0)
                if abs(corr) > 1.0:
                    result.warnings.append(
                        f"Correlation overflow detected: {corr} (IEEE 754 bug may have regressed)"
                    )
                    break

    # W13: Duration warning
    if result.duration_s > 280:
        result.warnings.append(
            f"Run took {result.duration_s:.0f}s (> 280s budget target)"
        )

    # W14: Validation used too many attempts
    if result.validation_attempts > result.item_count * 2:
        result.warnings.append(
            f"Excessive validation attempts: {result.validation_attempts} for {result.item_count} items"
        )

    # W15: SSE error events
    error_events = [e for e in result.events if e.event_type == "error"]
    for ee in error_events:
        err_msg = ee.data.get("error", "unknown")[:150]
        result.warnings.append(f"SSE error event: {err_msg}")

    # W16: Synonym-substitution detection (heuristic)
    texts = [item.get("item_text", "") for item in items]
    _check_synonym_substitution(result, texts)


def _check_synonym_substitution(result: RunResult, item_texts: list[str]) -> None:
    """Heuristic check for synonym-substitution items.

    Compares item openings — if most items start with the same 3-word prefix,
    that's a sign of template-driven generation.
    """
    if len(item_texts) < 3:
        return

    # Check 3-word prefix similarity
    prefixes: list[str] = []
    for text in item_texts:
        words = text.lower().split()[:3]
        prefixes.append(" ".join(words))

    from collections import Counter
    counts = Counter(prefixes)
    most_common_prefix, most_common_count = counts.most_common(1)[0]
    ratio = most_common_count / len(item_texts)

    if ratio > 0.6 and len(item_texts) >= 4:
        result.warnings.append(
            f"Template-driven items: {most_common_count}/{len(item_texts)} "
            f"items start with '{most_common_prefix}...'"
        )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(report: EvalReport) -> str:
    """Generate a human-readable evaluation report."""
    lines: list[str] = []
    lines.append("\n" + "=" * 70)
    lines.append("  MAPIG PRODUCTION EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append(f"  Total duration: {report.total_duration_s:.1f}s")
    lines.append(f"  Constructs tested: {len(report.runs)}")
    lines.append(f"  Passed: {sum(1 for r in report.runs if r.success)}/{len(report.runs)}")
    lines.append("")

    # Per-construct summary table
    lines.append(f"  {'Construct':<25} {'Status':<8} {'Time':>6} {'Items':>5} {'Facets':>6} {'AvgScore':>8} {'Iter':>4} {'Stop Reason':<20}")
    lines.append(f"  {'-'*25} {'-'*8} {'-'*6} {'-'*5} {'-'*6} {'-'*8} {'-'*4} {'-'*20}")

    for r in report.runs:
        status = "OK" if r.success else "FAIL"
        avg = f"{r.mean_weighted_score:.2f}" if r.mean_weighted_score else "N/A"
        stop = r.stop_reason[:20] if r.stop_reason else "N/A"
        lines.append(
            f"  {r.construct_name:<25} {status:<8} {r.duration_s:>5.0f}s {r.item_count:>5} {r.unique_facets:>6} {avg:>8} {r.iteration_count:>4} {stop:<20}"
        )

    # Analytics summary
    lines.append("")
    lines.append("  ANALYTICS:")
    lines.append(f"  {'Construct':<25} {'Omega':>7} {'Conv.Val':>8} {'Corr?':>5} {'Instr?':>6} {'Plag':>4}")
    lines.append(f"  {'-'*25} {'-'*7} {'-'*8} {'-'*5} {'-'*6} {'-'*4}")
    for r in report.runs:
        if not r.success:
            continue
        omega = f"{r.pseudo_alpha:.3f}" if r.pseudo_alpha is not None else "N/A"
        cv = f"{r.convergent_validity:.3f}" if r.convergent_validity is not None else "N/A"
        corr = "Yes" if r.has_correlation_matrix else "No"
        instr = "Yes" if r.has_comparison_instruments else "No"
        lines.append(
            f"  {r.construct_name:<25} {omega:>7} {cv:>8} {corr:>5} {instr:>6} {r.plagiarism_flags:>4}"
        )

    # All warnings
    all_warnings = []
    for r in report.runs:
        for w in r.warnings:
            all_warnings.append(f"  [{r.construct_name}] {w}")
    for w in report.warnings:
        all_warnings.append(f"  [GLOBAL] {w}")

    if all_warnings:
        lines.append("")
        lines.append(f"  WARNINGS ({len(all_warnings)}):")
        for w in all_warnings:
            lines.append(f"    {w}")
    else:
        lines.append("")
        lines.append("  WARNINGS: None")

    # Errors
    if report.errors:
        lines.append("")
        lines.append(f"  ERRORS ({len(report.errors)}):")
        for e in report.errors:
            lines.append(f"    {e}")

    # Verdict
    lines.append("")
    total_warnings = len(all_warnings)
    failed_runs = sum(1 for r in report.runs if not r.success)
    critical_warnings = sum(
        1 for r in report.runs for w in r.warnings
        if any(kw in w.lower() for kw in [
            "force-accept", "all items", "identical", "overflow", "timeout",
            "connection", "construct-shifting",
        ])
    )

    if failed_runs > 0:
        verdict = "FAIL"
        report.passed = False
    elif critical_warnings > 0:
        verdict = "WARN"
        report.passed = False
    elif total_warnings > 10:
        verdict = "WARN"
        report.passed = False
    else:
        verdict = "PASS"
        report.passed = True

    lines.append(f"  VERDICT: {verdict}")
    lines.append(f"  (Failed={failed_runs}, Critical={critical_warnings}, Total warnings={total_warnings})")
    lines.append("=" * 70)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPIG Production Evaluation")
    parser.add_argument(
        "--base-url",
        default="https://lmaig-langgraph.vercel.app",
        help="Base URL of the MAPIG API (default: production)",
    )
    parser.add_argument(
        "--construct",
        help="Run a single construct by name (partial match OK)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-construct timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--skip-analytics",
        action="store_true",
        help="Use fewer items (2) to skip analytics-heavy steps",
    )
    parser.add_argument(
        "--output",
        help="Write JSON results to file",
    )
    args = parser.parse_args()

    # Health check first
    print(f"Checking API health at {args.base_url}...")
    try:
        resp = httpx.get(f"{args.base_url}/healthz", timeout=10)
        health = resp.json()
        print(f"  Health: {health}")
        if health.get("status") != "ok":
            print("  ERROR: API not healthy")
            return 1
    except Exception as e:
        print(f"  ERROR: Health check failed: {e}")
        return 1

    # Select constructs
    constructs = TEST_CONSTRUCTS
    if args.construct:
        constructs = [
            c for c in constructs
            if args.construct.lower() in c["construct_name"].lower()
        ]
        if not constructs:
            print(f"No construct matching '{args.construct}'")
            return 1

    if args.skip_analytics:
        for c in constructs:
            c["item_count"] = 2

    # Run evaluations
    report = EvalReport()
    total_start = time.monotonic()

    for construct in constructs:
        result = stream_construct(args.base_url, construct, timeout_s=args.timeout)
        report.runs.append(result)
        if not result.success:
            report.errors.append(
                f"{result.construct_name}: {result.error or 'Unknown failure'}"
            )

    report.total_duration_s = time.monotonic() - total_start

    # Cross-construct checks
    successful = [r for r in report.runs if r.success]
    if len(successful) >= 2:
        # Check if all constructs have similar scores (suspiciously uniform)
        avg_scores = [r.mean_weighted_score for r in successful if r.mean_weighted_score > 0]
        if avg_scores and max(avg_scores) - min(avg_scores) < 0.3:
            report.warnings.append(
                f"Suspiciously uniform scores across constructs "
                f"(range={min(avg_scores):.2f}-{max(avg_scores):.2f})"
            )

        # Check if any construct took dramatically longer
        durations = [r.duration_s for r in successful]
        if durations:
            mean_d = sum(durations) / len(durations)
            for r in successful:
                if r.duration_s > mean_d * 2.5 and r.duration_s > 120:
                    report.warnings.append(
                        f"{r.construct_name} took {r.duration_s:.0f}s "
                        f"(mean={mean_d:.0f}s) — possible stall"
                    )

    # Print report
    report_text = generate_report(report)
    print(report_text)

    # Write JSON output if requested
    if args.output:
        json_output = {
            "total_duration_s": report.total_duration_s,
            "passed": report.passed,
            "runs": [
                {
                    "construct_name": r.construct_name,
                    "success": r.success,
                    "duration_s": r.duration_s,
                    "item_count": r.item_count,
                    "unique_facets": r.unique_facets,
                    "mean_weighted_score": r.mean_weighted_score,
                    "min_weighted_score": r.min_weighted_score,
                    "validation_attempts": r.validation_attempts,
                    "iteration_count": r.iteration_count,
                    "stop_reason": r.stop_reason,
                    "content_comments": r.content_comments,
                    "linguistic_comments": r.linguistic_comments,
                    "bias_comments": r.bias_comments,
                    "has_correlation_matrix": r.has_correlation_matrix,
                    "has_comparison_instruments": r.has_comparison_instruments,
                    "pseudo_alpha": r.pseudo_alpha,
                    "convergent_validity": r.convergent_validity,
                    "plagiarism_flags": r.plagiarism_flags,
                    "warnings": r.warnings,
                    "error": r.error,
                }
                for r in report.runs
            ],
            "global_warnings": report.warnings,
            "errors": report.errors,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2)
        print(f"\nJSON results written to {args.output}")

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
