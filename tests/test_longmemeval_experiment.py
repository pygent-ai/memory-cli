import json
import tempfile
import unittest
from pathlib import Path

from experiments.longmemeval.scripts.codex.evaluate_run import evaluate_case
from experiments.longmemeval.scripts.codex.prepare_cases import prepare_cases
from experiments.longmemeval.scripts.codex.run_all import selected_case_ids
from experiments.longmemeval.scripts.codex.summarize_results import summarize
from experiments.longmemeval.scripts.codex.run_case import (
    complete_retrieval_from_answer,
    copy_memory_input,
    copy_private_eval,
    copy_question_input,
    create_case_venv,
    prepare_qa_input,
    normalize_answer_output,
    render_answer_prompt,
)


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
            self.assertEqual("case_0001", memory_input["question_id"])
            self.assertEqual("case_0001", question_input["question_id"])
            self.assertNotIn("oolong", json.dumps(question_input))
            self.assertNotIn("has_answer", serialized_memory)
            self.assertEqual(["session_0001"], private_eval["answer_session_ids"])
            self.assertEqual("session_0001", private_eval["session_id_map"]["answer_secret_a"])
            self.assertEqual("oolong", private_eval["answer"])
            self.assertEqual("What tea did I buy?", question_input["question"])
            self.assertEqual("case-1", private_eval["original_question_id"])

    def test_public_question_id_does_not_expose_abstention_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.json"
            out = root / "processed"
            item = self.sample_item()
            item["question_id"] = "case-1_abs"
            self.write_json(raw, [item])

            prepare_cases(raw, out)

            question_input = json.loads((out / "cases" / "case-1_abs" / "question_input.json").read_text(encoding="utf-8"))
            private_eval = json.loads((out / "private_eval" / "case-1_abs.json").read_text(encoding="utf-8"))
            self.assertEqual("case_0001", question_input["question_id"])
            self.assertNotIn("_abs", question_input["question_id"])
            self.assertTrue(private_eval["is_abstention"])

    def test_case_inputs_are_copied_by_stage_to_avoid_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.json"
            processed = root / "processed"
            case_dir = root / "run" / "cases" / "case-1"
            self.write_json(raw, [self.sample_item()])
            prepare_cases(raw, processed)

            copy_memory_input(processed, "case-1", case_dir)
            self.assertTrue((case_dir / "work" / "input" / "memory_input.json").is_file())
            self.assertFalse((case_dir / "work" / "input" / "question_input.json").exists())
            self.assertFalse((case_dir / "private_eval_ref.json").exists())

            copy_question_input(processed, "case-1", case_dir)
            self.assertTrue((case_dir / "work" / "input" / "question_input.json").is_file())
            self.assertFalse((case_dir / "private_eval_ref.json").exists())

            copy_private_eval(processed, "case-1", case_dir)
            self.assertTrue((case_dir / "private_eval_ref.json").is_file())

    def test_prepare_qa_input_removes_memory_input_from_agent_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.json"
            processed = root / "processed"
            case_dir = root / "run" / "cases" / "case-1"
            self.write_json(raw, [self.sample_item()])
            prepare_cases(raw, processed)
            copy_memory_input(processed, "case-1", case_dir)

            prepare_qa_input(processed, "case-1", case_dir)

            input_files = {path.name for path in (case_dir / "work" / "input").iterdir()}
            self.assertEqual({"question_input.json"}, input_files)
            self.assertFalse((case_dir / "private_eval_ref.json").exists())

    def test_case_venv_uses_supplied_template_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "snapshot"
            cli = template / "assets" / "default-memory-cli-py" / "src" / "memory_cli" / "cli.py"
            cli.parent.mkdir(parents=True)
            cli.write_text("print('snapshot')\n", encoding="utf-8")

            create_case_venv(root / "work", template)

            wrapper = root / "work" / ".venv" / "Scripts" / "memory-cli.cmd"
            self.assertIn(str(cli), wrapper.read_text(encoding="utf-8"))
            self.assertIn(str((root / "work" / ".venv" / "Scripts" / "python.exe").resolve()), wrapper.read_text(encoding="utf-8"))

    def test_render_answer_prompt_replaces_public_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_work = Path(tmp) / "work"
            self.write_json(
                case_work / "input" / "question_input.json",
                {
                    "question_id": "case_0001",
                    "question": "What tea did I buy?",
                    "question_date": "2024/01/03 (Wed) 10:00",
                },
            )
            prompt = render_answer_prompt(case_work)
            self.assertIn("What tea did I buy?", prompt)
            self.assertNotIn("{{QUESTION}}", prompt)

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

    def test_evaluate_case_maps_generic_id_and_source_to_source_session_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case-1"
            self.write_json(
                case_dir / "private_eval_ref.json",
                {
                    "question_id": "case-1",
                    "question_type": "temporal-reasoning",
                    "answer": "GPS system not functioning correctly",
                    "answer_session_ids": ["session_0002"],
                    "is_abstention": False,
                },
            )
            self.write_json(
                case_dir / "outputs" / "answer.json",
                {"answer": "The first issue was the GPS system not functioning correctly."},
            )
            self.write_json(
                case_dir / "outputs" / "retrieval.json",
                {
                    "queries": [
                        {
                            "query": "after first service GPS",
                            "latency_ms": 12,
                            "matches": [
                                {"id": "session_0001", "source": "LongMemEval case_0001 session_0001"},
                                {"id": "mem-gps-repair", "source": "LongMemEval case_0001 session_0002 session_0003"},
                            ],
                        }
                    ]
                },
            )

            metrics = evaluate_case(case_dir)

            self.assertEqual(["session_0001", "session_0002", "session_0003"], metrics["retrieved_ids"])
            self.assertEqual(0, metrics["recall_at_1"])
            self.assertEqual(1, metrics["recall_at_5"])

    def test_evaluate_case_counts_manual_reviewed_semantic_match_as_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case-1"
            self.write_json(
                case_dir / "private_eval_ref.json",
                {
                    "question_id": "case-1",
                    "question_type": "temporal-reasoning",
                    "answer": "GPS system not functioning correctly",
                    "answer_session_ids": ["session_0001"],
                    "is_abstention": False,
                },
            )
            self.write_json(
                case_dir / "outputs" / "answer.json",
                {"answer": "The first issue was a problem with the GPS system."},
            )
            self.write_json(
                case_dir / "outputs" / "retrieval.json",
                {"queries": [{"latency_ms": 12, "matches": [{"id": "session_0001"}]}]},
            )
            self.write_json(
                case_dir / "outputs" / "manual_review.json",
                {
                    "answer_correct": True,
                    "rationale": "Semantically matches the reference answer.",
                },
            )

            metrics = evaluate_case(case_dir)

            self.assertFalse(metrics["answer_substring_match"])
            self.assertTrue(metrics["manual_answer_match"])
            self.assertTrue(metrics["answer_correct"])

    def test_summarize_uses_answer_correct_without_losing_substring_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            self.write_json(
                run_dir / "cases" / "case-1" / "outputs" / "metrics.json",
                {
                    "question_type": "temporal-reasoning",
                    "recall_at_1": 1,
                    "recall_at_5": 1,
                    "recall_at_10": 1,
                    "ndcg_at_5": 1,
                    "ndcg_at_10": 1,
                    "answer_substring_match": False,
                    "manual_answer_match": True,
                    "answer_correct": True,
                    "search_latency_ms_total": 10,
                    "search_latency_ms_max": 10,
                },
            )
            self.write_json(
                run_dir / "cases" / "case-2" / "outputs" / "metrics.json",
                {
                    "question_type": "temporal-reasoning",
                    "recall_at_1": 1,
                    "recall_at_5": 1,
                    "recall_at_10": 1,
                    "ndcg_at_5": 1,
                    "ndcg_at_10": 1,
                    "answer_substring_match": True,
                    "manual_answer_match": None,
                    "answer_correct": True,
                    "search_latency_ms_total": 20,
                    "search_latency_ms_max": 20,
                },
            )

            summary = summarize(run_dir)

            self.assertEqual(0.5, summary["overall"]["answer_substring_match"])
            self.assertEqual(1.0, summary["overall"]["answer_correct"])
            self.assertEqual(1.0, summary["overall"]["manual_answer_match"])

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

    def test_complete_retrieval_from_answer_replays_structured_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "case-1"
            work_dir = case_dir / "work"
            scripts = work_dir / ".venv" / "Scripts"
            scripts.mkdir(parents=True)
            memory_dir = work_dir / ".memory"
            memory_dir.mkdir(parents=True)
            wrapper = scripts / "memory-cli.cmd"
            wrapper.write_text(
                '@echo off\r\n'
                'echo {"matches":[{"id":"session_0001","score":1.0,"content":"I bought oolong tea."}]}\r\n',
                encoding="utf-8",
            )
            self.write_json(
                case_dir / "outputs" / "answer.json",
                {
                    "question_id": "case_0001",
                    "answer": "oolong",
                    "search_queries_and_cli_results": [
                        {
                            "query": "oolong tea",
                            "cli_result_summary": "session_0001 matched",
                        }
                    ],
                },
            )

            retrieval = complete_retrieval_from_answer(case_dir)

            saved = json.loads((case_dir / "outputs" / "retrieval.json").read_text(encoding="utf-8"))
            self.assertEqual(retrieval, saved)
            self.assertEqual("case_0001", retrieval["question_id"])
            self.assertEqual("oolong tea", retrieval["queries"][0]["query"])
            self.assertEqual("session_0001", retrieval["queries"][0]["matches"][0]["id"])
            self.assertIsInstance(retrieval["queries"][0]["latency_ms"], float)

    def test_answer_prompt_requires_structured_search_query_records(self):
        prompt = (ROOT / "experiments" / "longmemeval" / "prompts" / "answer_from_memory.md").read_text(encoding="utf-8")
        self.assertIn('"search_queries_and_cli_results"', prompt)
        self.assertIn('"query"', prompt)
        self.assertIn('"cli_result_summary"', prompt)

    def test_build_prompt_requires_generic_source_mapping_on_memories(self):
        prompt = (ROOT / "experiments" / "longmemeval" / "prompts" / "build_memory.md").read_text(encoding="utf-8")
        self.assertIn("不要新增实验专属字段", prompt)
        self.assertIn("id", prompt)
        self.assertIn("source", prompt)
        self.assertNotIn("session_ids", prompt)

    def test_windows_cmd_entrypoints_exist_for_codex_experiment_scripts(self):
        scripts = ROOT / "experiments" / "longmemeval" / "scripts" / "codex"
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
        render_text = (scripts / "qa_stage_render_prompt.ps1").read_text(encoding="utf-8")
        write_text = (scripts / "qa_stage_write_answer.ps1").read_text(encoding="utf-8")
        self.assertIn("-Encoding UTF8", render_text)
        self.assertIn("-Encoding UTF8", write_text)
        self.assertIn("UTF8Encoding]::new($false)", render_text)
        self.assertIn("UTF8Encoding]::new($false)", write_text)

    def test_selected_case_ids_rejects_unknown_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            self.write_json(manifest, {"case_ids": ["case-a"]})

            with self.assertRaisesRegex(ValueError, "Unknown case id"):
                selected_case_ids(root, "case-missing", None)


if __name__ == "__main__":
    unittest.main()
