import argparse
import json
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path


def is_memory_project(path):
    return (path / "memory.config.json").exists() or (path / "memories").is_dir()


def resolve_memory_root(start=None):
    current = Path(start or Path.cwd()).resolve()
    if is_memory_project(current):
        return current
    if is_memory_project(current / ".memory"):
        return current / ".memory"
    for parent in current.parents:
        candidate = parent / ".memory"
        if is_memory_project(candidate):
            return candidate
    return current


ROOT = resolve_memory_root()
MEMORY_DIR = ROOT / "memories"
CONFIG_PATH = ROOT / "memory.config.json"


def set_paths(next_root):
    global ROOT, MEMORY_DIR, CONFIG_PATH
    ROOT = resolve_memory_root(next_root)
    MEMORY_DIR = ROOT / "memories"
    CONFIG_PATH = ROOT / "memory.config.json"


def memory_project_exists():
    return is_memory_project(ROOT)


def missing_project_error():
    return {
        "error": "memory_project_not_found",
        "path": str(ROOT),
        "message": "No memory project found. Run from a memory project or a parent directory containing .memory.",
    }


def load_config():
    if not CONFIG_PATH.exists():
        return {
            "priority_thresholds": {"blocking_failure": 80, "warning_failure": 40},
            "performance_budget_ms": {"p95_search": 200, "full_test_suite": 5000},
        }
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def tokenize(text):
    return [part for part in re.split(r"\W+", text.lower()) if part]


def load_memories():
    memories = []
    for path in sorted(MEMORY_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path)
        memories.append(data)
    return memories


def active_memories():
    return [
        memory
        for memory in load_memories()
        if memory.get("status", "active") != "retired"
    ]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def memory_path(memory_id):
    for memory in load_memories():
        if memory.get("id") == memory_id:
            return Path(memory["_path"])
    return MEMORY_DIR / f"{memory_id}.json"


def public_memory(memory):
    return {key: value for key, value in memory.items() if key != "_path"}


def init_project(root=None):
    root = Path(root or ROOT)
    memories = root / "memories"
    config = root / "memory.config.json"
    memories.mkdir(parents=True, exist_ok=True)
    if not config.exists():
        write_json(
            config,
            {
                "priority_thresholds": {
                    "blocking_failure": 80,
                    "warning_failure": 40,
                },
                "performance_budget_ms": {
                    "p95_search": 200,
                    "full_test_suite": 5000,
                },
            },
        )
    return {"status": "initialized", "root": str(root), "memories": str(memories)}


def list_memories():
    memories = [
        {
            "id": memory.get("id"),
            "priority": memory.get("priority", 0),
            "status": memory.get("status", "active"),
            "tags": memory.get("tags", []),
            "source": memory.get("source"),
        }
        for memory in load_memories()
    ]
    memories.sort(key=lambda item: (item["priority"], item["id"] or ""), reverse=True)
    return {"memories": memories}


def show_memory(memory_id):
    for memory in load_memories():
        if memory.get("id") == memory_id:
            return {"memory": public_memory(memory)}
    return {"error": "not_found", "id": memory_id}


def validate_memory(memory):
    required = ["id", "priority", "content", "queries", "must_include"]
    missing = [field for field in required if field not in memory]
    if missing:
        return {"valid": False, "missing": missing}
    if not isinstance(memory.get("queries"), list) or not memory["queries"]:
        return {"valid": False, "missing": ["queries"]}
    return {"valid": True, "missing": []}


def check_conflicts(candidate):
    validation = validate_memory(candidate)
    if not validation["valid"]:
        return {"valid": False, "conflicts": [], "missing": validation["missing"]}

    conflicts = []
    for query in candidate.get("queries", []):
        result = search(query)
        matching_ids = [
            item["id"]
            for item in result["matches"]
            if item["id"] != candidate.get("id")
            and any(
                phrase.lower() in item["content"].lower()
                for phrase in candidate.get("must_include", [])
            )
        ]
        if matching_ids:
            conflicts.append({"query": query, "matching_ids": matching_ids})

    return {"valid": True, "conflicts": conflicts}


def add_memory(candidate, force=False):
    conflicts = check_conflicts(candidate)
    if not conflicts.get("valid"):
        return {"status": "invalid", **conflicts}
    if conflicts["conflicts"] and not force:
        return {"status": "conflict", **conflicts}

    path = memory_path(candidate["id"])
    if path.exists() and not force:
        return {"status": "exists", "id": candidate["id"], "path": str(path)}

    write_json(path, candidate)
    return {"status": "added", "id": candidate["id"], "path": str(path)}


def update_memory(memory_id, updates):
    path = memory_path(memory_id)
    if not path.exists():
        return {"status": "not_found", "id": memory_id}

    memory = json.loads(path.read_text(encoding="utf-8"))
    memory.update(updates)
    memory["id"] = memory_id
    memory["updated_at"] = date.today().isoformat()
    write_json(path, memory)
    return {"status": "updated", "id": memory_id, "path": str(path)}


def retire_memory(memory_id, reason=None):
    updates = {"status": "retired", "retired_at": date.today().isoformat()}
    if reason:
        updates["retired_reason"] = reason
    result = update_memory(memory_id, updates)
    if result["status"] == "updated":
        result["status"] = "retired"
    return result


