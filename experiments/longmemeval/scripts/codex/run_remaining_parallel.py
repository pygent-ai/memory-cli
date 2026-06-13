import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

try:
    from .run_all import copy_skill_snapshot, git_commit, read_json
    from .run_case import ROOT, run_case
    from .summarize_results import summarize
except ImportError:
    from run_all import copy_skill_snapshot, git_commit, read_json
    from run_case import ROOT, run_case
    from summarize_results import summarize


STATUS_LOCK = threading.Lock()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_case_ids(path):
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def selected_remaining(processed_dir, exclude_case_ids_path):
    manifest = read_json(Path(processed_dir) / "manifest.json")
    excluded = set(read_case_ids(exclude_case_ids_path))
    return [case_id for case_id in manifest["case_ids"] if case_id not in excluded]


def completed_case_ids(run_dir):
    cases_dir = Path(run_dir) / "cases"
    if not cases_dir.exists():
        return set()
    return {path.parent.parent.name for path in cases_dir.glob("*/outputs/metrics.json")}


def init_status(run_dir, all_case_ids, pending_case_ids, max_workers, agent_command, timeout_seconds):
    status = {
        "run_dir": str(Path(run_dir).resolve()),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "max_workers": max_workers,
        "agent_command": agent_command,
        "agent_timeout_seconds": timeout_seconds,
        "total_cases": len(all_case_ids),
        "completed_cases": 0,
        "failed_cases": 0,
        "running_cases": [],
        "pending_cases": pending_case_ids,
        "failures": [],
    }
    write_json(Path(run_dir) / "status.json", status)
    return status


def update_status(run_dir, mutator):
    path = Path(run_dir) / "status.json"
    with STATUS_LOCK:
        status = json.loads(path.read_text(encoding="utf-8"))
        mutator(status)
        write_json(path, status)
        return status


def mark_started(run_dir, case_id):
    def mutate(status):
        if case_id in status["pending_cases"]:
            status["pending_cases"].remove(case_id)
        if case_id not in status["running_cases"]:
            status["running_cases"].append(case_id)

    update_status(run_dir, mutate)


def mark_completed(run_dir, case_id):
    def mutate(status):
        if case_id in status["running_cases"]:
            status["running_cases"].remove(case_id)
        status["completed_cases"] += 1

    update_status(run_dir, mutate)


def mark_failed(run_dir, case_id, error):
    def mutate(status):
        if case_id in status["running_cases"]:
            status["running_cases"].remove(case_id)
        status["failed_cases"] += 1
        status["failures"].append({"case_id": case_id, "error": str(error)})

    update_status(run_dir, mutate)


def run_one(processed_dir, run_dir, case_id, agent_command, timeout_seconds, skill_snapshot, mock_agents):
    mark_started(run_dir, case_id)
    case_log = Path(run_dir) / "case-runner-logs" / f"{case_id}.json"
    started = time.perf_counter()
    try:
        metrics = run_case(
            processed_dir,
            case_id,
            run_dir,
            mock_agents=mock_agents,
            agent_command=agent_command,
            agent_timeout_seconds=timeout_seconds,
            skill_template=skill_snapshot,
        )
        write_json(
            case_log,
            {
                "case_id": case_id,
                "ok": True,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "metrics": metrics,
            },
        )
        summarize(run_dir)
        mark_completed(run_dir, case_id)
        return metrics
    except Exception as exc:
        write_json(
            case_log,
            {
                "case_id": case_id,
                "ok": False,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": str(exc),
            },
        )
        mark_failed(run_dir, case_id, exc)
        return None


def final_snapshot(run_dir, baseline_results_dir=None):
    run_dir = Path(run_dir)
    summary = summarize(run_dir)
    combined = {"new_run": summary}
    if baseline_results_dir:
        baseline_dir = Path(baseline_results_dir)
        baseline_metrics = read_json(baseline_dir / "combined_metrics.json")
        new_metrics = summary["overall"]
        baseline_count = int(baseline_metrics["case_count"])
        new_count = int(summary["case_count"])
        total = baseline_count + new_count
        combined["baseline"] = baseline_metrics
        combined["overall_merged"] = {
            "case_count": total,
            "answer_correct": weighted(
                baseline_metrics["overall"]["answer_correct"],
                baseline_count,
                new_metrics["answer_correct"],
                new_count,
            ),
            "answer_substring_match": weighted(
                baseline_metrics["overall"]["answer_substring_match"],
                baseline_count,
                new_metrics["answer_substring_match"],
                new_count,
            ),
            "recall_at_5": weighted(
                baseline_metrics["overall"]["recall_at_5"],
                baseline_count,
                new_metrics["recall_at_5"],
                new_count,
            ),
            "ndcg_at_5": weighted(
                baseline_metrics["overall"]["ndcg_at_5"],
                baseline_count,
                new_metrics["ndcg_at_5"],
                new_count,
            ),
        }
    write_json(run_dir / "final_snapshot.json", combined)
    return combined


def weighted(left_value, left_count, right_value, right_count):
    total = left_count + right_count
    if total == 0:
        return 0
    return round(((float(left_value) * left_count) + (float(right_value) * right_count)) / total, 4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--run-id", default="codex-remaining-209-bg")
    parser.add_argument("--run-dir")
    parser.add_argument("--exclude-case-ids", default="experiments/longmemeval/results/real-combined-291-latest/case_ids.txt")
    parser.add_argument("--baseline-results-dir", default="experiments/longmemeval/results/real-combined-291-latest")
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--agent-command", default="codex exec --ephemeral --skip-git-repo-check")
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--mock-agents", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir or ROOT / "experiments" / "longmemeval" / "runs" / args.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.max_workers < 1 or args.max_workers > 5:
        raise ValueError("--max-workers must be between 1 and 5")

    all_remaining = selected_remaining(args.processed_dir, args.exclude_case_ids)
    if args.limit is not None:
        all_remaining = all_remaining[: args.limit]
    done = completed_case_ids(run_dir)
    case_ids = [case_id for case_id in all_remaining if case_id not in done]
    (run_dir / "case_ids.txt").write_text("\n".join(all_remaining) + "\n", encoding="utf-8")

    config = {
        "processed_dir": args.processed_dir,
        "run_dir": str(run_dir),
        "exclude_case_ids": args.exclude_case_ids,
        "case_ids": all_remaining,
        "already_completed_in_run": sorted(done),
        "max_workers": args.max_workers,
        "agent_command": args.agent_command,
        "agent_timeout_seconds": args.agent_timeout_seconds,
        "mock_agents": args.mock_agents,
        "git_commit": git_commit(),
    }
    write_json(run_dir / "config.json", config)
    status = init_status(run_dir, all_remaining, case_ids, args.max_workers, args.agent_command, args.agent_timeout_seconds)
    status["completed_cases"] = len(done)
    write_json(run_dir / "status.json", status)

    skill_snapshot = copy_skill_snapshot(run_dir)

    if case_ids:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = [
                executor.submit(
                    run_one,
                    args.processed_dir,
                    run_dir,
                    case_id,
                    args.agent_command,
                    args.agent_timeout_seconds,
                    skill_snapshot,
                    args.mock_agents,
                )
                for case_id in case_ids
            ]
            for future in as_completed(futures):
                future.result()

    def finish(status):
        status["finished_at"] = datetime.now().isoformat(timespec="seconds")

    update_status(run_dir, finish)
    print(json.dumps(final_snapshot(run_dir, args.baseline_results_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
