# Evaluation Benchmark Suite

This directory contains the gold-standard benchmark evaluation dataset for the **AI Research & Report Agent**.

## Dataset Structure

The dataset (`questions.jsonl`) contains 50 carefully curated test queries with ground-truth facts, difficulty ratings, domain categories, and expected citation minimums.

### Archetypes
1. **Direct Factual (`direct_factual`)**: Tests single-concept factual retrieval, precision, and verified citations.
2. **Comparative (`comparative`)**: Tests multi-source synthesis, comparison tables, and synthesis across contrasting technical domains.
3. **Contradictory (`contradictory`)**: Tests the Analyst Agent's ability to identify conflicting statistics or expert opinions without hallucinating a false consensus.
4. **Unanswerable (`unanswerable`)**: Tests rejection of mythical or non-existent topics without fabricating facts.

### Benchmark Metrics
- **Citation Precision**: Proportion of inline references that map to verified evidence records.
- **Citation Recall**: Proportion of factual assertions in findings that possess at least one citation.
- **Faithfulness**: Token and semantic grounding of report text within retrieved source evidence.
- **Hallucination Rate**: Frequency of unsupported or contradictory claims.
- **Quality Score**: Composite multi-agent assessment score (0.0 to 10.0) assigned by the Critic Agent.

## Running the Benchmark

```bash
# Run benchmark on first 5 questions
python -m backend.eval.run_eval --max 5

# Run benchmark on hard questions only
python -m backend.eval.run_eval --difficulty hard --max 10

# Run empirical retrieval experiments
python -m backend.eval.experiments
```
