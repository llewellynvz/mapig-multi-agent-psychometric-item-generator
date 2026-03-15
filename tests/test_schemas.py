"""Test suite for validation schemas.

This module tests the Pydantic schemas used for validation results,
including dimension scores and export metadata.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_validation_export():
    """Verify FinalOutput schema can serialize validation_results with all metadata.

    Tests VAL-09: Export validation metadata (all dimension scores, reasoning, attempt count).

    Expected behavior:
    - FinalOutput schema includes optional validation_results field
    - validation_results is a list of ValidationResult objects
    - Each ValidationResult contains:
      - item_index, item_text
      - dimension_scores (list of 4 DimensionScore objects)
      - weighted_score (float)
      - accept (bool)
      - attempt (int, 1-3)
    - ValidationResult can be serialized to JSON
    - All dimension scores and reasoning are preserved in export
    """
    from backend.schemas import DimensionScore, ItemValidation, DraftItem, FinalOutput, AuditMetadata

    # Create dimension scores
    dim_scores = [
        DimensionScore(dimension="correspondence", reasoning="Aligns well", score=8),
        DimensionScore(dimension="distinctiveness", reasoning="Clear boundaries", score=7),
        DimensionScore(dimension="clarity", reasoning="Easy to understand", score=9),
        DimensionScore(dimension="specificity", reasoning="Precise wording", score=8),
    ]

    # Create item validation
    validation = ItemValidation(
        item_index=0,
        item_text="I feel anxious in social situations",
        dimension_scores=dim_scores,
        weighted_score=7.95,  # weighted: 8*0.5 + 7*0.25 + 9*0.15 + 8*0.1
        accept=True,
        attempt=1,
    )

    # Create draft item with validation
    item = DraftItem(
        item_text="I feel anxious in social situations",
        construct_name="Social Anxiety",
        rationale="Measures anxious response",
        validation_result=validation,
    )

    # Create final output with validation metadata
    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-08T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        validation_attempts=1,
        validation_failures=0,
    )

    output = FinalOutput(final_items=[item], audit=audit)

    # Verify serialization preserves validation data
    data = output.model_dump()
    assert data["final_items"][0]["validation_result"] is not None
    assert len(data["final_items"][0]["validation_result"]["dimension_scores"]) == 4
    assert data["final_items"][0]["validation_result"]["weighted_score"] == 7.95
    assert data["audit"]["validation_attempts"] == 1


def test_dimension_score_schema():
    """Verify DimensionScore schema validates score range 1-10.

    Tests schema validation for individual dimension scores.

    Expected behavior:
    - DimensionScore has three fields: dimension, reasoning, score
    - dimension is a string (correspondence/distinctiveness/clarity/specificity)
    - reasoning is a non-empty string
    - score is an integer with Pydantic constraint: ge=1, le=10
    - Pydantic raises ValidationError for scores < 1 or > 10
    - Pydantic raises ValidationError for float scores (must be int)
    """
    from pydantic import ValidationError
    from backend.schemas import DimensionScore, ItemValidation

    # Test valid score
    valid_score = DimensionScore(
        dimension="correspondence",
        reasoning="Strong alignment with construct",
        score=8
    )
    assert valid_score.score == 8
    assert valid_score.dimension == "correspondence"

    # Test boundary values (1 and 10 are valid)
    min_score = DimensionScore(dimension="clarity", reasoning="Minimal", score=1)
    assert min_score.score == 1

    max_score = DimensionScore(dimension="clarity", reasoning="Perfect", score=10)
    assert max_score.score == 10

    # Test invalid: score < 1
    with pytest.raises(ValidationError) as exc_info:
        DimensionScore(dimension="clarity", reasoning="Too low", score=0)
    assert "greater than or equal to 1" in str(exc_info.value).lower()

    # Test invalid: score > 10
    with pytest.raises(ValidationError) as exc_info:
        DimensionScore(dimension="clarity", reasoning="Too high", score=11)
    assert "less than or equal to 10" in str(exc_info.value).lower()

    # Test ItemValidation requires exactly 4 dimensions (VAL-02)
    dim_scores_4 = [
        DimensionScore(dimension="correspondence", reasoning="Good", score=8),
        DimensionScore(dimension="distinctiveness", reasoning="Good", score=7),
        DimensionScore(dimension="clarity", reasoning="Good", score=9),
        DimensionScore(dimension="specificity", reasoning="Good", score=8),
    ]

    validation = ItemValidation(
        item_index=0,
        item_text="Test item",
        dimension_scores=dim_scores_4,
        weighted_score=7.95,
        accept=True,
        attempt=1,
    )
    assert len(validation.dimension_scores) == 4


def test_finaloutput_enhanced_schema():
    """Phase 03.1: FinalOutput accepts optional metadata fields."""
    from backend.schemas import UserRequest, ReviewComment, DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create mock data
    user_req = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=5,
        constraints=[]
    )

    review_comment = ReviewComment(
        type="linguistic",
        item_index=0,
        issue="Test issue",
        severity=3,
        suggested_edit="Test edit"
    )

    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test Construct",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    # Act: Create FinalOutput with enhanced fields
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit,
        user_request=user_req,
        linguistic_feedback=[review_comment],
        bias_feedback=[],
        content_feedback=[]
    )

    # Assert: All fields populated correctly
    assert output.user_request == user_req
    assert len(output.linguistic_feedback) == 1
    assert output.linguistic_feedback[0].issue == "Test issue"
    assert output.bias_feedback == []
    assert output.content_feedback == []


def test_finaloutput_backward_compatibility():
    """Phase 03.1: FinalOutput maintains backward compatibility without optional fields."""
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create minimal valid FinalOutput (existing pattern)
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    # Act: Create FinalOutput WITHOUT new fields (backward compatibility)
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit
    )

    # Assert: New fields use defaults (None or empty list)
    assert output.user_request is None
    assert output.linguistic_feedback == []
    assert output.bias_feedback == []
    assert output.content_feedback == []


def test_finaloutput_mutable_defaults():
    """Phase 03.1: FinalOutput feedback arrays are not shared across instances."""
    from backend.schemas import ReviewComment, DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create two FinalOutput instances without feedback
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    output1 = FinalOutput(final_items=[draft_item], audit=audit)
    output2 = FinalOutput(final_items=[draft_item], audit=audit)

    # Act: Modify one instance's feedback
    comment = ReviewComment(
        type="bias",
        item_index=0,
        issue="Test",
        severity=2,
        suggested_edit="Edit"
    )
    output1.bias_feedback.append(comment)

    # Assert: Other instance unaffected (not shared reference)
    assert len(output1.bias_feedback) == 1
    assert len(output2.bias_feedback) == 0
    assert output1.bias_feedback is not output2.bias_feedback


# Phase 03: Claude API Migration - Provider Selection Tests


def test_user_request_model_provider_defaults_to_claude():
    """Phase 03-01: UserRequest.model_provider defaults to 'claude'."""
    from backend.schemas import UserRequest

    # Act: Create UserRequest without model_provider
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=5
    )

    # Assert: Default is 'claude'
    assert request.model_provider == "claude"


def test_user_request_validates_model_provider_enum():
    """Phase 03-01: UserRequest validates model_provider is 'claude' or 'openai'."""
    from pydantic import ValidationError
    from backend.schemas import UserRequest

    # Test valid values
    valid_claude = UserRequest(
        construct_name="Test",
        construct_definition="Definition",
        target_population="Adults",
        response_scale="1-5",
        model_provider="claude"
    )
    assert valid_claude.model_provider == "claude"

    valid_openai = UserRequest(
        construct_name="Test",
        construct_definition="Definition",
        target_population="Adults",
        response_scale="1-5",
        model_provider="openai"
    )
    assert valid_openai.model_provider == "openai"

    # Test invalid value
    with pytest.raises(ValidationError) as exc_info:
        UserRequest(
            construct_name="Test",
            construct_definition="Definition",
            target_population="Adults",
            response_scale="1-5",
            model_provider="azure"  # Invalid
        )
    assert "model_provider" in str(exc_info.value).lower()


def test_user_request_accepts_openai_provider():
    """Phase 03-01: UserRequest accepts 'openai' as model_provider."""
    from backend.schemas import UserRequest

    # Act: Create UserRequest with openai provider
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=10,
        model_provider="openai"
    )

    # Assert: model_provider set correctly
    assert request.model_provider == "openai"

    # Assert: Serialization preserves model_provider
    data = request.model_dump()
    assert data["model_provider"] == "openai"


# Task #4: Web Surfer Enhancement - Theoretical Model Discovery Tests


def test_evidence_chunk_basic_fields():
    """Task #4: EvidenceChunk maintains backward compatibility with existing fields."""
    from backend.schemas import EvidenceChunk

    # Act: Create basic evidence chunk without theoretical metadata
    evidence = EvidenceChunk(
        source_id="web:abc123",
        title="Test Source",
        snippet="A short snippet about the construct",
        url_or_docref="https://example.com/paper",
        quote="This is a quote from the source"
    )

    # Assert: Basic fields work correctly
    assert evidence.source_id == "web:abc123"
    assert evidence.title == "Test Source"
    assert evidence.snippet == "A short snippet about the construct"
    assert evidence.url_or_docref == "https://example.com/paper"
    assert evidence.quote == "This is a quote from the source"

    # Assert: Theoretical fields default to None
    assert evidence.evidence_type is None
    assert evidence.authors is None
    assert evidence.theoretical_model is None
    assert evidence.dimensions is None


