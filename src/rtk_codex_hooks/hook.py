#!/usr/bin/env python3
"""Codex PreToolUse hook for RTK deny-with-suggestion.

The hook intentionally does not use `updatedInput`, because current Codex docs
say that field is parsed but unsupported. Instead, it blocks RTK-supported
commands and tells Codex exactly which compact command to retry.
"""

from __future__ import annotations

import json
import os
import pathlib
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass


DEFAULT_RTK = "/root/.local/bin/rtk"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_NO_RTK = str(PROJECT_ROOT / "bin" / "NO_RTK")


@dataclass(frozen=True)
class Decision:
    action: str
    command: str | None = None
    reason: str | None = None


def main() -> int:
    payload = read_payload()
    if payload is None:
        return 0

    decision = decide(payload)
    if decision.action != "deny":
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": decision.reason,
                }
            },
            separators=(",", ":"),
        )
    )
    return 0


def read_payload() -> dict | None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def decide(payload: dict) -> Decision:
    if payload.get("tool_name") != "Bash":
        return Decision("allow")

    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str) or not command.strip():
        return Decision("allow")

    if is_bypass(command):
        return Decision("allow")

    rewritten = rtk_rewrite(command)
    if rewritten is None or rewritten == command:
        return Decision("allow")

    rtk_command = command_with_absolute_rtk(rewritten)
    raw_command = raw_escape_command(command)
    log_decision(payload, command, rtk_command)
    return Decision(
        "deny",
        command=rtk_command,
        reason=(
            "RTK can reduce token-heavy output. "
            f"Retry with: {rtk_command}. "
            f"Need raw output? Retry with: {raw_command}."
        ),
    )


def is_bypass(command: str) -> bool:
    stripped = command.lstrip()
    no_rtk_bin = os.environ.get("NO_RTK_BIN", DEFAULT_NO_RTK)
    return (
        "RTK_DISABLED=1" in command
        or stripped.startswith("NO_RTK ")
        or stripped.startswith(f"{no_rtk_bin} ")
        or stripped.startswith(f"{shlex.quote(no_rtk_bin)} ")
        or stripped == "rtk"
        or stripped.startswith("rtk ")
        or stripped == DEFAULT_RTK
        or stripped.startswith(f"{DEFAULT_RTK} ")
    )


def rtk_rewrite(command: str) -> str | None:
    rtk = os.environ.get("RTK_BIN", DEFAULT_RTK)
    try:
        result = subprocess.run(
            [rtk, "rewrite", command],
            check=False,
            text=True,
            capture_output=True,
            timeout=float(os.environ.get("RTK_REWRITE_TIMEOUT", "2")),
        )
    except Exception:
        return None

    rewritten = result.stdout.strip()
    if result.returncode not in (0, 3) or not rewritten:
        return None
    return rewritten


def command_with_absolute_rtk(command: str) -> str:
    rtk = os.environ.get("RTK_BIN", DEFAULT_RTK)
    if rtk == "rtk":
        return command
    if command == "rtk":
        return rtk
    if command.startswith("rtk "):
        return f"{rtk}{command[3:]}"
    return (
        command.replace("; rtk ", f"; {rtk} ")
        .replace("&& rtk ", f"&& {rtk} ")
        .replace("|| rtk ", f"|| {rtk} ")
    )


def raw_escape_command(command: str) -> str:
    no_rtk = os.environ.get("NO_RTK_BIN", DEFAULT_NO_RTK)
    return f"{shlex.quote(no_rtk)} -- {shlex.quote(command)}"


def log_decision(payload: dict, command: str, rewritten: str) -> None:
    log_path = pathlib.Path(
        os.environ.get(
            "RTK_CODEX_HOOK_LOG",
            str(pathlib.Path.home() / ".local/share/rtk/codex-deny-hook.jsonl"),
        )
    )
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": int(time.time()),
                        "cwd": payload.get("cwd"),
                        "tool_use_id": payload.get("tool_use_id"),
                        "command": command,
                        "rewritten": rewritten,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
