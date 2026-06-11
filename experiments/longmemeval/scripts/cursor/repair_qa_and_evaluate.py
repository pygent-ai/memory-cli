import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUN_DEFAULT = ROOT / "experiments/longmemeval/runs-cursor/cursor-oracle-500-parallel"
PROCESSED_DEFAULT = ROOT / "datasets/longmemeval/processed/oracle"

sys.path.insert(0, str(ROOT))

from experiments.longmemeval.scripts.codex.evaluate_run import evaluate_case
from experiments.longmemeval.scripts.codex.run_case import (
    copy_private_eval,
    normalize_answer_output,
    write_json,
)
from experiments.longmemeval.scripts.codex.summarize_results import summarize


def read_agent_stdout(path):
    raw = Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if b"\x00" in raw[:200]:
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


def fix_unclosed_json_strings(block):
    lines = []
    for line in block.splitlines():
        stripped = line.strip()
        if (
            "cli_result_summary" in line
            or stripped.startswith('"notes"')
            or (stripped.startswith('"') and ": " in line and not stripped.endswith(","))
        ):
            if line.count('"') % 2 == 1:
                line = line.rstrip() + '"'
        lines.append(line)
    return "\n".join(lines)


def extract_json_object(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    candidates = []
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
        candidates.append(fix_unclosed_json_strings(text[start : end + 1]))

    stderr_match = re.search(r"\(\d+\):\s*(\{.*\})\s", text, flags=re.DOTALL)
    if stderr_match:
        candidates.append(stderr_match.group(1))
        candidates.append(fix_unclosed_json_strings(stderr_match.group(1)))

    decoder = json.JSONDecoder()
    fallback = None
    for candidate in candidates:
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                obj, _ = decoder.raw_decode(candidate[index:])
                if isinstance(obj, dict) and "answer" in obj:
                    return obj
                if fallback is None:
                    fallback = obj
            except json.JSONDecodeError:
                continue
    if fallback is not None:
        return fallback

    answer_match = re.search(r'"answer"\s*:\s*(".*?"|\d+)', text, flags=re.DOTALL)
    if answer_match:
        answer_raw = answer_match.group(1).strip('"')
        queries = re.findall(r'"query"\s*:\s*"([^"]+)"', text)
        notes_match = re.search(r'"notes"\s*:\s*"(.*?)"', text, flags=re.DOTALL)
        notes = notes_match.group(1) if notes_match else ""
        return {
            "answer": answer_raw,
            "search_queries_and_cli_results": [
                {"query": query, "cli_result_summary": ""} for query in queries
            ],
            "notes": notes,
        }

    prose_match = re.search(r"答案[为是]\s*\*?\*?(\d+)\*?\*?", text)
    if prose_match:
        return {
            "answer": prose_match.group(1),
            "search_queries_and_cli_results": [],
            "notes": "Recovered from QA prose output.",
        }
    raise ValueError("QA stdout did not contain a JSON object")


def ensure_memory_layout(case_dir):
    work_dir = case_dir / "work"
    dot_memory = work_dir / ".memory"
    if dot_memory.exists():
        return False

    moved = False
    dot_memory.mkdir(parents=True, exist_ok=True)
    for name in ("memories", "test-cases", "indexes", ".memory-index"):
        source = work_dir / name
        if source.exists():
            target = dot_memory / name
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(source), str(target))
            moved = True
    for name in ("memory.config.json",):
        source = work_dir / name
        if source.exists():
            shutil.copy2(source, dot_memory / name)
            moved = True
    return moved


def repair_case_answer(case_dir):
    stdout_path = case_dir / "logs/qa_stdout.txt"
    qa_log_path = case_dir / "logs/qa_stage_cmd.json"
    if not stdout_path.exists():
        return None, "missing qa_stdout.txt"

    question_path = case_dir / "work/input/question_input.json"
    if not question_path.exists():
        return None, "missing question_input.json"

    stdout = read_agent_stdout(stdout_path)
    parse_text = stdout
    if qa_log_path.exists():
        qa_log = json.loads(qa_log_path.read_text(encoding="utf-8"))
        parse_text = stdout + "\n" + (qa_log.get("stderr") or "")
    agent = extract_json_object(parse_text)
    question = json.loads(question_path.read_text(encoding="utf-8"))

    answer = agent.get("answer", "")
    if answer is None:
        answer = ""
    elif not isinstance(answer, str):
        answer = str(answer)

    result = {
        "question_id": question["question_id"],
        "question": question["question"],
        "question_date": question["question_date"],
        "answer": answer,
        "search_queries_and_cli_results": agent.get("search_queries_and_cli_results", []),
        "notes": str(agent.get("notes", "") or ""),
    }
    outputs = case_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    write_json(outputs / "answer.json", result)
    write_json(case_dir / "logs/qa_raw_agent_output.json", agent)
    return result, None


