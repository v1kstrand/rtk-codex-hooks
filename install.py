#!/usr/bin/env python3
"""Install Codex hook config for this checkout."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import stat
import sys
import time


ROOT = pathlib.Path(__file__).resolve().parent
HOOK = ROOT / "src" / "rtk_codex_hooks" / "hook.py"
WRAPPER = ROOT / "bin" / "NO_RTK"
STATUS_MESSAGE = "Suggesting RTK for noisy command"
DISPLAY_NAME = "RTK Codex Guard"
DESCRIPTION = "Blocks supported noisy Bash commands and suggests RTK retries."


def main() -> int:
    parser = argparse.ArgumentParser(description="Install RTK Codex Guard")
    parser.add_argument(
        "--target",
        default="project",
        choices=["project", "user"],
        help="Install to <project>/.codex/hooks.json or ~/.codex/hooks.json",
    )
    parser.add_argument(
        "--project-dir",
        default=os.getcwd(),
        help="Project directory for --target project",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace hooks.json instead of merging this hook into it",
    )
    parser.add_argument(
        "--no-wrapper",
        action="store_true",
        help="Do not install NO_RTK into ~/.local/bin",
    )
    args = parser.parse_args()

    no_rtk_bin = str(WRAPPER)
    if not args.no_wrapper:
        no_rtk_bin = str(install_wrapper())

    rtk_bin = shutil.which("rtk") or "/root/.local/bin/rtk"
    if not pathlib.Path(rtk_bin).exists() and rtk_bin.startswith("/"):
        print(
            f"warning: RTK binary not found at {rtk_bin}; install RTK before enabling the hook",
            file=sys.stderr,
        )

    target_file = hooks_path(args.target, pathlib.Path(args.project_dir))
    target_file.parent.mkdir(parents=True, exist_ok=True)

    if target_file.exists():
        backup = backup_file(target_file)
        print(f"backed up existing hooks config to {backup}")
        current = read_json(target_file)
    else:
        current = {"hooks": {}}

    new_config = hooks_json(no_rtk_bin=no_rtk_bin, rtk_bin=rtk_bin)
    merged = new_config if args.replace else merge_hooks(current, new_config)
    target_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    print(f"installed Codex hook config: {target_file}")
    print("Next: restart Codex, open /hooks, trust and enable:")
    print(f"  {DISPLAY_NAME}")
    return 0


def hooks_path(target: str, project_dir: pathlib.Path) -> pathlib.Path:
    if target == "project":
        return project_dir.resolve() / ".codex" / "hooks.json"
    return pathlib.Path.home() / ".codex" / "hooks.json"


def install_wrapper() -> pathlib.Path:
    dest = pathlib.Path.home() / ".local" / "bin" / "NO_RTK"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WRAPPER, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def backup_file(path: pathlib.Path) -> pathlib.Path:
    stamp = f"{time.strftime('%Y%m%d%H%M%S')}.{time.time_ns()}"
    backup = path.with_suffix(f".json.{stamp}.bak")
    shutil.copy2(path, backup)
    return backup


def read_json(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"expected object in {path}")
    return data


def hooks_json(no_rtk_bin: str | None = None, rtk_bin: str | None = None) -> dict:
    no_rtk_bin = no_rtk_bin or str(WRAPPER)
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "displayName": DISPLAY_NAME,
                    "description": DESCRIPTION,
                    "matcher": "^Bash$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(no_rtk_bin=no_rtk_bin, rtk_bin=rtk_bin),
                            "timeout": 5,
                            "statusMessage": STATUS_MESSAGE,
                        }
                    ],
                }
            ]
        }
    }


def hook_command(no_rtk_bin: str | None = None, rtk_bin: str | None = None) -> str:
    env = ["RTK_CODEX_HOOK_MODE=deny"]
    if rtk_bin:
        env.append(f"RTK_BIN={shell_quote(rtk_bin)}")
    if no_rtk_bin:
        env.append(f"NO_RTK_BIN={shell_quote(no_rtk_bin)}")
    env.append("/usr/bin/python3")
    env.append(shell_quote(str(HOOK)))
    return " ".join(env)


def merge_hooks(current: dict, addition: dict) -> dict:
    merged = dict(current)
    merged_hooks = dict(merged.get("hooks") or {})
    existing_groups = list(merged_hooks.get("PreToolUse") or [])
    new_groups = addition["hooks"]["PreToolUse"]

    existing_groups = [
        group for group in existing_groups if not group_contains_guard_hook(group)
    ]
    merged_hooks["PreToolUse"] = existing_groups + new_groups
    merged["hooks"] = merged_hooks
    return merged


def group_contains_guard_hook(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return False
    return any(is_guard_handler(handler) for handler in hooks)


def is_guard_handler(handler: object) -> bool:
    if not isinstance(handler, dict):
        return False
    command = str(handler.get("command") or "")
    return str(HOOK) in command or handler.get("statusMessage") == STATUS_MESSAGE


def shell_quote(value: str) -> str:
    import shlex

    return shlex.quote(value)


if __name__ == "__main__":
    raise SystemExit(main())
