import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "memory-cli"
ASSETS = SKILL_ROOT / "assets"


class SkillTemplateContractTest(unittest.TestCase):
    def test_root_package_metadata_publishes_skill_plugin(self):
        package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

        self.assertEqual("@pygent-ai/memory-cli", package_json["name"])
        self.assertEqual("0.1.0", package_json["version"])
        self.assertEqual("Apache-2.0", package_json["license"])
        self.assertEqual("https://registry.npmjs.org/", package_json["publishConfig"]["registry"])
        self.assertEqual("public", package_json["publishConfig"]["access"])
        self.assertIn(".codex-plugin/", package_json["files"])
        self.assertIn("skills/", package_json["files"])
        self.assertNotIn("experiments/", package_json["files"])
        self.assertNotIn("datasets/", package_json["files"])

    def test_codex_plugin_manifest_points_to_skill_directory(self):
        plugin_json = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )

        self.assertEqual("memory-cli", plugin_json["name"])
        self.assertEqual("0.1.0", plugin_json["version"])
        self.assertEqual("Apache-2.0", plugin_json["license"])
        self.assertEqual("./skills/", plugin_json["skills"])
        self.assertEqual("Memory CLI", plugin_json["interface"]["displayName"])
        self.assertIn("Memory", plugin_json["interface"]["capabilities"])

    def test_language_templates_use_suffix_labels(self):
        for suffix in ["py", "js", "ts"]:
            template = ASSETS / f"default-memory-cli-{suffix}"

            self.assertTrue(template.is_dir(), f"missing {template.name}")
            self.assertTrue((template / "memory.config.json").is_file())
            self.assertTrue((template / "memories" / "example-memory.json").is_file())
            self.assertTrue((template / "test-cases" / "example-memory.json").is_file())

    def test_javascript_template_exposes_memory_cli_bin_and_test_script(self):
        package_json = json.loads(
            (ASSETS / "default-memory-cli-js" / "package.json").read_text(encoding="utf-8")
        )

        self.assertEqual("./src/cli.js", package_json["bin"]["memory-cli"])
        self.assertEqual("node --test", package_json["scripts"]["test"])

    def test_typescript_template_exposes_memory_cli_bin_and_test_script(self):
        package_json = json.loads(
            (ASSETS / "default-memory-cli-ts" / "package.json").read_text(encoding="utf-8")
        )

        self.assertEqual("./dist/src/cli.js", package_json["bin"]["memory-cli"])
        self.assertEqual("npm run build && node --test dist/tests/*.test.js", package_json["scripts"]["test"])

    def test_docs_reference_suffix_labeled_templates(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for suffix in ["py", "js", "ts"]:
            marker = f"assets/default-memory-cli-{suffix}/"
            self.assertIn(marker, skill)
            self.assertIn(marker, readme)


if __name__ == "__main__":
    unittest.main()
