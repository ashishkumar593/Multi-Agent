"""Unit tests for the evaluation dataset and quality metrics."""
import pytest
from backend.eval.dataset import load_eval_dataset, EvalQuestion
from backend.eval.metrics import (
    calculate_citation_precision,
    calculate_citation_recall,
    calculate_faithfulness,
    calculate_hallucination_rate,
    evaluate_research_report,
)


def test_load_benchmark_dataset():
    """Verify loading of the 50-question benchmark dataset."""
    dataset = load_eval_dataset("data/evaluation/questions.jsonl")
    assert len(dataset.questions) == 50
    
    # Check distributions
    easy = dataset.by_difficulty("easy")
    medium = dataset.by_difficulty("medium")
    hard = dataset.by_difficulty("hard")
    
    assert len(easy) > 0
    assert len(medium) > 0
    assert len(hard) > 0
    assert len(easy) + len(medium) + len(hard) == 50
    
    # Check question fields
    q1 = dataset.questions[0]
    assert isinstance(q1, EvalQuestion)
    assert q1.id == "Q001"
    assert len(q1.ground_truth_claims) >= 1


def test_citation_precision_calculation():
    """Verify precision scoring for matching and unmatching citation keys."""
    valid_ids = ["evid_1", "evid_2"]
    
    # Text with valid references
    text_perfect = "Recent findings show productivity gains [evid_1] and junior hiring declines [evid_2]."
    assert calculate_citation_precision(text_perfect, valid_ids) == 1.0
    
    # Text with invalid citation
    text_invalid = "AI eliminates 99% of work [evid_999]."
    # Note: calculate_citation_precision gives 0.8 partial credit if in bottom references, or <1.0
    prec = calculate_citation_precision(text_invalid, valid_ids)
    assert prec <= 0.8


def test_citation_recall_calculation():
    """Verify calculation of cited claims ratio."""
    assert calculate_citation_recall(total_claims=10, cited_claims=10) == 1.0
    assert calculate_citation_recall(total_claims=10, cited_claims=8) == 0.8
    assert calculate_citation_recall(total_claims=0, cited_claims=0) == 1.0


def test_faithfulness_and_hallucination_rate():
    """Verify token-level faithfulness and hallucination rate."""
    evidence = ["Artificial intelligence coding assistants improve software developer velocity."]
    grounded_report = "Developers using artificial intelligence coding assistants report higher velocity."
    
    score = calculate_faithfulness(grounded_report, evidence)
    assert score > 0.5
    
    assert calculate_hallucination_rate(unsupported_claims=1, total_claims=5) == 0.2


def test_evaluate_research_report_composite():
    """Verify composite report evaluation returns valid structured summary."""
    report = """# Executive Summary
Generative AI enhances coding throughput by 20% to 55% [EVID-1].

## Detailed Findings
Automated testing tools generate coverage suites rapidly [EVID-2].

## References
- [EVID-1] McKinsey Report 2024
- [EVID-2] GitHub Research 2024
"""
    evidence = [
        {"id": "EVID-1", "content": "Generative AI enhances coding throughput by 20% to 55%."},
        {"id": "EVID-2", "content": "Automated testing tools generate coverage suites rapidly."},
    ]
    claims = [
        {"claim": "AI boosts throughput", "supporting_evidence_ids": ["EVID-1"]},
        {"claim": "Testing tools generate coverage", "supporting_evidence_ids": ["EVID-2"]},
    ]
    
    summary = evaluate_research_report(
        report_markdown=report,
        evidence_items=evidence,
        extracted_claims=claims,
        critic_approved=True,
    )
    
    assert summary.citation_precision == 1.0
    assert summary.citation_recall == 1.0
    assert summary.hallucination_rate == 0.0
    assert summary.overall_quality_score >= 8.0
