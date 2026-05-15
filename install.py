#!/usr/bin/env python3
"""Install Codex hook config for this checkout."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parent
HOOK = ROOT / "src" / "rtk_codex_hooks" / "hook.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install RTK Codex hook config")
    parser.add_argument(
        "--target",
        default="project",
        choices=["project", "user"],
        help="Install to ./ .codex/hooks.json or ~/.codex/hooks.json",
    )
    parser.add_argument(
        "--project-dir",
        default=os.getcwd(),
        help="Project directory for --target project",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing hooks.json")
    args = parser.parse_args()

    target_dir = (
        pathlib.Path(args.project_dir).resolve() / ".codex"
        if args.target == "project"
        else pathlib.Path.home() / ".codex"
    )
    target_file = target_dir / "hooks.json"

    if target_file.exists() and not args.force:
        print(f"refusing to overwrite existing {target_file}; pass --force", file=sys.stderr)
        return 2

    target_dir.mkdir(parents=True, exist_ok=True)
    if target_file.exists():
        backup = target_file.with_suffix(".json.bak")
        shutil.copy2(target_file, backup)
        print(f"backed up existing hooks config to {backup}")

    target_file.write_text(json.dumps(hooks_json(), indent=2) + "\n", encoding="utf-8")
    print(f"installed Codex hook config: {target_file}")
    print("Next: restart Codex, open /hooks, trust and enable the hook.")
    return 0


def hooks_json() -> dict:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "^Bash$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"RTK_CODEX_HOOK_MODE=deny /usr/bin/python3 {HOOK}",
                            "timeout": 5,
                            "statusMessage": "Suggesting RTK for noisy command",
                        }
                    ],
                }
            ]
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())

