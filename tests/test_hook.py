import json
import os
import pathlib
import sys
import unittest
from io import StringIO
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from rtk_codex_hooks import hook


def payload(command):
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/project",
        "tool_use_id": "call_1",
    }


class HookDecisionTests(unittest.TestCase):
    def test_allows_non_bash(self):
        decision = hook.decide({"tool_name": "Read", "tool_input": {"command": "git diff"}})
        self.assertEqual(decision.action, "allow")

    def test_allows_bypass_env(self):
        decision = hook.decide(payload("RTK_DISABLED=1 git diff"))
        self.assertEqual(decision.action, "allow")

    def test_allows_no_rtk_wrapper(self):
        decision = hook.decide(payload(f"{hook.DEFAULT_NO_RTK} -- 'git diff'"))
        self.assertEqual(decision.action, "allow")

    @mock.patch("rtk_codex_hooks.hook.rtk_rewrite", return_value="rtk git diff")
    def test_denies_with_rtk_and_raw_suggestions(self, _rewrite):
        decision = hook.decide(payload("git diff"))
        self.assertEqual(decision.action, "deny")
        self.assertIn("/root/.local/bin/rtk git diff", decision.reason)
        self.assertIn("NO_RTK", decision.reason)
        self.assertIn("git diff", decision.reason)

    def test_replaces_segment_initial_rtk(self):
        self.assertEqual(
            hook.command_with_absolute_rtk("rtk wc -l file"),
            "/root/.local/bin/rtk wc -l file",
        )

    def test_raw_escape_quotes_shell_command(self):
        raw = hook.raw_escape_command("git diff && git status")
        self.assertIn("--", raw)
        self.assertIn("'git diff && git status'", raw)


class HookOutputTests(unittest.TestCase):
    @mock.patch.dict(os.environ, {"RTK_CODEX_HOOK_LOG": "/tmp/rtk-codex-hooks-test.jsonl"})
    @mock.patch("rtk_codex_hooks.hook.rtk_rewrite", return_value="rtk wc -l file")
    def test_main_outputs_deny_json(self, _rewrite):
        input_payload = json.dumps(payload("wc -l file"))
        stdout = StringIO()
        with mock.patch("sys.stdin", StringIO(input_payload)), mock.patch("sys.stdout", stdout):
            self.assertEqual(hook.main(), 0)

        output = json.loads(stdout.getvalue())
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn("/root/.local/bin/rtk wc -l file", hook_output["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