def test_evidence_chunk_theoretical_metadata():
    """Task #4: EvidenceChunk accepts theoretical model discovery fields."""
    from backend.schemas import EvidenceChunk

    # Act: Create evidence chunk with full theoretical metadata
    evidence = EvidenceChunk(
        source_id="web:keyes2002",
        title="Keyes (2002) - The Mental Health Continuum",
        snippet="Flourishing is defined as high levels of emotional, psychological, and social well-being",
        url_or_docref="https://doi.org/10.1037/0022-006X.70.3.674",
        quote="Flourishing is the presence of mental health, characterized by emotional vitality, positive functioning, and social integration.",
        evidence_type="theoretical_definition",
        authors="Keyes, C. L. M.",
        theoretical_model="Two-Continua Model of Mental Health",
        dimensions=["emotional well-being", "psychological well-being", "social well-being"]
    )

    # Assert: All theoretical fields populated correctly
    assert evidence.evidence_type == "theoretical_definition"
    assert evidence.authors == "Keyes, C. L. M."
    assert evidence.theoretical_model == "Two-Continua Model of Mental Health"
    assert evidence.dimensions == ["emotional well-being", "psychological well-being", "social well-being"]


def test_evidence_chunk_validates_evidence_type():
    """Task #4: EvidenceChunk validates evidence_type enum values."""
    from pydantic import ValidationError
    from backend.schemas import EvidenceChunk

    # Test valid evidence types
    valid_types = ["theoretical_definition", "dimensions", "measurement_precedent", "boundary_conditions"]

    for evidence_type in valid_types:
        evidence = EvidenceChunk(
            source_id="web:test",
            title="Test",
            snippet="Test snippet",
            url_or_docref="https://example.com",
            quote="Test quote",
            evidence_type=evidence_type
        )
        assert evidence.evidence_type == evidence_type

    # Test invalid evidence type
    with pytest.raises(ValidationError) as exc_info:
        EvidenceChunk(
            source_id="web:test",
            title="Test",
            snippet="Test snippet",
            url_or_docref="https://example.com",
            quote="Test quote",
            evidence_type="invalid_type"
        )
    assert "evidence_type" in str(exc_info.value).lower()


