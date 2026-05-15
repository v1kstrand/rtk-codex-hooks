import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from rtk_codex_hooks import policy


class PolicyTests(unittest.TestCase):
    def test_allows_small_commands(self):
        self.assertFalse(policy.should_consider("echo hello"))
        self.assertFalse(policy.should_consider("pwd"))
        self.assertFalse(policy.should_consider("date"))

    def test_considers_noisy_commands(self):
        self.assertTrue(policy.should_consider("git diff"))
        self.assertTrue(policy.should_consider("rg -n hook ."))
        self.assertTrue(policy.should_consider("wc -l README.md"))
        self.assertTrue(policy.should_consider("cargo test"))

    def test_strips_env_prefixes_before_matching(self):
        self.assertTrue(policy.should_consider("FOO=bar git diff"))
        self.assertFalse(policy.should_consider("FOO=bar echo hi"))

