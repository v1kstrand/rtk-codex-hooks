import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import install


class InstallConfigTests(unittest.TestCase):
    def test_hooks_json_points_at_checkout_hook(self):
        config = install.hooks_json()
        handler = config["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(handler["type"], "command")
        self.assertIn("RTK_CODEX_HOOK_MODE=deny", handler["command"])
        self.assertIn(str(install.HOOK), handler["command"])

    def test_hooks_json_is_serializable(self):
        encoded = json.dumps(install.hooks_json())
        self.assertIn("PreToolUse", encoded)


if __name__ == "__main__":
    unittest.main()
