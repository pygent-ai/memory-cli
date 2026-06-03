import argparse
import json
import shlex
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def substring_label(reference, hypothesis):
    reference = (reference or "").strip().lower()
    hypothesis = (hypothesis or "").strip().lower()
    if not hypothesis:
        return "unknown"
    if reference and (reference in hypothesis or hypothesis in reference):
        return "correct"
    return "wrong"


def build_judge_input(case_dir):
    case_dir = Path(case_dir)
    question = read_json(case_dir / "work" / "input" / "question_input.json")
    private_eval = read_json(case_dir / "private_eval_ref.json")
    answer = read_json(case_dir / "outputs" / "answer.json")
    return {
        "question_id": question["question_id"],
        "question": question["question"],
        "question_type": private_eval["question_type"],
        "reference_answer": private_eval["answer"],
        "hypothesis": answer.get("answer", ""),
    }


def mock_judge(case_dir):
    payload = build_judge_input(case_dir)
    label = substring_label(payload["reference_answer"], payload["hypothesis"])
    result = {
        "question_id": payload["question_id"],
        "autoeval_label": label,
        "rationale": "Mock judge uses case-insensitive substring matching.",
    }
    write_json(Path(case_dir) / "outputs" / "judge.json", result)
    return result


def codex_judge(case_dir, agent_command, timeout_seconds):
    case_dir = Path(case_dir)
    payload = build_judge_input(case_dir)
    prompt = (ROOT / "experiments" / "longmemeval" / "prompts" / "judge_answer.md").read_text(encoding="utf-8")
    full_prompt = prompt + "\n\nInput JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
    command = [*shlex.split(agent_command), full_prompt]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=case_dir,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        log = {
            "command": command,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
        write_json(case_dir / "logs" / "judge_agent.json", log)
        raise

    log = {
        "command": command,
        "timed_out": False,
        "returncode": completed.returncode,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    write_json(case_dir / "logs" / "judge_agent.json", log)
    if completed.returncode != 0:
        raise RuntimeError("Codex judge command failed")

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {
            "question_id": payload["question_id"],
            "autoeval_label": "unknown",
            "rationale": "Judge output was not valid JSON.",
            "raw_output": completed.stdout,
        }
    result.setdefault("question_id", payload["question_id"])
    write_json(case_dir / "outputs" / "judge.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--agent-command", default="codex exec --skip-git-repo-check")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    result = mock_judge(args.case_dir) if args.mock else codex_judge(args.case_dir, args.agent_command, args.timeout_seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
