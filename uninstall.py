#!/usr/bin/env python3
"""Remove RTK Codex Guard hook entries installed by install.py."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import time

from install import STATUS_MESSAGE, group_contains_guard_hook, hooks_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Uninstall RTK Codex Guard")
    parser.add_argument("--target", default="project", choices=["project", "user"])
    parser.add_argument("--project-dir", default=os.getcwd())
    args = parser.parse_args()

    target_file = hooks_path(args.target, pathlib.Path(args.project_dir))
    if not target_file.exists():
        print(f"nothing to remove: {target_file}")
        return 0

    current = json.loads(target_file.read_text(encoding="utf-8"))
    updated, removed = remove_guard_hooks(current)
    if removed == 0:
        print(f"no {STATUS_MESSAGE!r} hooks found in {target_file}")
        return 0

    backup = backup_file(target_file)
    target_file.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    print(f"backed up existing hooks config to {backup}")
    print(f"removed {removed} RTK Codex Guard hook group(s) from {target_file}")
    return 0


def remove_guard_hooks(config: dict) -> tuple[dict, int]:
    updated = dict(config)
    hooks = dict(updated.get("hooks") or {})
    groups = list(hooks.get("PreToolUse") or [])
    kept = [group for group in groups if not group_contains_guard_hook(group)]
    removed = len(groups) - len(kept)
    if kept:
        hooks["PreToolUse"] = kept
    else:
        hooks.pop("PreToolUse", None)
    updated["hooks"] = hooks
    return updated, removed


def backup_file(path: pathlib.Path) -> pathlib.Path:
    stamp = f"{time.strftime('%Y%m%d%H%M%S')}.{time.time_ns()}"
    backup = path.with_suffix(f".json.{stamp}.bak")
    shutil.copy2(path, backup)
    return backup


if __name__ == "__main__":
    raise SystemExit(main())
