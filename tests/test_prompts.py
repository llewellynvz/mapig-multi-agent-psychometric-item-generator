"""Test suite for agent prompt content validation.

This module tests prompt markdown files to ensure they contain required
psychometric principles, guidelines, and best practices per Phase 2 requirements.
"""

import pytest
from pathlib import Path


# AGT-01: Item Writer - 10 psychometric principles
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-02")
def test_item_writer_10_principles():
    """Test AGT-01: Verify all 10 psychometric principles present in item_writer.md.

    Expected principles:
    1. Unidimensionality
    2. Construct correspondence
    3. Distinctiveness
    4. Reading level control
    5. Semantic diversity
    6. Concrete language
    7. Temporal clarity
    8. Positive keying only
    9. Cultural neutrality
    10. Accessibility

    Tests VAL-08 requirement for research-backed item development.
    """
    prompt_path = Path("app/prompts/item_writer.md")
    assert prompt_path.exists(), "item_writer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Verify all 10 principles present
    assert "unidimensional" in content, "Principle 1: Unidimensionality must be present"
    assert "construct correspondence" in content, "Principle 2: Construct correspondence must be present"
    assert "distinctiveness" in content or "distinct" in content, "Principle 3: Distinctiveness must be present"
    assert "reading level" in content, "Principle 4: Reading level control must be present"
    assert "semantic diversity" in content, "Principle 5: Semantic diversity must be present"
    assert "concrete" in content, "Principle 6: Concrete language must be present"
    assert "temporal" in content, "Principle 7: Temporal clarity must be present"
    assert "positive keying" in content or "positively keyed" in content, "Principle 8: Positive keying must be present"
    assert "cultural" in content and "neutral" in content, "Principle 9: Cultural neutrality must be present"
    assert "accessibility" in content or "accessible" in content, "Principle 10: Accessibility must be present"


# AGT-02: Item Writer - Semantic diversity examples (Section B)
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-02")
def test_item_writer_semantic_diversity():
    """Test AGT-02: Verify semantic diversity examples present in Section B.

    Per research, semantic diversity prevents item redundancy and improves
    construct coverage. Section B should provide clear examples of:
    - Direct/indirect measurement approaches
    - Behavioral vs. affective indicators
    - Frequency vs. intensity anchors

    Expected behavior:
    - Section B exists in prompt
    - Contains semantic diversity guidance
    - Provides concrete examples (not just definitions)
    """
    prompt_path = Path("app/prompts/item_writer.md")
    assert prompt_path.exists(), "item_writer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8")

    # Check for Section B marker
    assert "section b" in content.lower() or "## b" in content.lower(), "Section B must be marked in prompt"

    # Check for semantic diversity content
    content_lower = content.lower()
    assert "semantic diversity" in content_lower, "Section B must mention semantic diversity"

    # Check for examples (at least one example indicator)
    example_indicators = ["example", "e.g.", "for instance", "such as"]
    assert any(indicator in content_lower for indicator in example_indicators), "Section B must provide examples"


# AGT-03: Item Writer - Reading level targets
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-02")
def test_item_writer_reading_levels():
    """Test AGT-03: Verify reading level targets specified.

    Per research (Lenzner 2014, Conrad & Blair 2009), reading level control
    is critical for comprehension and response quality.

    Expected targets:
    - General population: 6th-8th grade
    - Clinical population: 5th-6th grade
    - Specialized/technical constructs: 10th-12th grade

    Expected behavior:
    - All three targets specified with grade ranges
    - Guidance on how to achieve each level
    """
    prompt_path = Path("app/prompts/item_writer.md")
    assert prompt_path.exists(), "item_writer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for reading level section
    assert "reading level" in content, "Prompt must include reading level guidance"

    # Check for specific grade ranges
    assert ("6th" in content or "sixth" in content) and ("8th" in content or "eighth" in content), \
        "Must specify 6th-8th grade for general population"
    assert ("5th" in content or "fifth" in content) and ("6th" in content or "sixth" in content), \
        "Must specify 5th-6th grade for clinical population"
    assert ("10th" in content or "tenth" in content) and ("12th" in content or "twelfth" in content), \
        "Must specify 10th-12th grade for specialized constructs"


# AGT-04: Item Writer - Positive keying only (Section C)
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-02")
def test_item_writer_positive_keying():
    """Test AGT-04: Verify positive keying requirement in Section C, no reverse-item instructions.

    Per research (van Sonderen 2013, Podsakoff 2003), reverse-keyed items:
    - Increase cognitive load
    - Reduce reliability
    - Confuse respondents
    - Do not improve validity

    Expected behavior:
    - Section C explicitly requires positive keying only
    - No instructions for creating reverse-keyed items
    - Rationale provided (research-backed)
    """
    prompt_path = Path("app/prompts/item_writer.md")
    assert prompt_path.exists(), "item_writer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8")

    # Check for Section C marker
    assert "section c" in content.lower() or "## c" in content.lower(), "Section C must be marked in prompt"

    content_lower = content.lower()

    # Check for positive keying requirement
    assert "positive keying" in content_lower or "positively keyed" in content_lower, \
        "Section C must require positive keying"

    # Ensure NO reverse-item instructions present
    reverse_indicators = ["reverse-key", "reverse key", "negatively keyed", "reverse score"]
    reverse_found = any(indicator in content_lower for indicator in reverse_indicators)
    assert not reverse_found, "Section C must NOT include reverse-item instructions"


