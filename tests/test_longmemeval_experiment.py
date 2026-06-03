import json
import tempfile
import unittest
from pathlib import Path

from experiments.longmemeval.scripts.evaluate_run import evaluate_case
from experiments.longmemeval.scripts.prepare_cases import prepare_cases
from experiments.longmemeval.scripts.run_case import normalize_answer_output


ROOT = Path(__file__).resolve().parents[1]


class LongMemEvalExperimentTest(unittest.TestCase):
    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def sample_item(self):
        return {
            "question_id": "case-1",
            "question_type": "single-session-user",
            "question": "What tea did I buy?",
            "answer": "oolong",
            "question_date": "2024/01/03 (Wed) 10:00",
            "haystack_session_ids": ["answer_secret_a", "filler_secret_b"],
            "haystack_dates": ["2024/01/01 (Mon) 09:00", "2024/01/02 (Tue) 09:00"],
            "haystack_sessions": [
                [
                    {"role": "user", "content": "I bought oolong tea.", "has_answer": True},
                    {"role": "assistant", "content": "Nice choice."},
                ],
                [
                    {"role": "user", "content": "I like green mugs."},
                    {"role": "assistant", "content": "I'll remember that."},
                ],
            ],
            "answer_session_ids": ["answer_secret_a"],
        }

    def test_prepare_cases_separates_public_inputs_from_private_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.json"
            out = root / "processed"
            self.write_json(raw, [self.sample_item()])

            prepare_cases(raw, out)

            memory_input = json.loads((out / "cases" / "case-1" / "memory_input.json").read_text(encoding="utf-8"))
            question_input = json.loads((out / "cases" / "case-1" / "question_input.json").read_text(encoding="utf-8"))
            private_eval = json.loads((out / "private_eval" / "case-1.json").read_text(encoding="utf-8"))

            serialized_memory = json.dumps(memory_input)
            self.assertNotIn("What tea did I buy?", serialized_memory)
            self.assertNotIn("answer_secret_a", serialized_memory)
            self.assertNotIn("filler_secret_b", serialized_memory)
            self.assertNotIn("oolong", json.dumps(question_input))
            self.assertNotIn("has_answer", serialized_memory)
            self.assertEqual(["session_0001"], private_eval["answer_session_ids"])
            self.assertEqual("session_0001", private_eval["session_id_map"]["answer_secret_a"])
            self.assertEqual("oolong", private_eval["answer"])
            self.assertEqual("What tea did I buy?", question_input["question"])

    def test_evaluate_case_uses_retrieval_order_for_top_k_and_keeps_latency_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case-1"
            self.write_json(
                case_dir / "private_eval_ref.json",
                {
                    "question_id": "case-1",
                    "question_type": "single-session-user",
                    "answer": "oolong",
                    "answer_session_ids": ["session-a"],
                    "is_abstention": False,
                },
            )
            self.write_json(
                case_dir / "outputs" / "answer.json",
                {"question_id": "case-1", "answer": "oolong"},
            )
            self.write_json(
                case_dir / "outputs" / "retrieval.json",
                {
                    "queries": [
                        {
                            "query": "tea",
                            "latency_ms": 999,
                            "matches": [{"id": "session-b"}, {"id": "session-a"}],
                        }
                    ]
                },
            )

            metrics = evaluate_case(case_dir)

            self.assertEqual(0, metrics["recall_at_1"])
            self.assertEqual(1, metrics["recall_at_5"])
            self.assertEqual(999, metrics["search_latency_ms_max"])
            self.assertTrue(metrics["answer_substring_match"])

    def test_normalize_answer_output_adds_script_owned_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case-1"
            self.write_json(
                case_dir / "work" / "input" / "question_input.json",
                {
                    "question_id": "case-1",
                    "question": "What tea did I buy?",
                    "question_date": "2024/01/03 (Wed) 10:00",
                },
            )
            self.write_json(
                case_dir / "outputs" / "answer.json",
                {
                    "answer": "oolong",
                    "search_queries_and_cli_results": ["memory-cli search tea -> session_0001"],
                    "notes": "Found from memory search.",
                },
            )

            normalized = normalize_answer_output(case_dir)

            self.assertEqual("case-1", normalized["question_id"])
            self.assertEqual("What tea did I buy?", normalized["question"])
            self.assertEqual("oolong", normalized["answer"])
            self.assertEqual(["memory-cli search tea -> session_0001"], normalized["search_queries_and_cli_results"])

    def test_windows_cmd_entrypoints_exist_for_experiment_scripts(self):
        scripts = ROOT / "experiments" / "longmemeval" / "scripts"
        python_wrappers = [
            "download_dataset",
            "prepare_cases",
            "run_case",
            "run_all",
            "evaluate_run",
            "summarize_results",
            "judge_answer",
        ]
        for name in python_wrappers:
            cmd = scripts / f"{name}.cmd"
            self.assertTrue(cmd.is_file(), f"missing {cmd}")
            self.assertIn(f"{name}.py", cmd.read_text(encoding="utf-8"))

        qa_stage = scripts / "qa_stage.cmd"
        self.assertTrue(qa_stage.is_file())
        qa_stage_text = qa_stage.read_text(encoding="utf-8")
        self.assertIn("qa_stage_render_prompt.ps1", qa_stage_text)
        self.assertIn("qa_stage_write_answer.ps1", qa_stage_text)


if __name__ == "__main__":
    unittest.main()
