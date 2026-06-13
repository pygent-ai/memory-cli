import argparse
import json
import math
import re
from pathlib import Path


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dcg(relevances):
    return sum(rel / math.log2(index + 2) for index, rel in enumerate(relevances))


def ndcg_at(ranked_ids, evidence_ids, k):
    evidence = set(evidence_ids)
    if not evidence:
        return 1.0
    relevances = [1 if item_id in evidence else 0 for item_id in ranked_ids[:k]]
    ideal_count = min(len(evidence), k)
    ideal = [1] * ideal_count + [0] * (k - ideal_count)
    ideal_dcg = dcg(ideal)
    return dcg(relevances) / ideal_dcg if ideal_dcg else 0.0


def recall_at(ranked_ids, evidence_ids, k):
    evidence = set(evidence_ids)
    if not evidence:
        return 1.0
    return len(evidence.intersection(ranked_ids[:k])) / len(evidence)


def match_session_ids(match):
    ids = []
    for field in ("session_ids", "source_session_ids"):
        value = match.get(field)
        if isinstance(value, list):
            ids.extend(item for item in value if isinstance(item, str))
    value = match.get("session_id")
    if isinstance(value, str):
        ids.append(value)

    source = match.get("source")
    if isinstance(source, str):
        ids.extend(re.findall(r"session_\d{4}", source))
        for grouped in re.findall(r"sessions_([0-9_]+)", source):
            ids.extend(f"session_{item}" for item in grouped.split("_") if len(item) == 4)

    if not ids and isinstance(match.get("id"), str):
        ids.append(match["id"])
    return ids


def flatten_retrieval_ids(retrieval):
    ids = []
    for query in retrieval.get("queries", []):
        for match in query.get("matches", []):
            for item_id in match_session_ids(match):
                if item_id and item_id not in ids:
                    ids.append(item_id)
    return ids


def answer_matches(reference, hypothesis):
    reference = "" if reference is None else str(reference).strip().lower()
    hypothesis = "" if hypothesis is None else str(hypothesis).strip().lower()
    if not reference or not hypothesis:
        return False
    return reference in hypothesis or hypothesis in reference


def manual_answer_match(case_dir):
    review = load_json(Path(case_dir) / "outputs" / "manual_review.json", {})
    value = review.get("answer_correct")
    return value if isinstance(value, bool) else None


def evaluate_case(case_dir):
    case_dir = Path(case_dir)
    private_eval = load_json(case_dir / "private_eval_ref.json", {})
    answer = load_json(case_dir / "outputs" / "answer.json", {})
    retrieval = load_json(case_dir / "outputs" / "retrieval.json", {"queries": []})

    ranked_ids = flatten_retrieval_ids(retrieval)
    evidence_ids = private_eval.get("answer_session_ids", [])
    hypothesis = answer.get("answer", "")
    reference = private_eval.get("answer", "")
    is_abstention = private_eval.get("is_abstention", False)
    substring_match = answer_matches(reference, hypothesis)
    reviewed_match = manual_answer_match(case_dir)

    latencies = [
        query.get("latency_ms", 0)
        for query in retrieval.get("queries", [])
        if isinstance(query.get("latency_ms", 0), (int, float))
    ]

    metrics = {
        "question_id": private_eval.get("question_id") or case_dir.name,
        "question_type": private_eval.get("question_type"),
        "is_abstention": is_abstention,
        "retrieved_ids": ranked_ids,
        "recall_at_1": recall_at(ranked_ids, evidence_ids, 1),
        "recall_at_5": recall_at(ranked_ids, evidence_ids, 5),
        "recall_at_10": recall_at(ranked_ids, evidence_ids, 10),
        "ndcg_at_5": ndcg_at(ranked_ids, evidence_ids, 5),
        "ndcg_at_10": ndcg_at(ranked_ids, evidence_ids, 10),
        "answer_substring_match": substring_match,
        "manual_answer_match": reviewed_match,
        "answer_correct": substring_match or reviewed_match is True,
        "abstention_answered": bool(hypothesis.strip()) if is_abstention else None,
        "search_latency_ms_total": round(sum(latencies), 3),
        "search_latency_ms_max": round(max(latencies), 3) if latencies else 0,
    }
    out_path = case_dir / "outputs" / "metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    args = parser.parse_args()
    print(json.dumps(evaluate_case(args.case_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
