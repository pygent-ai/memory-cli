import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CURSOR_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CURSOR_SCRIPTS))

from experiments.longmemeval.scripts.codex import run_case as base
from experiments.longmemeval.scripts.codex.evaluate_run import evaluate_case

from agent_utils import build_agent_argv

DEFAULT_AGENT_COMMAND = "agent -p --trust --force"
QA_STAGE_CMD = CURSOR_SCRIPTS / "qa_stage.cmd"


def run_real_agent(work_dir, agent_command, prompt_path, log_path, timeout_seconds, prompt_text=None):
    env = os.environ.copy()
    env["PATH"] = str(base.scripts_dir(work_dir / ".venv")) + os.pathsep + env.get("PATH", "")
    prompt = prompt_text if prompt_text is not None else base.load_prompt(prompt_path)
    work_dir = Path(work_dir).resolve()
    command = build_agent_argv(agent_command, ["--workspace", str(work_dir), prompt])
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=work_dir,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        base.write_json(
            log_path,
            {
                "command": command,
                "timed_out": True,
                "timeout_seconds": timeout_seconds,
                "elapsed_ms": round(elapsed_ms, 3),
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
        )
        raise RuntimeError(f"Cursor agent command timed out: {log_path}") from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    base.write_json(
        log_path,
        {
            "command": command,
            "timed_out": False,
            "returncode": completed.returncode,
            "elapsed_ms": round(elapsed_ms, 3),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Cursor agent command failed: {log_path}")


def run_qa_stage_cmd(case_dir, agent_command, timeout_seconds):
    case_dir = Path(case_dir).resolve()
    command = [str(QA_STAGE_CMD), str(case_dir), agent_command]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout_seconds,
    )
    base.write_json(
        Path(case_dir) / "logs" / "qa_stage_cmd.json",
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Cursor QA stage cmd failed: {case_dir}")


def run_case(
    processed_dir,
    question_id,
    run_dir,
    mock_agents=False,
    agent_command=DEFAULT_AGENT_COMMAND,
    agent_timeout_seconds=900,
    skill_template=None,
):
    case_dir = Path(run_dir) / "cases" / question_id
    if case_dir.exists():
        import shutil

        shutil.rmtree(case_dir)
    (case_dir / "logs").mkdir(parents=True, exist_ok=True)
    (case_dir / "outputs").mkdir(parents=True, exist_ok=True)
    base.copy_memory_input(processed_dir, question_id, case_dir)
    work_dir = case_dir / "work"
    base.create_case_venv(work_dir, skill_template or base.TEMPLATE)

    if mock_agents:
        base.mock_build_agent(work_dir)
        base.prepare_qa_input(processed_dir, question_id, case_dir)
        base.mock_qa_agent(work_dir)
        base.copy_private_eval(processed_dir, question_id, case_dir)
        base.mock_judge(case_dir)
    else:
        run_real_agent(
            work_dir,
            agent_command,
            ROOT / "experiments" / "longmemeval" / "prompts" / "build_memory.md",
            case_dir / "logs" / "build_agent.json",
            agent_timeout_seconds,
        )
        base.prepare_qa_input(processed_dir, question_id, case_dir)
        run_qa_stage_cmd(case_dir, agent_command, agent_timeout_seconds)
        base.complete_retrieval_from_answer(case_dir)
        base.copy_private_eval(processed_dir, question_id, case_dir)

    return evaluate_case(case_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--agent-command", default=DEFAULT_AGENT_COMMAND)
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--mock-agents", action="store_true")
    args = parser.parse_args()

    metrics = run_case(
        args.processed_dir,
        args.question_id,
        args.run_dir,
        mock_agents=args.mock_agents,
        agent_command=args.agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
