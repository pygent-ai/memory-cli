import json
import contextlib
import io
import tempfile
import unittest
import tomllib
from pathlib import Path
from unittest.mock import patch

from memory_cli import cli as memory_cli


class MemoryCliBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.memory_dir = self.root / "memories"
        self.memory_dir.mkdir()
        self.config_path = self.root / "memory.config.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "priority_thresholds": {
                        "blocking_failure": 80,
                        "warning_failure": 40,
                    },
                    "performance_budget_ms": {
                        "p95_search": 200,
                        "full_test_suite": 5000,
                    },
                    "result_limit": 1,
                }
            ),
            encoding="utf-8",
        )
        self.old_memory_dir = memory_cli.MEMORY_DIR
        self.old_config_path = memory_cli.CONFIG_PATH
        memory_cli.MEMORY_DIR = self.memory_dir
        memory_cli.CONFIG_PATH = self.config_path

    def tearDown(self):
        memory_cli.MEMORY_DIR = self.old_memory_dir
        memory_cli.CONFIG_PATH = self.old_config_path
        self.tmp.cleanup()

    def write_memory(self, name, **data):
        (self.memory_dir / f"{name}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def read_memory(self, name):
        return json.loads((self.memory_dir / f"{name}.json").read_text(encoding="utf-8"))

    def test_search_returns_all_matches_without_limiting(self):
        for index in range(3):
            self.write_memory(
                f"memory-{index}",
                id=f"mem-{index}",
                priority=50 + index,
                content=f"shared topic memory {index}",
                queries=["shared topic"],
                must_include=[f"memory {index}"],
            )

        result = memory_cli.search("shared topic")

        self.assertEqual(["mem-2", "mem-1", "mem-0"], [m["id"] for m in result["matches"]])

    def test_search_orders_results_by_priority_before_score(self):
        self.write_memory(
            "low-score-high-priority",
            id="high-priority",
            priority=90,
            content="alpha durable preference",
            queries=["alpha"],
            must_include=["durable preference"],
        )
        self.write_memory(
            "high-score-low-priority",
            id="low-priority",
            priority=20,
            content="alpha alpha alpha noisy detail",
            queries=["alpha alpha alpha"],
            must_include=["noisy detail"],
        )

        result = memory_cli.search("alpha alpha alpha")

        self.assertEqual("high-priority", result["matches"][0]["id"])

    def test_memory_test_passes_when_expected_content_appears_anywhere_in_results(self):
        self.write_memory(
            "stronger-related-result",
            id="related",
            priority=95,
            content="python python python related implementation note",
            queries=["python memory"],
            must_include=["implementation note"],
        )
        self.write_memory(
            "expected-memory",
            id="expected",
            priority=60,
            content="remember exact expected content for python memory",
            queries=["python memory"],
            must_include=["exact expected content"],
        )

        result = memory_cli.run_tests()

        self.assertEqual([], result["failures"])

    def test_console_script_is_named_memory_cli(self):
        pyproject = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            "memory_cli.cli:main",
            pyproject["project"]["scripts"].get("memory-cli"),
        )

    def test_init_creates_memory_project_files(self):
        empty_root = self.root / "empty-project"

        result = memory_cli.init_project(empty_root)

        self.assertEqual("initialized", result["status"])
        self.assertTrue((empty_root / "memories").is_dir())
        self.assertTrue((empty_root / "memory.config.json").is_file())

    def test_list_and_show_return_memory_summaries(self):
        self.write_memory(
            "first",
            id="mem-first",
            priority=70,
            content="first durable memory",
            queries=["first"],
            must_include=["durable"],
            tags=["demo"],
        )

        listed = memory_cli.list_memories()
        shown = memory_cli.show_memory("mem-first")

        self.assertEqual("mem-first", listed["memories"][0]["id"])
        self.assertEqual("first durable memory", shown["memory"]["content"])

    def test_check_conflicts_reports_existing_matches_for_candidate_queries(self):
        self.write_memory(
            "existing",
            id="mem-existing",
            priority=80,
            content="existing memory about editor preference",
            queries=["editor preference"],
            must_include=["editor preference"],
        )
        candidate = {
            "id": "mem-new",
            "priority": 80,
            "content": "new memory about editor preference",
            "queries": ["editor preference"],
            "must_include": ["editor preference"],
        }

        result = memory_cli.check_conflicts(candidate)

        self.assertEqual(["mem-existing"], result["conflicts"][0]["matching_ids"])

    def test_add_memory_writes_file_when_no_conflicts(self):
        candidate = {
            "id": "mem-new",
            "priority": 60,
            "content": "new standalone memory",
            "queries": ["standalone"],
            "must_include": ["standalone"],
        }

        result = memory_cli.add_memory(candidate)

        self.assertEqual("added", result["status"])
        self.assertEqual("new standalone memory", self.read_memory("mem-new")["content"])

    def test_add_memory_refuses_conflicts_without_force(self):
        self.write_memory(
            "existing",
            id="mem-existing",
            priority=80,
            content="existing memory about shell preference",
            queries=["shell preference"],
            must_include=["shell preference"],
        )
        candidate = {
            "id": "mem-new",
            "priority": 60,
            "content": "new memory about shell preference",
            "queries": ["shell preference"],
            "must_include": ["shell preference"],
        }

        result = memory_cli.add_memory(candidate)

        self.assertEqual("conflict", result["status"])
        self.assertFalse((self.memory_dir / "mem-new.json").exists())

    def test_update_memory_merges_fields(self):
        self.write_memory(
            "existing",
            id="mem-existing",
            priority=60,
            content="old content",
            queries=["old"],
            must_include=["old"],
        )

        result = memory_cli.update_memory("mem-existing", {"priority": 90})

        self.assertEqual("updated", result["status"])
        self.assertEqual(90, self.read_memory("existing")["priority"])

    def test_retire_memory_marks_memory_inactive(self):
        self.write_memory(
            "existing",
            id="mem-existing",
            priority=60,
            content="old content",
            queries=["old"],
            must_include=["old"],
        )

        result = memory_cli.retire_memory("mem-existing", "stale")

        retired = self.read_memory("existing")
        self.assertEqual("retired", result["status"])
        self.assertEqual("retired", retired["status"])
        self.assertEqual("stale", retired["retired_reason"])

    def test_retired_memories_are_excluded_from_active_workflows(self):
        self.write_memory(
            "retired",
            id="mem-retired",
            priority=100,
            status="retired",
            content="retired shell preference",
            queries=["shell preference"],
            must_include=["shell preference"],
        )
        candidate = {
            "id": "mem-new",
            "priority": 80,
            "content": "active shell preference",
            "queries": ["shell preference"],
            "must_include": ["shell preference"],
        }

        self.assertEqual([], memory_cli.search("shell preference")["matches"])
        self.assertEqual([], memory_cli.check_conflicts(candidate)["conflicts"])
        self.assertEqual(0, memory_cli.run_tests()["total"])
        self.assertEqual(0, memory_cli.bench()["queries"])

    def test_main_exposes_management_subcommands(self):
        with patch.object(memory_cli, "init_project", return_value={"status": "initialized"}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, memory_cli.main(["init"]))


if __name__ == "__main__":
    unittest.main()