def read_json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_memory(memory, query):
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0

    fields = [
        ("content", memory.get("content", ""), 3),
        ("tags", " ".join(memory.get("tags", [])), 2),
        ("aliases", " ".join(memory.get("aliases", [])), 2),
        ("keywords", " ".join(memory.get("keywords", [])), 2),
        ("id", memory.get("id", ""), 1),
    ]

    score = 0
    for token in query_tokens:
        for _, value, weight in fields:
            value_tokens = tokenize(value)
            if token in value_tokens:
                score += weight
            elif token in value.lower():
                score += max(1, weight - 1)

    if query.lower() in memory.get("content", "").lower():
        score += 8

    return score


def search(query):
    matches = []

    for memory in active_memories():
        score = score_memory(memory, query)
        if score > 0:
            matches.append(
                {
                    "id": memory["id"],
                    "priority": memory.get("priority", 0),
                    "score": score,
                    "content": memory.get("content", ""),
                    "tags": memory.get("tags", []),
                    "source": memory.get("source"),
                }
            )

    matches.sort(key=lambda item: (item["priority"], item["score"]), reverse=True)
    return {"query": query, "matches": matches}


def search_many(queries):
    return {"queries": [search(query) for query in queries]}


def run_tests():
    started = time.perf_counter()
    config = load_config()
    blocking_priority = config["priority_thresholds"]["blocking_failure"]
    failures = []
    total = 0

    for memory in active_memories():
        for query in memory.get("queries", []):
            total += 1
            result = search(query)
            matched = next(
                (
                    item
                    for item in result["matches"]
                    if item["id"] == memory["id"]
                    and all(
                        phrase.lower() in item["content"].lower()
                        for phrase in memory.get("must_include", [])
                    )
                ),
                None,
            )
            if matched is None:
                failures.append(
                    {
                        "memory_id": memory["id"],
                        "priority": memory.get("priority", 0),
                        "query": query,
                        "expected": memory.get("must_include", []),
                        "found_ids": [item["id"] for item in result["matches"]],
                    }
                )

    elapsed_ms = (time.perf_counter() - started) * 1000
    blocking = [f for f in failures if f["priority"] >= blocking_priority]
    return {
        "total": total,
        "failed": len(failures),
        "blocking_failed": len(blocking),
        "elapsed_ms": round(elapsed_ms, 3),
        "failures": failures,
    }


def percentile(values, percent):
    if not values:
        return 0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * percent))
    return ordered[index]


def bench():
    started = time.perf_counter()
    latencies = []
    memories = active_memories()
    for memory in memories:
        for query in memory.get("queries", []):
            query_start = time.perf_counter()
            search(query)
            latencies.append((time.perf_counter() - query_start) * 1000)

    total_ms = (time.perf_counter() - started) * 1000
    return {
        "memories": len(memories),
        "queries": len(latencies),
        "p50_search_ms": round(statistics.median(latencies), 3) if latencies else 0,
        "p95_search_ms": round(percentile(latencies, 0.95), 3),
        "full_suite_ms": round(total_ms, 3),
        "budget_ms": load_config()["performance_budget_ms"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="UT-driven memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--path", default=".")

    search_parser = sub.add_parser("search")
    search_parser.add_argument("query", nargs="+")

    check_parser = sub.add_parser("check-conflicts")
    check_parser.add_argument("--file", required=True)

    add_parser = sub.add_parser("add")
    add_parser.add_argument("--file", required=True)
    add_parser.add_argument("--force", action="store_true")

    sub.add_parser("list")

    show_parser = sub.add_parser("show")
    show_parser.add_argument("id")

    update_parser = sub.add_parser("update")
    update_parser.add_argument("id")
    update_parser.add_argument("--file", required=True)

    retire_parser = sub.add_parser("retire")
    retire_parser.add_argument("id")
    retire_parser.add_argument("--reason")

    sub.add_parser("test")
    sub.add_parser("bench")

    args = parser.parse_args(argv)

    if args.command != "init" and not memory_project_exists():
        print(json.dumps(missing_project_error(), ensure_ascii=False, indent=2))
        return 1

    handlers = {
        "init": lambda: (init_project(args.path), 0),
        "search": lambda: (
            search(args.query[0]) if len(args.query) == 1 else search_many(args.query),
            0,
        ),
        "check-conflicts": lambda: (check_conflicts(read_json_file(args.file)), 0),
        "add": lambda: _add_command(args),
        "list": lambda: (list_memories(), 0),
        "show": lambda: _status_command(show_memory(args.id)),
        "update": lambda: _status_command(update_memory(args.id, read_json_file(args.file))),
        "retire": lambda: _status_command(retire_memory(args.id, args.reason)),
        "test": lambda: _test_command(),
        "bench": lambda: (bench(), 0),
    }

    result, code = handlers[args.command]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


def _add_command(args):
    result = add_memory(read_json_file(args.file), force=args.force)
    return result, 1 if result["status"] in {"conflict", "invalid", "exists"} else 0


def _status_command(result):
    status = result.get("status")
    error = result.get("error")
    return result, 1 if status == "not_found" or error else 0


def _test_command():
    result = run_tests()
    return result, 1 if result["blocking_failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
