import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "experiments/longmemeval/runs-cursor/cursor-oracle-500-parallel/cases"


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path, limit=300):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def classify(case_dir):
    qid = case_dir.name
    if (case_dir / "outputs/answer.json").exists():
        return None

    build_log = case_dir / "logs/build_agent.json"
    qa_log = case_dir / "logs/qa_stage_cmd.json"
    qa_stderr = case_dir / "logs/qa_stderr.txt"
    qa_stdout = case_dir / "logs/qa_stdout.txt"
    memory = case_dir / "work/.memory"
    build_input = case_dir / "work/input/memory_input.json"
    question_input = case_dir / "work/input/question_input.json"

    if not build_log.exists():
        return "no_build_log", "build 尚未开始或尚无日志"

    build = load_json(build_log)
    if build.get("timed_out"):
        return "build_timeout", f"build 超时（{build.get('timeout_seconds')}s）"
    if build.get("returncode", 0) not in (0, None):
        detail = read_text(case_dir / "logs/build_agent.json")
        stderr = build.get("stderr") or ""
        stdout = build.get("stdout") or ""
        return "build_failed", (stderr or stdout or detail)[:300]

    if build_input.exists() and not question_input.exists():
        return "build_running", "仍在 build 阶段（memory_input 还在）"

    if question_input.exists() and not memory.exists():
        return "build_incomplete", "已切到 QA 输入，但 .memory 项目缺失"

    if qa_log.exists():
        qa = load_json(qa_log)
        if qa.get("returncode", 0) != 0:
            detail = (qa.get("stderr") or qa.get("stdout") or read_text(qa_stderr))[:300]
            return "qa_cmd_failed", detail or "qa_stage.cmd 非零退出"
        return "qa_no_answer", "qa_stage.cmd 成功但未写出 answer.json"

    if qa_stderr.exists() and qa_stderr.stat().st_size > 0:
        return "qa_agent_failed", read_text(qa_stderr)

    if qa_stdout.exists() and qa_stdout.stat().st_size > 0 and not (case_dir / "outputs/answer.json").exists():
        stdout = read_text(qa_stdout)
        if "JSON" in stdout or "{" in stdout:
            return "qa_parse_pending", "qa stdout 有内容但 answer 解析/写入未完成"
        return "qa_agent_failed", stdout[:300] or "qa agent 无有效输出"

    if question_input.exists() and memory.exists():
        return "qa_not_started", "build 已完成，QA 尚未开始或正在排队/执行"

    return "unknown", "状态不明"


def main():
    reasons = Counter()
    samples = {}
    details = []

    for case_dir in sorted(RUN.iterdir()):
        if not case_dir.is_dir():
            continue
        result = classify(case_dir)
        if result is None:
            continue
        category, detail = result
        reasons[category] += 1
        details.append({"id": case_dir.name, "category": category, "detail": detail})
        samples.setdefault(category, [])
        if len(samples[category]) < 2:
            samples[category].append({"id": case_dir.name, "detail": detail})

    total_no_qa = sum(reasons.values())
    print(
        json.dumps(
            {
                "total_no_qa": total_no_qa,
                "qa_finished": len(list(RUN.glob("*/outputs/answer.json"))),
                "breakdown": dict(reasons),
                "samples": samples,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
