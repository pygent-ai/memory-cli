import argparse
import json
import sys
from datetime import datetime
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


def run_all(
    processed_dir,
    run_dir,
    cases="smoke",
    limit=None,
    mock_agents=False,
    agent_command=DEFAULT_AGENT_COMMAND,
    agent_timeout_seconds=900,
):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    skill_snapshot = copy_skill_snapshot(run_dir)
    case_ids = selected_case_ids(processed_dir, cases, limit)
    config = {
        "runner": "cursor",
        "processed_dir": str(processed_dir),
        "cases": cases,
        "case_ids": case_ids,
        "mock_agents": mock_agents,
        "agent_command": agent_command,
        "agent_timeout_seconds": agent_timeout_seconds,
        "git_commit": git_commit(),
        "qa_stage_cmd": str(CURSOR_SCRIPTS / "qa_stage.cmd"),
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
                skill_template=skill_snapshot,
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
    parser.add_argument("--agent-command", default=DEFAULT_AGENT_COMMAND)
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--mock-agents", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or f"cursor-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = args.run_dir or str(DEFAULT_RUNS_DIR / run_id)
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