def test_evidence_chunk_dimensions_type():
    """Task #4: EvidenceChunk dimensions field accepts list of strings."""
    from backend.schemas import EvidenceChunk

    # Act: Create evidence with dimensions
    evidence = EvidenceChunk(
        source_id="web:sdt",
        title="Self-Determination Theory",
        snippet="SDT identifies three basic psychological needs",
        url_or_docref="https://example.com/sdt",
        quote="Autonomy, competence, and relatedness are the three fundamental needs",
        evidence_type="dimensions",
        authors="Deci & Ryan",
        theoretical_model="Self-Determination Theory",
        dimensions=["autonomy", "competence", "relatedness"]
    )

    # Assert: Dimensions stored as list
    assert isinstance(evidence.dimensions, list)
    assert len(evidence.dimensions) == 3
    assert "autonomy" in evidence.dimensions
    assert "competence" in evidence.dimensions
    assert "relatedness" in evidence.dimensions


def test_evidence_chunk_serialization():
    """Task #4: EvidenceChunk serializes to JSON with theoretical metadata."""
    from backend.schemas import EvidenceChunk

    # Arrange: Create evidence with theoretical metadata
    evidence = EvidenceChunk(
        source_id="web:flourishing",
        title="Flourishing Framework",
        snippet="Test snippet",
        url_or_docref="https://example.com",
        quote="Test quote",
        evidence_type="dimensions",
        authors="Keyes",
        theoretical_model="Flourishing Model",
        dimensions=["emotional", "psychological", "social"]
    )

    # Act: Serialize to dict
    data = evidence.model_dump()

    # Assert: All fields present in serialization
    assert data["source_id"] == "web:flourishing"
    assert data["evidence_type"] == "dimensions"
    assert data["authors"] == "Keyes"
    assert data["theoretical_model"] == "Flourishing Model"
    assert data["dimensions"] == ["emotional", "psychological", "social"]


