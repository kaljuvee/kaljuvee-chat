"""Eval runner for the Ask Julian CV chatbot.

Calls the live `ask_julian` agent for each case, then scores the answer with
deepeval GEval metrics judged by our own LLM (Grok). Writes a JSON report to
`eval/eval-results.json` and a Markdown summary to `evals/EVAL_REPORT.md`.

Usage:
    python -m evals.run_eval                     # full suite
    python -m evals.run_eval --limit 5           # first 5 cases
    python -m evals.run_eval --category technical # one category
    python -m evals.run_eval --out eval/eval-results.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
os.environ.setdefault("DB_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from deepeval.metrics import GEval  # noqa: E402
from deepeval.test_case import LLMTestCase, LLMTestCaseParams as P  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402

from evals.grok_judge import GrokJudge  # noqa: E402

EVALS_DIR = Path(__file__).resolve().parent
CASES_PATH = EVALS_DIR / "cv_eval_cases.json"
SHARED = ROOT / "prompts" / "shared"
THRESHOLD = 0.7


def _load_context() -> list[str]:
    cv = (SHARED / "cv.md").read_text(encoding="utf-8")
    facts = (SHARED / "career_facts.md").read_text(encoding="utf-8")
    return [cv, facts]


def _answer(agent, question: str) -> str:
    out = agent.invoke({"messages": [HumanMessage(content=question)]})
    msgs = out.get("messages", [])
    return msgs[-1].content if msgs else ""


def _build_metrics(judge):
    groundedness = GEval(
        name="Groundedness",
        criteria=(
            "Given the CV context, decide whether the Actual Output only makes claims "
            "supported by the Context and does NOT fabricate employers, dates, numbers, "
            "tools or facts about Julian. If the Input asks for information that is not in "
            "the Context, a polite refusal that points the user to contact Julian directly "
            "is fully grounded (score high); inventing an answer is not (score low)."
        ),
        evaluation_params=[P.INPUT, P.ACTUAL_OUTPUT, P.CONTEXT],
        model=judge, threshold=THRESHOLD, async_mode=False,
    )
    correctness = GEval(
        name="Correctness",
        criteria=(
            "Decide whether the Actual Output is factually consistent with the Expected "
            "Output (reference facts about Julian). Wording and formatting differences are "
            "fine; missing key facts or contradictions lower the score. When the Expected "
            "Output marks this as a guardrail (info not in the CV), a polite refusal that "
            "points to contacting Julian is fully correct."
        ),
        evaluation_params=[P.INPUT, P.ACTUAL_OUTPUT, P.EXPECTED_OUTPUT],
        model=judge, threshold=THRESHOLD, async_mode=False,
    )
    relevancy = GEval(
        name="Relevancy",
        criteria=(
            "Decide whether the Actual Output answers the recruiter's question and stays "
            "on-topic about Julian, in a clear and professional tone. Additional accurate, "
            "relevant detail about Julian (context, related experience) is HELPFUL and must "
            "NOT be penalised. Only score low if the output fails to answer the question, "
            "drifts off-topic, or is disorganised/confusing."
        ),
        evaluation_params=[P.INPUT, P.ACTUAL_OUTPUT],
        model=judge, threshold=THRESHOLD, async_mode=False,
    )
    return {"groundedness": groundedness, "correctness": correctness, "relevancy": relevancy}


def _measure(metric, tc) -> tuple[float, str]:
    metric.measure(tc)
    return round(float(metric.score or 0.0), 3), (metric.reason or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--category", type=str, default="")
    ap.add_argument("--out", type=str, default="eval/eval-results.json")
    args = ap.parse_args()

    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
    if args.limit:
        cases = cases[: args.limit]

    context = _load_context()

    from agents.base import cached_agent
    from utils.config import settings
    agent = cached_agent("ask_julian")
    judge = GrokJudge()
    metrics = _build_metrics(judge)

    print(f"Running {len(cases)} cases · judge={judge.get_model_name()} · "
          f"agent={settings().grok_model}\n")

    results = []
    for i, c in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {c['id']} ({c['category']})")
        answer = _answer(agent, c["question"])
        tc = LLMTestCase(
            input=c["question"],
            actual_output=answer,
            expected_output=c["reference"],
            context=context,
        )
        scores, reasons = {}, {}
        for key, metric in metrics.items():
            s, r = _measure(metric, tc)
            scores[key] = s
            reasons[key] = r
        passed = min(scores.values()) >= THRESHOLD
        print(f"    grounded={scores['groundedness']}  correct={scores['correctness']}  "
              f"relevant={scores['relevancy']}  -> {'PASS' if passed else 'FAIL'}")
        results.append({
            "id": c["id"], "category": c["category"], "question": c["question"],
            "guardrail": bool(c.get("guardrail")), "answer": answer,
            "scores": scores, "reasons": reasons, "passed": passed,
        })

    # ---- Aggregate ----
    def _mean(vals):
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    by_category = {
        cat: {
            "n": len(rs),
            "pass_rate": _mean([1.0 if x["passed"] else 0.0 for x in rs]),
            "mean_groundedness": _mean([x["scores"]["groundedness"] for x in rs]),
            "mean_correctness": _mean([x["scores"]["correctness"] for x in rs]),
            "mean_relevancy": _mean([x["scores"]["relevancy"] for x in rs]),
        }
        for cat, rs in by_cat.items()
    }
    summary = {
        "num_cases": len(results),
        "overall_pass_rate": _mean([1.0 if x["passed"] else 0.0 for x in results]),
        "mean_groundedness": _mean([x["scores"]["groundedness"] for x in results]),
        "mean_correctness": _mean([x["scores"]["correctness"] for x in results]),
        "mean_relevancy": _mean([x["scores"]["relevancy"] for x in results]),
        "by_category": by_category,
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": judge.get_model_name(),
        "agent_model": settings().grok_model,
        "threshold": THRESHOLD,
        "summary": summary,
        "cases": results,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(report, ROOT / "evals" / "EVAL_REPORT.md")

    print(f"\nOverall pass rate: {summary['overall_pass_rate']:.0%}  "
          f"(grounded {summary['mean_groundedness']}, correct {summary['mean_correctness']}, "
          f"relevant {summary['mean_relevancy']})")
    print(f"Wrote {out_path}")
    print(f"Wrote {ROOT / 'evals' / 'EVAL_REPORT.md'}")


def _write_markdown(report: dict, path: Path):
    s = report["summary"]
    lines = [
        "# Ask Julian — Eval Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Judge: `{report['judge_model']}` · Agent: `{report['agent_model']}` · "
        f"Threshold: {report['threshold']}",
        f"- **Overall pass rate: {s['overall_pass_rate']:.0%}** "
        f"({s['num_cases']} cases)",
        f"- Mean scores — Groundedness {s['mean_groundedness']}, "
        f"Correctness {s['mean_correctness']}, Relevancy {s['mean_relevancy']}",
        "",
        "## By category",
        "",
        "| Category | N | Pass rate | Grounded | Correct | Relevant |",
        "|---|---|---|---|---|---|",
    ]
    for cat, c in report["summary"]["by_category"].items():
        lines.append(f"| {cat} | {c['n']} | {c['pass_rate']:.0%} | "
                     f"{c['mean_groundedness']} | {c['mean_correctness']} | {c['mean_relevancy']} |")
    lines += ["", "## Cases", "",
              "| ID | Category | Pass | G | C | R |", "|---|---|---|---|---|---|"]
    for r in report["cases"]:
        sc = r["scores"]
        lines.append(f"| {r['id']} | {r['category']} | {'✅' if r['passed'] else '❌'} | "
                     f"{sc['groundedness']} | {sc['correctness']} | {sc['relevancy']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
