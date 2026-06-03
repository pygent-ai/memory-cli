import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from run_case import ROOT, run_case
from summarize_results import summarize


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def copy_skill_snapshot(run_dir):
    source = ROOT / "skills" / "memory-cli"
    target = Path(run_dir) / "skill_snapshot" / "memory-cli"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("*.zip"))


def git_commit():
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def selected_case_ids(processed_dir, cases, limit):
    manifest = read_json(Path(processed_dir) / "manifest.json")
    ids = manifest["case_ids"]
    if cases != "all":
        wanted = [item.strip() for item in cases.split(",") if item.strip()]
        if cases == "smoke":
            wanted = ids[: limit or 3]
        ids = wanted
    if limit is not None:
        ids = ids[:limit]
    return ids


def run_all(
    processed_dir,
    run_dir,
    cases="smoke",
    limit=None,
    mock_agents=False,
    agent_command="codex exec --skip-git-repo-check",
    agent_timeout_seconds=900,
):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    copy_skill_snapshot(run_dir)
    case_ids = selected_case_ids(processed_dir, cases, limit)
    config = {
        "processed_dir": str(processed_dir),
        "cases": cases,
        "case_ids": case_ids,
        "mock_agents": mock_agents,
        "agent_command": agent_command,
        "agent_timeout_seconds": agent_timeout_seconds,
        "git_commit": git_commit(),
    }
    (run_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    metrics = []
    for question_id in case_ids:
        metrics.append(
            run_case(
                processed_dir,
                question_id,
                run_dir,
                mock_agents=mock_agents,
                agent_command=agent_command,
                agent_timeout_seconds=agent_timeout_seconds,
            )
        )
    summary = summarize(run_dir)
    return {"run_dir": str(run_dir), "case_metrics": metrics, "summary": summary}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir")
    parser.add_argument("--cases", default="smoke")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--agent-command", default="codex exec --skip-git-repo-check")
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--mock-agents", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = args.run_dir or str(ROOT / "experiments" / "longmemeval" / "runs" / run_id)
    result = run_all(
        args.processed_dir,
        run_dir,
        cases=args.cases,
        limit=args.limit,
        mock_agents=args.mock_agents,
        agent_command=args.agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
