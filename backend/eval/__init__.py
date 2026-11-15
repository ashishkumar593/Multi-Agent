"""Evaluation and benchmarking module for the AI Research & Report Agent."""
from backend.eval.dataset import EvalQuestion, EvalDataset, load_eval_dataset
from backend.eval.metrics import (
    calculate_citation_precision,
    calculate_citation_recall,
    calculate_hallucination_rate,
    calculate_faithfulness,
    evaluate_research_report,
)

__all__ = [
    "EvalQuestion",
    "EvalDataset",
    "load_eval_dataset",
    "calculate_citation_precision",
    "calculate_citation_recall",
    "calculate_hallucination_rate",
    "calculate_faithfulness",
    "evaluate_research_report",
]
