"""Evaluation dataset models and loaders for benchmarking research agents."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class EvalQuestion(BaseModel):
    """A benchmark research question with expected properties and evaluation criteria."""
    id: str = Field(description="Unique question identifier (e.g. Q001)")
    topic: str = Field(description="The research query or topic prompt")
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")
    domain: str = Field(default="general", description="Subject area (ai_ml, cloud, security, etc.)")
    archetype: Literal["direct_factual", "comparative", "contradictory", "unanswerable"] = Field(
        default="direct_factual",
        description="Archetype test case"
    )
    expected_subquestions_min: int = Field(default=3, description="Minimum expected sub-questions")
    expected_citations_min: int = Field(default=2, description="Minimum expected valid citations")
    ground_truth_claims: List[str] = Field(default_factory=list, description="Key facts that should appear in findings")
    unacceptable_claims: List[str] = Field(default_factory=list, description="Hallucinated or invalid assertions")


class EvalDataset(BaseModel):
    """Collection of evaluation benchmark questions."""
    name: str = "Research Agent Benchmark Suite"
    version: str = "1.0.0"
    questions: List[EvalQuestion] = Field(default_factory=list)

    def by_difficulty(self, difficulty: str) -> List[EvalQuestion]:
        return [q for q in self.questions if q.difficulty == difficulty]

    def by_domain(self, domain: str) -> List[EvalQuestion]:
        return [q for q in self.questions if q.domain == domain]

    def to_jsonl(self, filepath: str | Path) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for q in self.questions:
                f.write(json.dumps(q.model_dump()) + "\n")


def load_eval_dataset(filepath: str | Path) -> EvalDataset:
    """Load evaluation questions from a JSONL file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {path}")

    questions: List[EvalQuestion] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            data = json.loads(line)
            questions.append(EvalQuestion(**data))

    return EvalDataset(questions=questions)
