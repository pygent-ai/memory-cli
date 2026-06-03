import argparse
import json
import os
import shlex
import shutil
import subprocess
import time
import venv
from pathlib import Path

try:
    from .evaluate_run import evaluate_case
    from .judge_answer import mock_judge
except ImportError:
    from evaluate_run import evaluate_case
    from judge_answer import mock_judge


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = ROOT / "skills" / "memory-cli" / "assets" / "default-memory-cli-py"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def copy_inputs(processed_dir, question_id, case_dir):
    processed_dir = Path(processed_dir)
    input_dir = case_dir / "work" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(processed_dir / "cases" / question_id / "memory_input.json", input_dir / "memory_input.json")
    shutil.copy2(processed_dir / "cases" / question_id / "question_input.json", input_dir / "question_input.json")
    shutil.copy2(processed_dir / "private_eval" / f"{question_id}.json", case_dir / "private_eval_ref.json")


def scripts_dir(venv_dir):
    return venv_dir / ("Scripts" if os.name == "nt" else "bin")


def create_case_venv(work_dir):
    venv_dir = work_dir / ".venv"
    if not venv_dir.exists():
        venv.EnvBuilder(with_pip=False).create(venv_dir)

    wrapper = scripts_dir(venv_dir) / ("memory-cli.cmd" if os.name == "nt" else "memory-cli")
    python_exe = scripts_dir(venv_dir) / ("python.exe" if os.name == "nt" else "python")
    cli_path = TEMPLATE / "src" / "memory_cli" / "cli.py"
    if os.name == "nt":
        wrapper.write_text(
            f'@echo off\r\n"{python_exe}" "{cli_path}" %*\r\n',
            encoding="utf-8",
        )
    else:
        wrapper.write_text(
            f'#!/usr/bin/env sh\n"{python_exe}" "{cli_path}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
    return venv_dir


def run_memory_cli(work_dir, *args, cwd=None):
    command = [str(scripts_dir(work_dir / ".venv") / ("memory-cli.cmd" if os.name == "nt" else "memory-cli")), *args]
    completed = subprocess.run(command, cwd=cwd or work_dir, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def memory_content(session):
    lines = [f"Session {session['session_id']} at {session['timestamp']}."]
    for turn in session["turns"]:
        lines.append(f"{turn['role']}: {turn['content']}")
    return "\n".join(lines)


def mock_build_agent(work_dir):
    memory_input = read_json(work_dir / "input" / "memory_input.json")
    run_memory_cli(work_dir, "init", "--path", ".memory")
    memory_dir = work_dir / ".memory" / "memories"
    for index, session in enumerate(memory_input["sessions"]):
        content = memory_content(session)
        memory = {
            "id": session["session_id"],
            "priority": 80,
            "status": "active",
            "content": content,
            "queries": [
                session["session_id"],
                session["timestamp"],
                " ".join(content.split()[:24]),
            ],
            "must_include": [session["session_id"]],
            "tags": ["longmemeval", "session"],
            "source": f"LongMemEval {memory_input['question_id']} session {index}",
            "timestamp": session["timestamp"],
        }
        write_json(memory_dir / f"{session['session_id']}.json", memory)
    test_result = run_memory_cli(work_dir, "test", cwd=work_dir / ".memory")
    bench_result = run_memory_cli(work_dir, "bench", cwd=work_dir / ".memory")
    write_json(work_dir.parent / "logs" / "build_agent.json", {"mode": "mock", "test": test_result, "bench": bench_result})


def mock_qa_agent(work_dir):
    question = read_json(work_dir / "input" / "question_input.json")
    started = time.perf_counter()
    result = run_memory_cli(work_dir, "search", question["question"], cwd=work_dir / ".memory")
    latency_ms = (time.perf_counter() - started) * 1000
    matches = result.get("matches", [])
    answer = matches[0]["content"] if matches else "The information provided is not enough."
    write_json(
        work_dir.parent / "outputs" / "retrieval.json",
        {
            "question_id": question["question_id"],
            "queries": [
                {
                    "query": question["question"],
                    "latency_ms": round(latency_ms, 3),
                    "matches": matches,
                }
            ],
        },
    )
    write_json(
        work_dir.parent / "outputs" / "answer.json",
        {
            "answer": answer,
            "search_queries_and_cli_results": [
                json.dumps(
                    {
                        "query": question["question"],
                        "matches": [
                            {"id": match["id"], "score": match.get("score")}
                            for match in matches[:5]
                        ],
                    },
                    ensure_ascii=False,
                )
            ],
            "notes": "Mock QA returns the top retrieved memory content.",
        },
    )
    normalize_answer_output(work_dir.parent)
    write_json(work_dir.parent / "logs" / "qa_agent.json", {"mode": "mock"})


def load_prompt(path):
    return Path(path).read_text(encoding="utf-8").strip()


def render_answer_prompt(work_dir):
    question = read_json(work_dir / "input" / "question_input.json")
    template = load_prompt(ROOT / "experiments" / "longmemeval" / "prompts" / "answer_from_memory.md")
    question_text = f"{question['question']}\n\nQuestion date: {question['question_date']}"
    return template.replace("【QUESTION】", question_text)


def normalize_answer_output(case_dir):
    case_dir = Path(case_dir)
    answer_path = case_dir / "outputs" / "answer.json"
    work_answer_path = case_dir / "work" / "outputs" / "answer.json"
    if not answer_path.exists() and work_answer_path.exists():
        answer_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work_answer_path, answer_path)
    question = read_json(case_dir / "work" / "input" / "question_input.json")
    answer = read_json(answer_path)

    normalized = {
        "question_id": question["question_id"],
        "question": question["question"],
        "question_date": question["question_date"],
        "answer": answer.get("answer", ""),
        "search_queries_and_cli_results": answer.get("search_queries_and_cli_results", []),
        "notes": answer.get("notes", ""),
    }
    write_json(answer_path, normalized)
    return normalized


def run_real_agent(work_dir, agent_command, prompt_path, log_path, timeout_seconds, prompt_text=None):
    env = os.environ.copy()
    env["PATH"] = str(scripts_dir(work_dir / ".venv")) + os.pathsep + env.get("PATH", "")
    prompt = prompt_text if prompt_text is not None else load_prompt(prompt_path)
    command = [*shlex.split(agent_command), prompt]
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
        write_json(
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
        raise RuntimeError(f"Agent command timed out: {log_path}") from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    write_json(
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
        raise RuntimeError(f"Agent command failed: {log_path}")


def run_qa_stage_cmd(case_dir, agent_command, timeout_seconds):
    command = [
        str(ROOT / "experiments" / "longmemeval" / "scripts" / "qa_stage.cmd"),
        str(case_dir),
        agent_command,
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout_seconds,
    )
    write_json(
        Path(case_dir) / "logs" / "qa_stage_cmd.json",
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(f"QA stage cmd failed: {case_dir}")


def run_case(
    processed_dir,
    question_id,
    run_dir,
    mock_agents=False,
    agent_command="codex exec --skip-git-repo-check",
    agent_timeout_seconds=900,
):
    case_dir = Path(run_dir) / "cases" / question_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    (case_dir / "logs").mkdir(parents=True, exist_ok=True)
    (case_dir / "outputs").mkdir(parents=True, exist_ok=True)
    copy_inputs(processed_dir, question_id, case_dir)
    work_dir = case_dir / "work"
    create_case_venv(work_dir)

    if mock_agents:
        mock_build_agent(work_dir)
        mock_qa_agent(work_dir)
        mock_judge(case_dir)
    else:
        run_real_agent(
            work_dir,
            agent_command,
            ROOT / "experiments" / "longmemeval" / "prompts" / "build_memory.md",
            case_dir / "logs" / "build_agent.json",
            agent_timeout_seconds,
        )
        run_qa_stage_cmd(case_dir, agent_command, agent_timeout_seconds)

    return evaluate_case(case_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--agent-command", default="codex exec --skip-git-repo-check")
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
