import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import install
import uninstall


class InstallConfigTests(unittest.TestCase):
    def test_hooks_json_points_at_checkout_hook(self):
        config = install.hooks_json()
        handler = config["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(handler["type"], "command")
        self.assertIn("RTK_CODEX_HOOK_MODE=deny", handler["command"])
        self.assertIn(str(install.HOOK), handler["command"])
        self.assertIn("NO_RTK_BIN=", handler["command"])

    def test_hooks_json_is_serializable(self):
        encoded = json.dumps(install.hooks_json())
        self.assertIn("PreToolUse", encoded)

    def test_merge_preserves_existing_hook_and_adds_guard(self):
        current = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 existing.py",
                                "statusMessage": "Existing hook",
                            }
                        ],
                    }
                ]
            }
        }
        merged = install.merge_hooks(current, install.hooks_json())
        groups = merged["hooks"]["PreToolUse"]
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["hooks"][0]["statusMessage"], "Existing hook")
        self.assertEqual(groups[1]["hooks"][0]["statusMessage"], install.STATUS_MESSAGE)

    def test_merge_replaces_prior_guard_hook(self):
        first = install.merge_hooks({"hooks": {}}, install.hooks_json())
        second = install.merge_hooks(first, install.hooks_json())
        self.assertEqual(len(second["hooks"]["PreToolUse"]), 1)

    def test_uninstall_removes_only_guard_hook(self):
        current = install.merge_hooks(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "^Bash$",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 existing.py",
                                    "statusMessage": "Existing hook",
                                }
                            ],
                        }
                    ]
                }
            },
            install.hooks_json(),
        )
        updated, removed = uninstall.remove_guard_hooks(current)
        self.assertEqual(removed, 1)
        self.assertEqual(len(updated["hooks"]["PreToolUse"]), 1)
        self.assertEqual(
            updated["hooks"]["PreToolUse"][0]["hooks"][0]["statusMessage"], "Existing hook"
        )


if __name__ == "__main__":
    unittest.main()