def test_retrieval_response_with_theoretical_evidence():
    """Task #4: RetrievalResponse accepts evidence chunks with theoretical metadata."""
    from backend.schemas import RetrievalResponse, EvidenceChunk

    # Arrange: Create evidence chunks with theoretical metadata
    evidence_list = [
        EvidenceChunk(
            source_id="web:def",
            title="Definition",
            snippet="Snippet 1",
            url_or_docref="https://example.com/1",
            quote="Quote 1",
            evidence_type="theoretical_definition",
            authors="Author A"
        ),
        EvidenceChunk(
            source_id="web:dim",
            title="Dimensions",
            snippet="Snippet 2",
            url_or_docref="https://example.com/2",
            quote="Quote 2",
            evidence_type="dimensions",
            dimensions=["dim1", "dim2"]
        )
    ]

    # Act: Create RetrievalResponse
    response = RetrievalResponse(evidence=evidence_list)

    # Assert: Response contains all evidence with metadata
    assert len(response.evidence) == 2
    assert response.evidence[0].evidence_type == "theoretical_definition"
    assert response.evidence[0].authors == "Author A"
    assert response.evidence[1].evidence_type == "dimensions"
    assert response.evidence[1].dimensions == ["dim1", "dim2"]


# Phase 7: v2.0 Analytics Schema Tests


def test_correlation_cell_validation():
    """Phase 7-01: CorrelationCell validates correlation and confidence interval ranges."""
    from pydantic import ValidationError
    from backend.schemas import CorrelationCell

    # Test valid correlation cell
    valid_cell = CorrelationCell(
        item_i_index=0,
        item_j_index=1,
        correlation=0.75,
        ci_low=0.65,
        ci_high=0.85
    )
    assert valid_cell.correlation == 0.75
    assert valid_cell.item_i_index == 0
    assert valid_cell.item_j_index == 1

    # Test boundary values: correlation at -1.0 and 1.0
    min_corr = CorrelationCell(
        item_i_index=0,
        item_j_index=1,
        correlation=-1.0,
        ci_low=-1.0,
        ci_high=-0.8
    )
    assert min_corr.correlation == -1.0

    max_corr = CorrelationCell(
        item_i_index=2,
        item_j_index=3,
        correlation=1.0,
        ci_low=0.9,
        ci_high=1.0
    )
    assert max_corr.correlation == 1.0

    # Test invalid: correlation > 1.0
    with pytest.raises(ValidationError) as exc_info:
        CorrelationCell(
            item_i_index=0,
            item_j_index=1,
            correlation=1.5,
            ci_low=0.5,
            ci_high=1.0
        )
    assert "correlation" in str(exc_info.value).lower()

    # Test invalid: correlation < -1.0
    with pytest.raises(ValidationError) as exc_info:
        CorrelationCell(
            item_i_index=0,
            item_j_index=1,
            correlation=-1.5,
            ci_low=-1.0,
            ci_high=-0.5
        )
    assert "correlation" in str(exc_info.value).lower()

    # Test invalid: negative item index
    with pytest.raises(ValidationError) as exc_info:
        CorrelationCell(
            item_i_index=-1,
            item_j_index=1,
            correlation=0.5,
            ci_low=0.3,
            ci_high=0.7
        )
    assert "item_i_index" in str(exc_info.value).lower()


