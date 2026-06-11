"""Export completed Cursor run metrics into experiments/longmemeval/results/."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from experiments.longmemeval.scripts.cursor.check_qa_accuracy import (
    semantic_match,
    substring_match,
)

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RUN_DIR = ROOT / "experiments/longmemeval/runs-cursor/cursor-oracle-500-parallel"
DEFAULT_OUT_DIR = ROOT / "experiments/longmemeval/results/cursor-oracle-500-qa83"
PRIVATE_EVAL = ROOT / "datasets/longmemeval/processed/oracle/private_eval"

METRIC_KEYS = [
    "recall_at_1",
    "recall_at_5",
    "recall_at_10",
    "ndcg_at_5",
    "ndcg_at_10",
    "answer_substring_match",
    "manual_answer_match",
    "answer_correct",
    "search_latency_ms_total",
    "search_latency_ms_max",
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_per_case(run_dir: Path) -> list[dict]:
    rows = []
    for metrics_path in sorted((run_dir / "cases").glob("*/outputs/metrics.json")):
        case_id = metrics_path.parents[1].name
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        row = {"case_id": case_id, **metrics}
        rows.append(row)
    return rows


def qa_accuracy(run_dir: Path, case_ids: list[str]) -> dict:
    rows = []
    for case_id in case_ids:
        answer_path = run_dir / "cases" / case_id / "outputs/answer.json"
        if not answer_path.exists():
            continue
        answer = json.loads(answer_path.read_text(encoding="utf-8"))
        ref_data = json.loads((PRIVATE_EVAL / f"{case_id}.json").read_text(encoding="utf-8"))
        ref = ref_data["answer"]
        hyp = answer.get("answer", "")
        rows.append(
            {
                "id": case_id,
                "substring": substring_match(ref, hyp),
                "semantic": semantic_match(ref, hyp),
            }
        )
    sub_ok = sum(row["substring"] for row in rows)
    sem_ok = sum(row["semantic"] for row in rows)
    return {
        "qa_finished": len(rows),
        "substring_correct": sub_ok,
        "substring_accuracy": round(sub_ok / len(rows), 4) if rows else 0,
        "semantic_correct": sem_ok,
        "semantic_accuracy": round(sem_ok / len(rows), 4) if rows else 0,
    }


def build_combined(run_dir: Path, snapshot_name: str, per_case: list[dict]) -> dict:
    overall = {}
    for key in METRIC_KEYS:
        if key in ("answer_substring_match", "manual_answer_match", "answer_correct"):
            values = [1.0 if item.get(key) else 0.0 for item in per_case if item.get(key) is not None]
        else:
            values = [float(item[key]) for item in per_case if item.get(key) is not None]
        overall[key] = round(mean(values), 4)

    by_type: dict[str, dict] = {}
    grouped = defaultdict(list)
    for item in per_case:
        grouped[item.get("question_type") or "unknown"].append(item)
    for question_type, items in sorted(grouped.items()):
        by_type[question_type] = {}
        for key in METRIC_KEYS:
            if key in ("answer_substring_match", "manual_answer_match", "answer_correct"):
                values = [1.0 if item.get(key) else 0.0 for item in items if item.get(key) is not None]
            else:
                values = [float(item[key]) for item in items if item.get(key) is not None]
            by_type[question_type][key] = round(mean(values), 4)

    by_type_counts = {}
    for question_type, items in sorted(grouped.items()):
        by_type_counts[question_type] = {
            "case_count": len(items),
            "correct_count": sum(1 for item in items if item.get("answer_correct")),
            "strict_correct_count": sum(1 for item in items if item.get("answer_substring_match")),
            "manual_true_count": sum(1 for item in items if item.get("manual_answer_match") is True),
            "manual_false_count": sum(1 for item in items if item.get("manual_answer_match") is False),
        }

    failed_case_ids = sorted(case["case_id"] for case in per_case if not case.get("answer_correct"))
    strict_correct_count = sum(1 for case in per_case if case.get("answer_substring_match"))
    correct_count = sum(1 for case in per_case if case.get("answer_correct"))

    qa = qa_accuracy(run_dir, [case["case_id"] for case in per_case])
    overall.update(
        {
            "correct_count": correct_count,
            "failed_count": len(failed_case_ids),
            "strict_correct_count": strict_correct_count,
            "manual_true_count": sum(1 for case in per_case if case.get("manual_answer_match") is True),
            "manual_false_count": sum(1 for case in per_case if case.get("manual_answer_match") is False),
            "semantic_accuracy": qa["semantic_accuracy"],
            "semantic_correct_count": qa["semantic_correct"],
        }
    )

    return {
        "snapshot_name": snapshot_name,
        "agent": "cursor",
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "case_count": len(per_case),
        "run_id": run_dir.name,
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
        "dataset": "longmemeval_oracle",
        "target_case_count": 500,
        "completion_note": "Interim snapshot: only cases with completed QA and metrics are included.",
        "source_counts": {run_dir.name: len(per_case)},
        "selection_policy": "Include every case under the Cursor run that has outputs/metrics.json.",
        "overall": overall,
        "by_question_type": by_type,
        "by_question_type_counts": by_type_counts,
        "qa_accuracy": qa,
        "failed_case_ids": failed_case_ids,
    }


def write_results_md(out_dir: Path, combined: dict) -> None:
    overall = combined["overall"]
    qa = combined["qa_accuracy"]
    lines = [
        "# LongMemEval Cursor Results",
        "",
        "This directory contains an interim unified result set for Cursor Agent runs on LongMemEval oracle.",
        "",
        "## Scope",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| Completed cases with metrics | {combined['case_count']} |",
        f"| Target oracle cases | {combined['target_case_count']} |",
        f"| Strict substring correct | {overall['strict_correct_count']} |",
        f"| Harness answer correct | {overall['correct_count']} |",
        f"| Still failed (harness) | {overall['failed_count']} |",
        f"| Semantic heuristic correct | {qa['semantic_correct']} |",
        "",
        "## Run Metadata",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Agent | Cursor |",
        f"| Run id | `{combined['run_id']}` |",
        f"| Run dir | `{combined['run_dir']}` |",
        f"| Snapshot | `{combined['snapshot_name']}` |",
        f"| Created at | {combined['created_at']} |",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| recall@1 | {overall['recall_at_1']:.4f} |",
        f"| recall@5 | {overall['recall_at_5']:.4f} |",
        f"| recall@10 | {overall['recall_at_10']:.4f} |",
        f"| ndcg@5 | {overall['ndcg_at_5']:.4f} |",
        f"| ndcg@10 | {overall['ndcg_at_10']:.4f} |",
        f"| strict substring accuracy | {overall['answer_substring_match']:.4f} |",
        f"| harness answer accuracy | {overall['answer_correct']:.4f} |",
        f"| semantic heuristic accuracy | {qa['semantic_accuracy']:.4f} |",
        f"| average total search latency ms | {overall['search_latency_ms_total']:.4f} |",
        f"| average max search latency ms | {overall['search_latency_ms_max']:.4f} |",
        "",
        "## Metrics By Question Type",
        "",
        "| Question type | Cases | Correct | Accuracy | recall@5 | Strict correct |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for question_type, counts in combined["by_question_type_counts"].items():
        metrics = combined["by_question_type"][question_type]
        lines.append(
            f"| {question_type} | {counts['case_count']} | {counts['correct_count']} | "
            f"{metrics['answer_correct']:.4f} | {metrics['recall_at_5']:.4f} | "
            f"{counts['strict_correct_count']} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is a partial Cursor run snapshot, not the full 500-case oracle benchmark.",
            "- Most incomplete cases failed during the build stage because Cursor usage limits were reached.",
            "- QA JSON repair was applied before evaluation for cases with recoverable `qa_stdout.txt`.",
            "- Compare with Codex results in `results/real-combined-291-latest/`.",
            "",
            "## Files",
            "",
            "- `combined_metrics.json`: aggregate metrics and counts for the Cursor result set.",
            "- `per_case_metrics.json`: one metrics record per completed case.",
            "- `source_map.json`: maps each case to the Cursor run directory.",
            "- `case_ids.txt`: all included case ids.",
            "- `failed_case_ids.txt`: cases marked incorrect by harness substring matching.",
            "",
        ]
    )
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_snapshot(run_dir: Path, out_dir: Path, snapshot_name: str) -> dict:
    per_case = load_per_case(run_dir)
    combined = build_combined(run_dir, snapshot_name, per_case)
    source_map = {
        case["case_id"]: {
            "agent": "cursor",
            "run_id": run_dir.name,
            "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
            "case_dir": f"{run_dir.relative_to(ROOT).as_posix()}/cases/{case['case_id']}",
        }
        for case in per_case
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "combined_metrics.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "per_case_metrics.json").write_text(
        json.dumps(per_case, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_map.json").write_text(
        json.dumps(source_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "case_ids.txt").write_text(
        "\n".join(case["case_id"] for case in per_case) + "\n",
        encoding="utf-8",
    )
    (out_dir / "failed_case_ids.txt").write_text(
        "\n".join(combined["failed_case_ids"]) + ("\n" if combined["failed_case_ids"] else ""),
        encoding="utf-8",
    )
    write_results_md(out_dir, combined)
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Cursor run metrics to results/")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--snapshot-name", default=DEFAULT_OUT_DIR.name)
    args = parser.parse_args()
    summary = export_snapshot(Path(args.run_dir), Path(args.out_dir), args.snapshot_name)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
