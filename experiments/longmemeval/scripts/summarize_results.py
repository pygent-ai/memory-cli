import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


METRIC_KEYS = [
    "recall_at_1",
    "recall_at_5",
    "recall_at_10",
    "ndcg_at_5",
    "ndcg_at_10",
    "answer_substring_match",
    "search_latency_ms_total",
    "search_latency_ms_max",
]


def mean(values):
    return statistics.mean(values) if values else 0


def load_metrics(run_dir):
    metrics = []
    for path in sorted((Path(run_dir) / "cases").glob("*/outputs/metrics.json")):
        metrics.append(json.loads(path.read_text(encoding="utf-8")))
    return metrics


def summarize(run_dir):
    metrics = load_metrics(run_dir)
    summary = {"case_count": len(metrics), "overall": {}, "by_question_type": {}}
    for key in METRIC_KEYS:
        values = [float(item[key]) for item in metrics if item.get(key) is not None]
        summary["overall"][key] = round(mean(values), 4)

    grouped = defaultdict(list)
    for item in metrics:
        grouped[item.get("question_type") or "unknown"].append(item)
    for question_type, items in sorted(grouped.items()):
        summary["by_question_type"][question_type] = {}
        for key in METRIC_KEYS:
            values = [float(item[key]) for item in items if item.get(key) is not None]
            summary["by_question_type"][question_type][key] = round(mean(values), 4)

    out_path = Path(run_dir) / "aggregate_metrics.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.run_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
