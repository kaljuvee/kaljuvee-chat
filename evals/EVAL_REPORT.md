# Talk to Julian — Eval Report

- Generated: 2026-07-06T20:15:39.989476+00:00
- Judge: `GrokJudge(grok-4-1-fast-reasoning)` · Agent: `grok-4-1-fast-reasoning` · Threshold: 0.7
- **Overall pass rate: 82%** (22 cases)
- Mean scores — Groundedness 0.873, Correctness 0.877, Relevancy 0.882

## By category

| Category | N | Pass rate | Grounded | Correct | Relevant |
|---|---|---|---|---|---|
| cv_facts | 3 | 100% | 1.0 | 0.8 | 0.9 |
| technical | 6 | 83% | 0.867 | 0.883 | 0.967 |
| experience_years | 4 | 50% | 0.575 | 0.875 | 0.95 |
| career | 5 | 100% | 0.98 | 0.88 | 0.86 |
| soft | 4 | 75% | 0.95 | 0.925 | 0.7 |

## Cases

| ID | Category | Pass | G | C | R |
|---|---|---|---|---|---|
| cv-education | cv_facts | ✅ | 1.0 | 0.9 | 0.9 |
| cv-contact | cv_facts | ✅ | 1.0 | 0.7 | 0.9 |
| cv-company | cv_facts | ✅ | 1.0 | 0.8 | 0.9 |
| tech-orchestration | technical | ✅ | 0.9 | 1.0 | 1.0 |
| tech-cloud | technical | ✅ | 1.0 | 0.9 | 1.0 |
| tech-vectordb | technical | ❌ | 0.3 | 0.7 | 0.9 |
| tech-graphrag | technical | ✅ | 1.0 | 0.9 | 1.0 |
| tech-languages | technical | ✅ | 1.0 | 1.0 | 1.0 |
| tech-rl | technical | ✅ | 1.0 | 0.8 | 0.9 |
| exp-total | experience_years | ✅ | 1.0 | 0.9 | 1.0 |
| exp-python | experience_years | ❌ | 0.2 | 0.8 | 0.9 |
| exp-genai | experience_years | ✅ | 1.0 | 0.9 | 1.0 |
| exp-datawarehouse | experience_years | ❌ | 0.1 | 0.9 | 0.9 |
| career-current | career | ✅ | 1.0 | 0.9 | 0.9 |
| career-microsoft | career | ✅ | 0.9 | 0.9 | 0.8 |
| career-finance | career | ✅ | 1.0 | 0.8 | 0.9 |
| career-vaxart | career | ✅ | 1.0 | 0.9 | 0.8 |
| career-pe | career | ✅ | 1.0 | 0.9 | 0.9 |
| soft-fit-leadership | soft | ✅ | 1.0 | 0.9 | 1.0 |
| soft-intro | soft | ✅ | 0.9 | 0.9 | 0.9 |
| soft-guardrail-salary | soft | ✅ | 1.0 | 1.0 | 0.9 |
| soft-guardrail-offtopic | soft | ❌ | 0.9 | 0.9 | 0.0 |
