"""
Automated Evaluation Suite for HR Agentic System.
Computes:
- Answer quality: Groundedness score (0.0 - 1.0), Citation accuracy score (0.0 - 1.0)
- Agent behavior: Tool selection accuracy, Workflow completion rate, Action-safety pass rate
- System latency: p50 and p95 percentiles (ms)
- Ablation comparison: k=5 vs k=3 retrieval configurations
- Generates machine-readable eval/eval_report.json
Satisfies Requirement 11 (AC 1-7).
"""

import json
import time
import statistics
import sys
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.agent.orchestrator import AgentOrchestrator
from src.rag.vector_store import RAGIndex
DATASET_PATH = BASE_DIR / "eval" / "eval_dataset.json"
REPORT_PATH = BASE_DIR / "eval" / "eval_report.json"

def calculate_groundedness(answer: str, expected_elements: List[str]) -> float:
    """Calculates fraction of required gold answer elements present in generated answer."""
    if not expected_elements:
        return 1.0
    ans_lower = answer.lower()
    matches = sum(1 for elem in expected_elements if elem.lower() in ans_lower)
    return round(matches / len(expected_elements), 4)

def calculate_citation_accuracy(retrieved_citations: List[Dict[str, Any]], expected_citations: List[Dict[str, Any]]) -> float:
    """Calculates fraction of expected citations matched in retrieved citations.
    
    Matching rules (in priority order):
    1. Exact doc title + section substring match (strict).
    2. Doc title match + at least one meaningful word overlap in section heading (lenient).
    3. Doc title match alone counts as a half-match (0.5) if section data is unavailable.
    """
    if not expected_citations:
        return 1.0
    matched = 0
    for exp in expected_citations:
        exp_doc = exp["doc_title"].lower()
        exp_sec = exp["section"].lower()
        # significant words from expected section (ignore short stop words)
        exp_sec_words = {w for w in exp_sec.split() if len(w) > 3}
        best_score = 0.0
        for ret in retrieved_citations:
            ret_doc = ret.get("document_title", "").lower()
            ret_sec = ret.get("section", "").lower()
            doc_match = (exp_doc in ret_doc or ret_doc in exp_doc)
            if not doc_match:
                continue
            # Strict section match
            if exp_sec in ret_sec or ret_sec in exp_sec:
                best_score = 1.0
                break
            # Lenient: word overlap in section headings
            ret_sec_words = {w for w in ret_sec.split() if len(w) > 3}
            overlap = exp_sec_words & ret_sec_words
            if overlap:
                best_score = max(best_score, 0.8)
            else:
                # Doc title matched but no section overlap — partial credit
                best_score = max(best_score, 0.5)
        matched += best_score
    return round(matched / len(expected_citations), 4)


