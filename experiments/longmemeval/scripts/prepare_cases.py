import argparse
import json
from pathlib import Path


PRIVATE_TURN_KEYS = {"has_answer"}


def sanitize_turn(turn):
    return {key: value for key, value in turn.items() if key not in PRIVATE_TURN_KEYS}


def session_id_map(item):
    return {
        session_id: f"session_{index + 1:04d}"
        for index, session_id in enumerate(item["haystack_session_ids"])
    }


def build_memory_input(item, id_map):
    sessions = []
    for session_id, timestamp, turns in zip(
        item["haystack_session_ids"],
        item["haystack_dates"],
        item["haystack_sessions"],
    ):
        sessions.append(
            {
                "session_id": id_map[session_id],
                "timestamp": timestamp,
                "turns": [sanitize_turn(turn) for turn in turns],
            }
        )
    return {"question_id": item["question_id"], "sessions": sessions}


def build_question_input(item):
    return {
        "question_id": item["question_id"],
        "question": item["question"],
        "question_date": item["question_date"],
    }


def build_private_eval(item, id_map):
    evidence_turns = []
    for session_id, timestamp, turns in zip(
        item["haystack_session_ids"],
        item["haystack_dates"],
        item["haystack_sessions"],
    ):
        for turn_index, turn in enumerate(turns):
            if turn.get("has_answer"):
                evidence_turns.append(
                    {
                        "session_id": id_map[session_id],
                        "original_session_id": session_id,
                        "timestamp": timestamp,
                        "turn_index": turn_index,
                        "role": turn.get("role"),
                        "content": turn.get("content", ""),
                    }
                )

    return {
        "question_id": item["question_id"],
        "question_type": item["question_type"],
        "answer": item["answer"],
        "answer_session_ids": [
            id_map[session_id]
            for session_id in item.get("answer_session_ids", [])
            if session_id in id_map
        ],
        "session_id_map": id_map,
        "evidence_turns": evidence_turns,
        "is_abstention": item["question_id"].endswith("_abs"),
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare_cases(raw_path, out_dir, limit=None):
    raw_path = Path(raw_path)
    out_dir = Path(out_dir)
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    if limit is not None:
        data = data[:limit]

    case_ids = []
    for item in data:
        question_id = item["question_id"]
        id_map = session_id_map(item)
        case_dir = out_dir / "cases" / question_id
        write_json(case_dir / "memory_input.json", build_memory_input(item, id_map))
        write_json(case_dir / "question_input.json", build_question_input(item))
        write_json(out_dir / "private_eval" / f"{question_id}.json", build_private_eval(item, id_map))
        case_ids.append(question_id)

    manifest = {
        "source": str(raw_path),
        "case_count": len(case_ids),
        "case_ids": case_ids,
    }
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="datasets/longmemeval/raw/longmemeval_oracle.json")
    parser.add_argument("--out-dir", default="datasets/longmemeval/processed/oracle")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    print(json.dumps(prepare_cases(args.raw, args.out_dir, args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