def test_correlation_matrix_validation():
    """Phase 7-01: CorrelationMatrix validates aggregates and disclaimer default."""
    from backend.schemas import CorrelationMatrix, CorrelationCell

    # Arrange: Create valid cells
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.68, ci_low=0.58, ci_high=0.78),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.72, ci_low=0.62, ci_high=0.82),
    ]

    # Act: Create correlation matrix with valid data
    matrix = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.72,
        internal_consistency_flag="good"
    )

    # Assert: All fields populated correctly
    assert len(matrix.cells) == 3
    assert matrix.mcdonalds_omega == 0.85
    assert matrix.mean_inter_item_correlation == 0.72
    assert matrix.internal_consistency_flag == "good"
    assert matrix.disclaimer == "Correlations estimated via sentence-embedding cosine similarity (Hommel & Arslan, 2024). Not a substitute for empirical validation."

    # Test boundary: mcdonalds_omega at 0.0 and 1.0
    matrix_min = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.0,
        mean_inter_item_correlation=0.2,
        internal_consistency_flag="poor"
    )
    assert matrix_min.mcdonalds_omega == 0.0

    matrix_max = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=1.0,
        mean_inter_item_correlation=0.95,
        internal_consistency_flag="excellent"
    )
    assert matrix_max.mcdonalds_omega == 1.0

    # Test invalid: mcdonalds_omega > 1.0
    from pydantic import ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CorrelationMatrix(
            cells=cells,
            mcdonalds_omega=1.2,
            mean_inter_item_correlation=0.8,
            internal_consistency_flag="excellent"
        )
    assert "mcdonalds_omega" in str(exc_info.value).lower()

    # Test invalid: empty cells list
    with pytest.raises(ValidationError):
        CorrelationMatrix(
            cells=[],
            mcdonalds_omega=0.85,
            mean_inter_item_correlation=0.72,
            internal_consistency_flag="good"
        )


def test_comparison_instrument_validation():
    """Phase 7-01: ComparisonInstrument validates required fields and extra='forbid'."""
    from pydantic import ValidationError
    from backend.schemas import ComparisonInstrument

    # Test valid instrument
    instrument = ComparisonInstrument(
        name="Rosenberg Self-Esteem Scale",
        construct="Self-Esteem",
        source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
        publication_year=1965,
        sample_items_count=10,
        psychometric_properties="Cronbach's alpha: 0.88, test-retest reliability: 0.85",
        similarity_rationale="Measures global self-worth, similar construct to our self-concept measure"
    )

    assert instrument.name == "Rosenberg Self-Esteem Scale"
    assert instrument.construct == "Self-Esteem"
    assert instrument.publication_year == 1965
    assert instrument.sample_items_count == 10

    # Test minimal valid (only required fields)
    minimal = ComparisonInstrument(
        name="Test Scale",
        construct="Test Construct",
        source_citation="Author (2020). Title. Journal."
    )
    assert minimal.publication_year is None
    assert minimal.sample_items_count is None
    assert minimal.psychometric_properties is None
    assert minimal.similarity_rationale is None

    # Test invalid: name too short
    with pytest.raises(ValidationError) as exc_info:
        ComparisonInstrument(
            name="A",
            construct="Test",
            source_citation="Citation here"
        )
    assert "name" in str(exc_info.value).lower()

    # Test invalid: extra field (extra="forbid")
    with pytest.raises(ValidationError) as exc_info:
        ComparisonInstrument(
            name="Test Scale",
            construct="Test",
            source_citation="Citation",
            invalid_field="should fail"
        )
    assert "extra" in str(exc_info.value).lower() or "invalid_field" in str(exc_info.value).lower()


