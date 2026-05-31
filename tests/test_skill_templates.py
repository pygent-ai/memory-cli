import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "memory-cli"
ASSETS = SKILL_ROOT / "assets"


class SkillTemplateContractTest(unittest.TestCase):
    def test_language_templates_use_suffix_labels(self):
        for suffix in ["py", "js", "ts"]:
            template = ASSETS / f"default-memory-cli-{suffix}"

            self.assertTrue(template.is_dir(), f"missing {template.name}")
            self.assertTrue((template / "memory.config.json").is_file())
            self.assertTrue((template / "memories" / "example-memory.json").is_file())

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
