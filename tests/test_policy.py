import pathlib
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_minimal_preset_skips_default_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = pathlib.Path(tmp) / ".codex"
            config_dir.mkdir()
            (config_dir / "rtk-guard.json").write_text(
                '{"preset": "minimal"}\n',
                encoding="utf-8",
            )
            self.assertTrue(policy.should_consider("git diff", cwd=tmp))
            self.assertFalse(policy.should_consider("cargo test", cwd=tmp))

    def test_full_preset_considers_broad_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = pathlib.Path(tmp) / ".codex"
            config_dir.mkdir()
            (config_dir / "rtk-guard.json").write_text(
                '{"preset": "full"}\n',
                encoding="utf-8",
            )
            self.assertTrue(policy.should_consider("terraform plan", cwd=tmp))
            self.assertTrue(policy.should_consider("make test", cwd=tmp))

    def test_config_can_add_candidate_and_allow_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = pathlib.Path(tmp) / ".codex"
            config_dir.mkdir()
            (config_dir / "rtk-guard.json").write_text(
                (
                    "{"
                    '"candidate_prefixes": ["custom noisy"],'
                    '"allow_prefixes": ["git diff"]'
                    "}\n"
                ),
                encoding="utf-8",
            )
            self.assertTrue(policy.should_consider("custom noisy command", cwd=tmp))
            self.assertFalse(policy.should_consider("git diff", cwd=tmp))

    @mock.patch.dict("os.environ", {"RTK_CODEX_PRESET": "minimal"})
    def test_env_preset(self):
        self.assertFalse(policy.should_consider("cargo test"))