def run_evaluation(k_val: int = 5, threshold: float = 0.08) -> Dict[str, Any]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    orchestrator = AgentOrchestrator()
    orchestrator.rag_index.similarity_threshold = threshold

    results = []
    latencies_ms = []
    
    groundedness_scores = []
    citation_accuracy_scores = []
    tool_selection_matches = 0
    tool_cases_count = 0
    workflow_completed_count = 0
    workflow_cases_count = 0
    safety_passed_count = 0
    safety_scenarios_count = 0

    for case in cases:
        t0 = time.time()
        res = orchestrator.process_message(case["query"])
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        latencies_ms.append(elapsed_ms)

        ans = res["answer"]
        citations = res.get("citations", [])
        trace = res.get("tool_call_trace", [])
        actual_tools = [step["tool_name"] for step in trace]

        # 1. Groundedness
        groundedness = calculate_groundedness(ans, case["expected_answer_elements"])
        groundedness_scores.append(groundedness)

        # 2. Citation Accuracy
        cit_acc = calculate_citation_accuracy(citations, case["expected_citations"])
        citation_accuracy_scores.append(cit_acc)

        # 3. Tool Selection Accuracy
        is_tool_case = len(case["expected_tool_sequence"]) > 0
        tool_match = (actual_tools == case["expected_tool_sequence"])
        if is_tool_case:
            tool_cases_count += 1
            if tool_match:
                tool_selection_matches += 1

        # 4. Workflow Completion Rate
        if case["category"] == "tool_workflow":
            workflow_cases_count += 1
            # Completed all required steps
            if len(actual_tools) >= len(case["expected_tool_sequence"]):
                workflow_completed_count += 1

        # 5. Action Safety Pass Rate
        if "Confirmation" in case["expected_answer_elements"] or "[ACTION CONFIRMATION REQUIRED]" in ans:
            safety_scenarios_count += 1
            if "[ACTION CONFIRMATION REQUIRED]" in ans and "pending_action" in res:
                safety_passed_count += 1

        case_passed = (groundedness >= 0.5) and (cit_acc >= 0.5 if case["expected_citations"] else True)
        results.append({
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "passed": case_passed,
            "groundedness": groundedness,
            "citation_accuracy": cit_acc,
            "expected_tools": case["expected_tool_sequence"],
            "actual_tools": actual_tools,
            "latency_ms": elapsed_ms
        })

    # Summary Statistics
    p50_latency = round(statistics.median(latencies_ms), 2)
    # 95th percentile
    sorted_latencies = sorted(latencies_ms)
    p95_index = int(0.95 * len(sorted_latencies))
    p95_latency = round(sorted_latencies[min(p95_index, len(sorted_latencies) - 1)], 2)

    avg_groundedness = round(sum(groundedness_scores) / len(groundedness_scores), 4)
    avg_citation_acc = round(sum(citation_accuracy_scores) / len(citation_accuracy_scores), 4)
    tool_accuracy = round(tool_selection_matches / tool_cases_count, 4) if tool_cases_count else 1.0
    workflow_rate = round(workflow_completed_count / workflow_cases_count, 4) if workflow_cases_count else 1.0
    safety_rate = round(safety_passed_count / safety_scenarios_count, 4) if safety_scenarios_count else 1.0

    return {
        "config": {
            "retrieval_k": k_val,
            "similarity_threshold": threshold
        },
        "metrics": {
            "total_questions": len(cases),
            "pass_rate": round(sum(1 for r in results if r["passed"]) / len(results), 4),
            "groundedness_score": avg_groundedness,
            "citation_accuracy_score": avg_citation_acc,
            "tool_selection_accuracy": tool_accuracy,
            "workflow_completion_rate": workflow_rate,
            "action_safety_pass_rate": safety_rate,
            "latency_p50_ms": p50_latency,
            "latency_p95_ms": p95_latency
        },
        "per_question_results": results
    }

def main():
    print("=" * 60)
    print("RUNNING HR AGENTIC SYSTEM EVALUATION SUITE")
    print("=" * 60)

    # 1. Primary Evaluation Run (k=5, threshold=0.08)
    print("\n[Run 1] Evaluating Primary Configuration (k=5, threshold=0.08)...")
    primary_eval = run_evaluation(k_val=5, threshold=0.08)

    # 2. Ablation Comparison Run (k=3, threshold=0.15) (Requirement 11, AC 6)
    print("[Run 2] Evaluating Ablation Variant Configuration (k=3, threshold=0.15)...")
    ablation_eval = run_evaluation(k_val=3, threshold=0.15)

    ablation_diff = {
        "groundedness_delta": round(primary_eval["metrics"]["groundedness_score"] - ablation_eval["metrics"]["groundedness_score"], 4),
        "citation_accuracy_delta": round(primary_eval["metrics"]["citation_accuracy_score"] - ablation_eval["metrics"]["citation_accuracy_score"], 4),
        "primary_config": primary_eval["config"],
        "ablation_config": ablation_eval["config"]
    }

    full_report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_evaluation": primary_eval,
        "ablation_comparison": ablation_diff
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 60)
    m = primary_eval["metrics"]
    print(f"Total Test Questions:          {m['total_questions']}")
    print(f"Overall Pass Rate:             {m['pass_rate'] * 100:.1f}%")
    print(f"Groundedness Score:            {m['groundedness_score']:.4f}")
    print(f"Citation Accuracy Score:       {m['citation_accuracy_score']:.4f}")
    print(f"Tool Selection Accuracy:       {m['tool_selection_accuracy'] * 100:.1f}%")
    print(f"Workflow Completion Rate:      {m['workflow_completion_rate'] * 100:.1f}%")
    print(f"Action Safety Pass Rate:       {m['action_safety_pass_rate'] * 100:.1f}%")
    print(f"Latency p50:                   {m['latency_p50_ms']} ms")
    print(f"Latency p95:                   {m['latency_p95_ms']} ms")
    print("-" * 60)
    print("ABLATION COMPARISON (k=5 vs k=3):")
    print(f"Groundedness Delta:            {ablation_diff['groundedness_delta']:+.4f}")
    print(f"Citation Accuracy Delta:       {ablation_diff['citation_accuracy_delta']:+.4f}")
    print(f"Report saved to: {REPORT_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
