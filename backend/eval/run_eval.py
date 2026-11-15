"""CLI and automated evaluation runner for benchmark evaluation."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Safeguard sys.path for direct execution
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from typing import Any, Dict, List

from backend.eval.dataset import load_eval_dataset
from backend.eval.metrics import evaluate_research_report
from backend.services.research_service import ResearchService


def run_benchmark(
    dataset_path: str = "data/evaluation/questions.jsonl",
    output_dir: str = "reports",
    max_questions: int = 5,
    difficulty: str | None = None,
) -> Dict[str, Any]:
    """Execute evaluation benchmark against the research agent."""
    dataset = load_eval_dataset(dataset_path)
    questions = dataset.questions
    
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]
    if max_questions:
        questions = questions[:max_questions]
        
    print(f"\n=======================================================")
    print(f"  AI Research & Report Agent Benchmark Suite")
    print(f"  Running on {len(questions)} evaluation queries...")
    print(f"=======================================================\n")
    
    service = ResearchService()
    results: List[Dict[str, Any]] = []
    
    start_total = time.time()
    
    for idx, q in enumerate(questions, 1):
        print(f"[{idx}/{len(questions)}] ({q.difficulty.upper()}) {q.topic[:65]}...")
        t0 = time.time()
        
        # Execute research
        job = service.execute_research_sync(topic=q.topic, scope="standard")
        duration = round(time.time() - t0, 2)
        
        # Evaluate report
        eval_scores = evaluate_research_report(
            report_markdown=job.get("report_markdown", ""),
            evidence_items=job.get("evidence", []),
            critic_approved=job.get("critic_approved", True),
            critic_quality_score=job.get("quality_score"),
        )
        
        res_record = {
            "question_id": q.id,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "domain": q.domain,
            "duration_sec": duration,
            "scores": eval_scores.model_dump(),
        }
        results.append(res_record)
        
        print(f"    -> Status: COMPLETED in {duration}s | Quality: {eval_scores.overall_quality_score}/10 | Prec: {eval_scores.citation_precision*100:.0f}%")
        
    total_time = round(time.time() - start_total, 2)
    avg_quality = round(sum(r["scores"]["overall_quality_score"] for r in results) / len(results), 2) if results else 0.0
    avg_prec = round(sum(r["scores"]["citation_precision"] for r in results) / len(results), 3) if results else 0.0
    avg_rec = round(sum(r["scores"]["citation_recall"] for r in results) / len(results), 3) if results else 0.0
    avg_latency = round(sum(r["duration_sec"] for r in results) / len(results), 2) if results else 0.0

    summary = {
        "total_queries_evaluated": len(results),
        "total_time_seconds": total_time,
        "average_latency_seconds": avg_latency,
        "average_quality_score": avg_quality,
        "average_citation_precision": avg_prec,
        "average_citation_recall": avg_rec,
        "results": results,
    }
    
    # Save output reports
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    json_path = out_path / "evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    md_path = out_path / "evaluation_summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Benchmark Evaluation Summary\n\n")
        f.write(f"- **Evaluated Queries**: {len(results)}\n")
        f.write(f"- **Average Quality Score**: {avg_quality} / 10.0\n")
        f.write(f"- **Average Citation Precision**: {avg_prec * 100:.1f}%\n")
        f.write(f"- **Average Citation Recall**: {avg_rec * 100:.1f}%\n")
        f.write(f"- **Average Latency**: {avg_latency}s\n\n")
        f.write("| ID | Difficulty | Topic | Latency | Quality | Precision |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            f.write(f"| {r['question_id']} | {r['difficulty']} | {r['topic'][:35]}... | {r['duration_sec']}s | {r['scores']['overall_quality_score']} | {r['scores']['citation_precision']*100:.0f}% |\n")
            
    print(f"\n=======================================================")
    print(f"  Benchmark Complete in {total_time}s")
    print(f"  Avg Quality: {avg_quality}/10 | Citation Precision: {avg_prec*100:.1f}%")
    print(f"  Reports written to {out_path}")
    print(f"=======================================================\n")
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run research agent evaluation benchmark")
    parser.add_argument("--dataset", default="data/evaluation/questions.jsonl", help="Path to JSONL dataset")
    parser.add_argument("--max", type=int, default=3, help="Max questions to evaluate")
    parser.add_argument("--difficulty", default=None, help="Filter by difficulty (easy, medium, hard)")
    parser.add_argument("--output", default="reports", help="Output directory for reports")
    args = parser.parse_args()
    
    run_benchmark(
        dataset_path=args.dataset,
        output_dir=args.output,
        max_questions=args.max,
        difficulty=args.difficulty,
    )
