import argparse
import json
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CURSOR_SCRIPTS = Path(__file__).resolve().parent
DEFAULT_RUNS_DIR = ROOT / "experiments" / "longmemeval" / "runs-cursor"
DEFAULT_AGENT_COMMAND = "agent -p --trust --force"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CURSOR_SCRIPTS))

from experiments.longmemeval.scripts.codex.run_all import copy_skill_snapshot, git_commit, selected_case_ids
from experiments.longmemeval.scripts.codex.summarize_results import summarize
from run_case import run_case

progress_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def case_metrics_path(run_dir, question_id):
    return Path(run_dir) / "cases" / question_id / "outputs" / "metrics.json"


def is_case_complete(run_dir, question_id):
    return case_metrics_path(run_dir, question_id).exists()


def append_runner_log(run_dir, message):
    log_path = Path(run_dir) / "runner.log"
    with progress_lock:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{utc_now()}] {message}\n")


def update_progress(progress_path, progress, runner_log=None):
    progress["updated_at"] = utc_now()
    write_json(progress_path, progress)
    if runner_log:
        append_runner_log(progress_path.parent, runner_log)


def run_one_case(
    processed_dir,
    question_id,
    run_dir,
    skill_snapshot,
    agent_command,
    agent_timeout_seconds,
    mock_agents,
):
    metrics = run_case(
        processed_dir,
        question_id,
        run_dir,
        mock_agents=mock_agents,
        agent_command=agent_command,
        agent_timeout_seconds=agent_timeout_seconds,
        skill_template=skill_snapshot,
    )
    return metrics


def run_all_parallel(
    processed_dir,
    run_dir,
    cases="all",
    limit=None,
    mock_agents=False,
    agent_command=DEFAULT_AGENT_COMMAND,
    agent_timeout_seconds=900,
    workers=5,
    resume=True,
):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    skill_snapshot = copy_skill_snapshot(run_dir)
    case_ids = selected_case_ids(processed_dir, cases, limit)

    progress_path = run_dir / "progress.json"
    failures_path = run_dir / "failures.json"

    if progress_path.exists():
        progress = read_json(progress_path)
        progress.setdefault("cases", {})
    else:
        config = {
            "runner": "cursor-parallel",
            "processed_dir": str(processed_dir),
            "cases": cases,
            "case_ids": case_ids,
            "workers": workers,
            "mock_agents": mock_agents,
            "agent_command": agent_command,
            "agent_timeout_seconds": agent_timeout_seconds,
            "git_commit": git_commit(),
            "qa_stage_cmd": str(CURSOR_SCRIPTS / "qa_stage.cmd"),
        }
        write_json(run_dir / "config.json", config)
        progress = {
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "started_at": utc_now(),
            "updated_at": utc_now(),
            "total": len(case_ids),
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "running": [],
            "pending": [],
            "workers": workers,
            "cases": {},
        }

    pending = []
    skipped = 0
    for question_id in case_ids:
        existing = progress["cases"].get(question_id, {})
        if resume and is_case_complete(run_dir, question_id):
            if existing.get("status") != "completed":
                progress["cases"][question_id] = {
                    "status": "completed",
                    "resumed_from_disk": True,
                    "updated_at": utc_now(),
                }
            skipped += 1
            continue
        if existing.get("status") == "completed" and is_case_complete(run_dir, question_id):
            skipped += 1
            continue
        pending.append(question_id)

    def recount():
        progress["completed"] = sum(
            1 for question_id in case_ids if progress["cases"].get(question_id, {}).get("status") == "completed"
        )
        progress["failed"] = sum(
            1 for question_id in case_ids if progress["cases"].get(question_id, {}).get("status") == "failed"
        )

    progress["total"] = len(case_ids)
    progress["skipped"] = skipped
    progress["pending"] = pending.copy()
    recount()
    update_progress(progress_path, progress, f"starting parallel run with {len(pending)} pending case(s), workers={workers}")

    failures = read_json(failures_path) if failures_path.exists() else []

    def mark_running(question_id):
        with progress_lock:
            if question_id in progress["pending"]:
                progress["pending"].remove(question_id)
            if question_id not in progress["running"]:
                progress["running"].append(question_id)
            progress["cases"][question_id] = {
                "status": "running",
                "started_at": utc_now(),
                "updated_at": utc_now(),
            }
            update_progress(progress_path, progress)

    def mark_done(question_id, result):
        with progress_lock:
            if question_id in progress["running"]:
                progress["running"].remove(question_id)
            progress["cases"][question_id] = {
                **result,
                "updated_at": utc_now(),
            }
            if result["status"] == "completed":
                recount()
                update_progress(
                    progress_path,
                    progress,
                    f"completed {question_id} ({progress['completed']}/{progress['total']})",
                )
            else:
                recount()
                failures.append(
                    {
                        "question_id": question_id,
                        "error": result.get("error"),
                        "traceback": result.get("traceback"),
                        "updated_at": utc_now(),
                    }
                )
                write_json(failures_path, failures)
                update_progress(
                    progress_path,
                    progress,
                    f"failed {question_id}: {result.get('error')}",
                )

    def run_one_case_tracked(question_id):
        mark_running(question_id)
        try:
            metrics = run_one_case(
                processed_dir,
                question_id,
                run_dir,
                skill_snapshot,
                agent_command,
                agent_timeout_seconds,
                mock_agents,
            )
            mark_done(
                question_id,
                {
                    "status": "completed",
                    "finished_at": utc_now(),
                    "metrics": metrics,
                },
            )
            return metrics
        except Exception as exc:
            mark_done(
                question_id,
                {
                    "status": "failed",
                    "finished_at": utc_now(),
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(run_one_case_tracked, question_id): question_id for question_id in pending
        }
        for future in as_completed(future_map):
            future.result()

    summary = summarize(run_dir)
    progress["finished_at"] = utc_now()
    progress["summary"] = summary
    progress["pending"] = []
    progress["running"] = []
    update_progress(progress_path, progress, "parallel run finished")
    write_json(run_dir / "final_summary.json", summary)
    return {"run_dir": str(run_dir), "summary": summary, "progress": progress}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir")
    parser.add_argument("--cases", default="all")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--agent-command", default=DEFAULT_AGENT_COMMAND)
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--mock-agents", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or f"cursor-oracle-500-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = args.run_dir or str(DEFAULT_RUNS_DIR / run_id)
    result = run_all_parallel(
        args.processed_dir,
        run_dir,
        cases=args.cases,
        limit=args.limit,
        mock_agents=args.mock_agents,
        agent_command=args.agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
        workers=args.workers,
        resume=not args.no_resume,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
