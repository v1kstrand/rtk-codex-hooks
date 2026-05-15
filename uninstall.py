#!/usr/bin/env python3
"""Remove hooks.json installed by install.py when it still matches this project."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from install import hooks_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Uninstall RTK Codex hook config")
    parser.add_argument("--target", default="project", choices=["project", "user"])
    parser.add_argument("--project-dir", default=os.getcwd())
    args = parser.parse_args()

    target_dir = (
        pathlib.Path(args.project_dir).resolve() / ".codex"
        if args.target == "project"
        else pathlib.Path.home() / ".codex"
    )
    target_file = target_dir / "hooks.json"
    if not target_file.exists():
        print(f"nothing to remove: {target_file}")
        return 0

    current = json.loads(target_file.read_text(encoding="utf-8"))
    if current != hooks_json():
        print(f"refusing to remove modified hooks config: {target_file}", file=sys.stderr)
        return 2

    target_file.unlink()
    print(f"removed Codex hook config: {target_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

