"""Keep the central workflow privilege boundaries explicit."""

import re
import unittest
from pathlib import Path


class WorkflowTests(unittest.TestCase):
    def test_actions_use_immutable_references(self):
        workflows = Path(__file__).parents[1] / "workflows"
        for name in ["marketplace-import", "marketplace-validate", "marketplace-tags"]:
            text = (workflows / (name + ".yml")).read_text()
            for action in re.findall(r"uses:\s*(\S+)", text):
                self.assertRegex(action, r"^[^@]+@[0-9a-f]{40}$")
            self.assertIn("persist-credentials: false", text)

    def test_writer_installs_nothing_and_token_is_central_only(self):
        workflows = Path(__file__).parents[1] / "workflows"
        read, write = (
            (workflows / "marketplace-import.yml").read_text().split("\n  publish:\n")
        )
        self.assertNotIn("secrets.PLUGINS_PR_TOKEN", read)
        self.assertIn("secrets.PLUGINS_PR_TOKEN", write)
        self.assertNotRegex(write, r"(?:pip|npm) install")
        self.assertIn("needs: verify", write)
        self.assertIn("--native-hosts", read)
        self.assertIn("--ignore-scripts", read)

    def test_tags_follow_successful_main_push_validation(self):
        workflows = Path(__file__).parents[1] / "workflows"
        text = (workflows / "marketplace-tags.yml").read_text()
        for guard in [
            "conclusion == 'success'",
            "event == 'push'",
            "head_branch == 'main'",
            "head_repository.full_name == github.repository",
            "ref: ${{ github.event.workflow_run.head_sha }}",
            '--source-sha "$VALIDATED_SHA"',
        ]:
            self.assertIn(guard, text)


if __name__ == "__main__":
    unittest.main()
