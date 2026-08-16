import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "dynamic-memory-cli" / "scripts" / "dynamic_memory_cli.py"
SPEC = importlib.util.spec_from_file_location("dynamic_memory_cli", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def ut(ut_id="ut-1", content="The project uses blue deployments."):
    return {
        "action": "upsert", "id": ut_id, "memory_id": f"mem-{ut_id}", "priority": 80,
        "content": content, "queries": ["project deployment", "blue deployments"],
        "must_include": ["blue"], "evidence_refs": ["raw-history:event-1"],
        "source": "session-1", "tags": ["decision"],
    }


class DynamicMemoryCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "memory"
        MODULE.init_project(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def proposal(self, changes=None, *, base_memory=0, base_snapshot=0, start=1, end=4):
        return {
            "base_memory_revision": base_memory, "base_snapshot_revision": base_snapshot,
            "from_cursor": start, "to_cursor": end,
            "snapshot": {"current_state": ["Use blue deployments"], "next_actions": []},
            "changed_uts": [ut()] if changes is None else changes,
            "evidence_refs": [f"raw-history:range-{start}-{end}"],
            "semantic_statement": "All future-relevant effects are carried.",
        }

    def test_pending_publish_search_and_built_migration_are_atomic(self):
        published = MODULE.publish_pending(self.root, self.proposal())
        self.assertEqual(1, published["memory_revision"])
        self.assertEqual(1, published["snapshot_revision"])
        self.assertEqual("pending", MODULE.search(self.root, ["deployment"])["matches"][0]["build_state"])
        batch_path = Path(self.temp.name) / "batch.json"
        MODULE.freeze_pending(self.root, batch_path)
        built = MODULE.build_pending(self.root, json.loads(batch_path.read_text(encoding="utf-8")))
        self.assertEqual("built", built["status"])
        self.assertEqual("built", MODULE.search(self.root, ["deployment"])["matches"][0]["build_state"])
        self.assertEqual(0, MODULE.run_tests(self.root, built_only=True)["failed"])
        with MODULE.connect(self.root) as conn:
            state = MODULE.state(conn)
        self.assertEqual(1, state["memory_revision"])
        self.assertEqual(1, state["snapshot_revision"])

    def test_modified_built_ut_returns_to_pending_and_stale_batch_is_skipped(self):
        MODULE.publish_pending(self.root, self.proposal())
        old_batch = Path(self.temp.name) / "old.json"
        MODULE.freeze_pending(self.root, old_batch)
        MODULE.build_pending(self.root, json.loads(old_batch.read_text(encoding="utf-8")))
        change = ut(content="The project uses blue-green deployments.")
        next_proposal = self.proposal([change], base_memory=1, base_snapshot=1, start=5, end=8)
        MODULE.publish_pending(self.root, next_proposal)
        result = MODULE.build_pending(self.root, json.loads(old_batch.read_text(encoding="utf-8")))
        self.assertEqual(["ut-1"], result["skipped"])
        self.assertEqual("pending", MODULE.show(self.root, "ut-1")["memory"]["build_state"])

    def test_empty_change_advances_snapshot_and_cursor_without_memory_revision(self):
        result = MODULE.publish_pending(self.root, self.proposal([]))
        self.assertEqual(0, result["memory_revision"])
        self.assertEqual(1, result["snapshot_revision"])
        self.assertEqual(4, result["covered_through"])

    def test_rejects_stale_or_non_contiguous_proposals(self):
        MODULE.publish_pending(self.root, self.proposal([]))
        with self.assertRaisesRegex(ValueError, "stale"):
            MODULE.publish_pending(self.root, self.proposal([], start=5, end=8))
        with self.assertRaisesRegex(ValueError, "continuous"):
            MODULE.publish_pending(self.root, self.proposal([], base_snapshot=1, start=6, end=8))


if __name__ == "__main__":
    unittest.main()
