# Ask Julian — Evals

Automated quality checks for the recruiter-facing CV chatbot. Each case is a real
recruiter question; the live `ask_julian` agent answers it, and a **deepeval GEval**
LLM judge (running on the same provider as the app — xAI Grok by default) scores the
answer on three metrics.

## Metrics

| Metric | What it checks |
|---|---|
| **Groundedness** | Answer only makes claims supported by the CV; no fabricated employers/dates/tools. A correct refusal for out-of-CV questions counts as grounded. |
| **Correctness** | Answer is factually consistent with the reference facts for that question. |
| **Relevancy** | Answer addresses the question and stays on-topic (helpful extra detail is fine). |

Pass threshold is **0.7**; a case passes only if all three metrics clear it.

## Categories

`cv_facts` · `technical` · `experience_years` · `career` · `soft` (incl. guardrail
questions that are *not* in the CV and must be declined, not fabricated).

Cases live in [`cv_eval_cases.json`](cv_eval_cases.json).

## Run

```bash
uv pip install -r requirements-eval.txt      # one-time (deepeval)
python -m evals.run_eval                      # full suite
python -m evals.run_eval --category technical # one category
python -m evals.run_eval --limit 5            # first 5 cases
```

Outputs:
- `eval/eval-results.json` — full machine-readable report (per-case answers, scores, judge reasons, aggregates).
- `evals/EVAL_REPORT.md` — human-readable summary tables.

The judge uses `utils.llm.build_llm()`, so it follows `LLM_PROVIDER` (`xai` / `openai` /
`anthropic`) — no extra API keys needed beyond the one the app already uses.