def test_cross_construct_comparison_validation():
    """Phase 7-01: CrossConstructComparison validates required fields and extra='forbid'."""
    from pydantic import ValidationError
    from backend.schemas import CrossConstructComparison, ConstructPairAnalysis

    # Test valid cross-construct comparison
    pairs = [
        ConstructPairAnalysis(
            construct_a="Self-Esteem",
            construct_b="Self-Efficacy",
            estimated_correlation=0.45,
            discriminant_validity_flag="adequate",
            reasoning="Moderate correlation expected, constructs are related but distinct"
        )
    ]

    comparison = CrossConstructComparison(
        target_construct="Self-Esteem",
        comparison_constructs=["Self-Efficacy", "Depression", "Anxiety"],
        analysis_summary="Self-esteem shows adequate discriminant validity from related constructs",
        construct_pairs=pairs
    )

    assert comparison.target_construct == "Self-Esteem"
    assert len(comparison.comparison_constructs) == 3
    assert comparison.analysis_summary.startswith("Self-esteem")
    assert len(comparison.construct_pairs) == 1
    assert comparison.disclaimer == "LLM-estimated, not empirically validated"

    # Test minimal valid (no construct_pairs)
    minimal = CrossConstructComparison(
        target_construct="Test Construct",
        comparison_constructs=["Related Construct"],
        analysis_summary="Test analysis summary here"
    )
    assert minimal.construct_pairs == []

    # Test invalid: target_construct too short
    with pytest.raises(ValidationError) as exc_info:
        CrossConstructComparison(
            target_construct="A",
            comparison_constructs=["B"],
            analysis_summary="Analysis"
        )
    assert "target_construct" in str(exc_info.value).lower()

    # Test invalid: extra field (extra="forbid")
    with pytest.raises(ValidationError) as exc_info:
        CrossConstructComparison(
            target_construct="Test",
            comparison_constructs=["Related"],
            analysis_summary="Analysis",
            invalid_field="should fail"
        )
    assert "extra" in str(exc_info.value).lower() or "invalid_field" in str(exc_info.value).lower()


def test_finaloutput_analytics_backward_compat():
    """Phase 7-01: FinalOutput backward compatibility - without analytics fields."""
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create minimal FinalOutput (existing v1.1 pattern)
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale for item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-14T10:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    # Act: Create FinalOutput WITHOUT analytics fields
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit
    )

    # Assert: Analytics fields default to None or empty list
    assert output.correlation_matrix is None
    assert output.comparison_instruments == []
    assert output.cross_construct_analysis is None


def test_finaloutput_analytics_populated():
    """Phase 7-01: FinalOutput forward compatibility - with analytics fields populated."""
    from backend.schemas import (
        DraftItem, FinalOutput, AuditMetadata,
        CorrelationMatrix, CorrelationCell,
        ComparisonInstrument, CrossConstructComparison
    )

    # Arrange: Create full FinalOutput with analytics
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-14T10:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85)
    ]

    matrix = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.75,
        internal_consistency_flag="good"
    )

    instruments = [
        ComparisonInstrument(
            name="Test Scale",
            construct="Test Construct",
            source_citation="Author (2020). Title. Journal."
        )
    ]

    cross_construct = CrossConstructComparison(
        target_construct="Test Construct",
        comparison_constructs=["Related Construct"],
        analysis_summary="Adequate discriminant validity demonstrated"
    )

    # Act: Create FinalOutput WITH analytics fields
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit,
        correlation_matrix=matrix,
        comparison_instruments=instruments,
        cross_construct_analysis=cross_construct
    )

    # Assert: All analytics fields populated
    assert output.correlation_matrix is not None
    assert output.correlation_matrix.mcdonalds_omega == 0.85
    assert len(output.comparison_instruments) == 1
    assert output.comparison_instruments[0].name == "Test Scale"
    assert output.cross_construct_analysis is not None
    assert output.cross_construct_analysis.target_construct == "Test Construct"

    # Assert: model_dump() serializes correctly
    data = output.model_dump()
    assert data["correlation_matrix"]["mcdonalds_omega"] == 0.85
    assert len(data["comparison_instruments"]) == 1
    assert data["cross_construct_analysis"]["target_construct"] == "Test Construct"


def test_finaloutput_analytics_mutable_defaults():
    """Phase 7-01: FinalOutput comparison_instruments list not shared across instances."""
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, ComparisonInstrument

    # Arrange: Create two FinalOutput instances
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-14T10:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    output1 = FinalOutput(final_items=[draft_item], audit=audit)
    output2 = FinalOutput(final_items=[draft_item], audit=audit)

    # Act: Modify one instance's comparison_instruments
    instrument = ComparisonInstrument(
        name="Test Scale",
        construct="Test",
        source_citation="Citation"
    )
    output1.comparison_instruments.append(instrument)

    # Assert: Other instance unaffected (not shared reference)
    assert len(output1.comparison_instruments) == 1
    assert len(output2.comparison_instruments) == 0
    assert output1.comparison_instruments is not output2.comparison_instruments