# AGT-05: Content Reviewer - Construct correspondence criteria
def test_content_reviewer_criteria():
    """Test AGT-05: Verify construct correspondence criteria in content_reviewer.md.

    Per research, construct correspondence requires:
    1. Definition anchoring - item must directly measure construct definition
    2. Competitor construct specification - identify what else item might measure
    3. Facet coverage tracking - ensure items span all construct facets

    Expected behavior:
    - All three criteria explicitly defined in prompt
    - Structured evaluation format (not just general guidance)
    - Examples or templates for each criterion
    """
    prompt_path = Path("app/prompts/content_reviewer.md")
    assert prompt_path.exists(), "content_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for construct correspondence section
    assert "construct correspondence" in content or "correspondence" in content, \
        "Prompt must include construct correspondence criteria"

    # Check for definition anchoring
    assert "definition" in content and "anchor" in content, \
        "Must include definition anchoring criterion"

    # Check for competitor construct identification
    assert "competitor" in content or ("alternative" in content and "construct" in content), \
        "Must include competitor construct specification"

    # Check for facet coverage
    assert "facet" in content and ("coverage" in content or "balance" in content), \
        "Must include facet coverage tracking"


# AGT-06: Linguistic Reviewer - Vague quantifier rules
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-04")
def test_linguistic_reviewer_quantifiers():
    """Test AGT-06: Verify vague quantifier rules in linguistic_reviewer.md.

    Per research (Lenzner 2012, Conrad & Blair 2009), vague quantifiers reduce
    item reliability. Three categories identified:

    Category 1 (requires time anchoring): "often", "sometimes", "rarely"
    Category 2 (avoid entirely): "a lot", "much", "many"
    Category 3 (context-dependent): "most", "few", "several"

    Expected behavior:
    - All three categories explicitly defined
    - Clear guidance for each category
    - Examples of acceptable vs. unacceptable usage
    """
    prompt_path = Path("app/prompts/linguistic_reviewer.md")
    assert prompt_path.exists(), "linguistic_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for vague quantifier section
    assert "quantifier" in content or "vague" in content, \
        "Prompt must address vague quantifiers"

    # Check for category structure (at least 2 categories mentioned)
    assert "category" in content or ("type" in content and "quantifier" in content), \
        "Must define quantifier categories"

    # Check for time anchoring guidance (Category 1)
    assert "time" in content and ("anchor" in content or "frame" in content), \
        "Must include time anchoring guidance for Category 1 quantifiers"

    # Check for avoidance guidance (Category 2)
    assert "avoid" in content or "do not use" in content, \
        "Must include avoidance guidance for Category 2 quantifiers"


# AGT-07: Bias Reviewer - 7 bias types defined
def test_bias_reviewer_7_types():
    """Test AGT-07: Verify 7 bias types defined in bias_reviewer.md.

    Per research (AGT-07 requirement), comprehensive bias detection requires:
    1. Construct bias
    2. Linguistic bias
    3. Cultural reference bias
    4. Socioeconomic bias
    5. Context access bias
    6. Protected attribute bias
    7. Intersectional bias

    Expected behavior:
    - All 7 types explicitly defined with descriptions
    - Examples or detection criteria for each type
    - Severity escalation rule for intersectional bias (≥4)
    """
    prompt_path = Path("app/prompts/bias_reviewer.md")
    assert prompt_path.exists(), "bias_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for all 7 bias types
    assert "construct bias" in content, "Type 1: Construct bias must be defined"
    assert "linguistic bias" in content, "Type 2: Linguistic bias must be defined"
    assert "cultural" in content and ("reference" in content or "bias" in content), \
        "Type 3: Cultural reference bias must be defined"
    assert "socioeconomic" in content or ("socio-economic" in content), \
        "Type 4: Socioeconomic bias must be defined"
    assert "context access" in content or ("access" in content and "bias" in content), \
        "Type 5: Context access bias must be defined"
    assert "protected attribute" in content, \
        "Type 6: Protected attribute bias must be defined"
    assert "intersectional" in content, \
        "Type 7: Intersectional bias must be defined"


# AGT-09: Meta Editor - Facet balancing rules
@pytest.mark.skip(reason="Awaiting prompt optimization in plan 02-04")
def test_meta_editor_facet_balance():
    """Test AGT-09: Verify facet balancing rules in meta_editor.md.

    Per research, balanced facet coverage ensures:
    - Comprehensive construct measurement
    - Prevents over-representation of easy-to-write facets
    - Maintains construct validity

    Expected rules:
    - Target ≥20% per facet (minimum representation)
    - Max 2:1 ratio between any two facets (balance constraint)

    Expected behavior:
    - Both rules explicitly stated with numeric thresholds
    - Guidance on when to regenerate for balance
    - Priority ordering for facet selection
    """
    prompt_path = Path("app/prompts/meta_editor.md")
    assert prompt_path.exists(), "meta_editor.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for facet balancing section
    assert "facet" in content and ("balance" in content or "coverage" in content), \
        "Prompt must include facet balancing rules"

    # Check for 20% threshold
    assert "20" in content or "0.2" in content, \
        "Must specify ≥20% per facet target"

    # Check for 2:1 ratio constraint
    assert ("2:1" in content or "2-to-1" in content or ("2" in content and "ratio" in content)), \
        "Must specify max 2:1 ratio constraint"