def should_repair(case_dir):
    answer_path = case_dir / "outputs/answer.json"
    if answer_path.exists():
        answer = json.loads(answer_path.read_text(encoding="utf-8"))
        if str(answer.get("answer", "")).strip():
            return False
    stdout_path = case_dir / "logs/qa_stdout.txt"
    if not stdout_path.exists() or stdout_path.stat().st_size == 0:
        return False
    qa_log = case_dir / "logs/qa_stage_cmd.json"
    if qa_log.exists():
        log = json.loads(qa_log.read_text(encoding="utf-8"))
        stderr = log.get("stderr") or ""
        if "ConvertFrom-Json" in stderr:
            return True
        if log.get("returncode", 0) != 0 and stdout_path.stat().st_size > 0:
            return True
    return stdout_path.stat().st_size > 0


def normalize_answer_file(case_dir):
    answer_path = case_dir / "outputs/answer.json"
    answer = json.loads(answer_path.read_text(encoding="utf-8"))
    value = answer.get("answer", "")
    if value is None:
        answer["answer"] = ""
    elif not isinstance(value, str):
        answer["answer"] = str(value)
    write_json(answer_path, answer)
    return answer


def evaluate_case_pipeline(case_dir, processed_dir):
    import subprocess
    import time

    ensure_memory_layout(case_dir)
    normalize_answer_file(case_dir)
    normalized = normalize_answer_output(case_dir)
    if not isinstance(normalized.get("answer"), str):
        normalized["answer"] = str(normalized.get("answer", ""))
        write_json(case_dir / "outputs/answer.json", normalized)

    case_dir = Path(case_dir)
    work_dir = case_dir / "work"
    answer = json.loads((case_dir / "outputs/answer.json").read_text(encoding="utf-8"))
    retrieval_path = case_dir / "outputs/retrieval.json"
    memory_root = work_dir / ".memory"
    if not retrieval_path.exists() and memory_root.exists():
        from experiments.longmemeval.scripts.codex.run_case import answer_search_queries, scripts_dir

        queries = []
        for query in answer_search_queries(answer):
            command = [
                str(scripts_dir(work_dir / ".venv") / "memory-cli.cmd"),
                "search",
                query,
            ]
            started = time.perf_counter()
            completed = subprocess.run(
                command,
                cwd=memory_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr or completed.stdout or f"search failed for {query}")
            result = json.loads(completed.stdout)
            queries.append(
                {
                    "query": query,
                    "latency_ms": round(latency_ms, 3),
                    "matches": result.get("matches", []),
                }
            )
        write_json(
            retrieval_path,
            {"question_id": answer.get("question_id") or case_dir.name, "queries": queries},
        )
    elif not retrieval_path.exists():
        write_json(
            retrieval_path,
            {"question_id": answer.get("question_id") or case_dir.name, "queries": []},
        )
    copy_private_eval(processed_dir, case_dir.name, case_dir)
    private_eval_path = case_dir / "private_eval_ref.json"
    private_eval = json.loads(private_eval_path.read_text(encoding="utf-8"))
    if not isinstance(private_eval.get("answer"), str):
        private_eval["answer"] = str(private_eval.get("answer", ""))
        write_json(private_eval_path, private_eval)
    return evaluate_case(case_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default=str(RUN_DEFAULT))
    parser.add_argument("--processed-dir", default=str(PROCESSED_DEFAULT))
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    processed_dir = Path(args.processed_dir)

    repaired = []
    repair_failed = []
    for case_dir in sorted((run_dir / "cases").iterdir()):
        if not case_dir.is_dir() or not should_repair(case_dir):
            continue
        try:
            _, error = repair_case_answer(case_dir)
            if error:
                repair_failed.append({"id": case_dir.name, "error": error})
            else:
                repaired.append(case_dir.name)
        except Exception as exc:
            repair_failed.append({"id": case_dir.name, "error": str(exc)})

    evaluated = []
    eval_failed = []
    for case_dir in sorted((run_dir / "cases").iterdir()):
        if not case_dir.is_dir() or not (case_dir / "outputs/answer.json").exists():
            continue
        try:
            evaluate_case_pipeline(case_dir, processed_dir)
            evaluated.append(case_dir.name)
        except Exception as exc:
            eval_failed.append({"id": case_dir.name, "error": str(exc)})

    summary = summarize(run_dir)
    report = {
        "repaired_count": len(repaired),
        "repaired_ids": repaired,
        "repair_failed": repair_failed,
        "evaluated_count": len(evaluated),
        "eval_failed": eval_failed,
        "summary": summary,
    }
    write_json(run_dir / "qa_repair_eval_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