# Phase 8: Correlation Matrix Schema Migration Tests


def test_correlation_matrix_mcdonalds_omega_field():
    """Phase 8-01: CorrelationMatrix uses mcdonalds_omega field (cronbachs_alpha removed)."""
    from backend.schemas import CorrelationMatrix, CorrelationCell

    # Arrange: Create valid cells
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.68, ci_low=0.58, ci_high=0.78),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.72, ci_low=0.62, ci_high=0.82),
    ]

    # Act: Create correlation matrix with mcdonalds_omega
    matrix = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.72,
        internal_consistency_flag="good"
    )

    # Assert: mcdonalds_omega field works
    assert matrix.mcdonalds_omega == 0.85
    assert matrix.mean_inter_item_correlation == 0.72
    assert matrix.internal_consistency_flag == "good"
    assert matrix.disclaimer == "Correlations estimated via sentence-embedding cosine similarity (Hommel & Arslan, 2024). Not a substitute for empirical validation."


def test_correlation_matrix_omega_threshold_flagging():
    """Phase 8-01: McDonald's omega threshold flagging (>= 0.70 pass, < 0.70 warning)."""
    from backend.schemas import CorrelationMatrix, CorrelationCell

    # Arrange: Create valid cells
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
    ]

    # Test: Omega >= 0.70 (pass)
    matrix_pass = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.75,
        internal_consistency_flag="pass"
    )
    assert matrix_pass.mcdonalds_omega >= 0.70

    # Test: Omega < 0.70 (warning)
    matrix_warning = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.65,
        mean_inter_item_correlation=0.65,
        internal_consistency_flag="warning"
    )
    assert matrix_warning.mcdonalds_omega < 0.70

    # Test: Omega exactly 0.70 (boundary - pass)
    matrix_boundary = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.70,
        mean_inter_item_correlation=0.70,
        internal_consistency_flag="pass"
    )
    assert matrix_boundary.mcdonalds_omega == 0.70


def test_correlation_matrix_no_cronbachs_alpha():
    """Phase 8-01: CorrelationMatrix no longer has cronbachs_alpha field (breaking change)."""
    from pydantic import ValidationError
    from backend.schemas import CorrelationMatrix, CorrelationCell

    # Arrange: Create valid cells
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
    ]

    # Act & Assert: cronbachs_alpha should be rejected (extra='forbid')
    with pytest.raises(ValidationError) as exc_info:
        CorrelationMatrix(
            cells=cells,
            cronbachs_alpha=0.85,  # Old field name - should fail
            mean_inter_item_correlation=0.75,
            internal_consistency_flag="good"
        )
    # Check that error mentions cronbachs_alpha or extra field
    error_str = str(exc_info.value).lower()
    assert "cronbachs_alpha" in error_str or "extra" in error_str


def test_correlation_cell_ci_bounds_preserved():
    """Phase 8-01: CorrelationCell CI bounds preserved after rename (CORR-03)."""
    from backend.schemas import CorrelationCell

    # Act: Create cell with confidence intervals
    cell = CorrelationCell(
        item_i_index=0,
        item_j_index=1,
        correlation=0.75,
        ci_low=0.65,
        ci_high=0.85
    )

    # Assert: CI bounds are stored correctly
    assert cell.ci_low == 0.65
    assert cell.ci_high == 0.85
    assert cell.correlation == 0.75
    assert cell.ci_low <= cell.correlation <= cell.ci_high


def test_correlation_matrix_disclaimer_default():
    """Phase 8-01: CorrelationMatrix disclaimer defaults correctly (CORR-05)."""
    from backend.schemas import CorrelationMatrix, CorrelationCell

    # Arrange: Create cells
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
    ]

    # Act: Create matrix without explicit disclaimer
    matrix = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.75,
        internal_consistency_flag="optimal_range"
    )

    # Assert: Default disclaimer is set
    assert matrix.disclaimer == "Correlations estimated via sentence-embedding cosine similarity (Hommel & Arslan, 2024). Not a substitute for empirical validation."
