"""Command policy for the Codex RTK guard."""

from __future__ import annotations

import os
import shlex


DEFAULT_ALLOW_PREFIXES = (
    "cd ",
    "pwd",
    "echo ",
    "printf ",
    "date",
    "true",
    "false",
    "mkdir ",
    "touch ",
    "chmod ",
    "chown ",
    "git rev-parse ",
    "git branch ",
    "git remote ",
)

DEFAULT_CANDIDATE_PREFIXES = (
    "git status",
    "git diff",
    "git show",
    "git log",
    "ls",
    "tree",
    "find",
    "fd",
    "rg",
    "grep",
    "wc",
    "cat",
    "head",
    "tail",
    "npm test",
    "npm run test",
    "pnpm test",
    "pnpm run test",
    "yarn test",
    "bun test",
    "cargo test",
    "cargo build",
    "cargo check",
    "pytest",
    "python -m pytest",
    "python3 -m pytest",
    "vitest",
    "npx vitest",
    "jest",
    "npx jest",
    "tsc",
    "npx tsc",
    "eslint",
    "npx eslint",
    "ruff",
    "mypy",
    "go test",
    "go build",
    "docker",
    "kubectl",
    "aws",
)


def should_consider(command: str) -> bool:
    stripped = command.strip()
    if not stripped:
        return False

    if matches_any(stripped, env_prefixes("RTK_CODEX_EXTRA_ALLOW_PREFIXES")):
        return False
    if matches_any(stripped, DEFAULT_ALLOW_PREFIXES):
        return False

    extra_candidates = env_prefixes("RTK_CODEX_EXTRA_CANDIDATE_PREFIXES")
    if matches_any(stripped, extra_candidates):
        return True

    return matches_any(stripped, DEFAULT_CANDIDATE_PREFIXES)


def matches_any(command: str, prefixes: tuple[str, ...]) -> bool:
    normalized = normalize_command_start(command)
    return any(matches_prefix(normalized, prefix) for prefix in prefixes)


def matches_prefix(command: str, prefix: str) -> bool:
    prefix = prefix.strip()
    if not prefix:
        return False
    if command == prefix:
        return True
    return command.startswith(prefix + " ")


def normalize_command_start(command: str) -> str:
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        return command.strip()
    if not parts:
        return ""

    env_count = 0
    for part in parts:
        if "=" not in part or part.startswith("="):
            break
        key = part.split("=", 1)[0]
        if not key.replace("_", "").isalnum():
            break
        env_count += 1
    return " ".join(parts[env_count:])


def env_prefixes(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "")
    return tuple(part.strip() for part in raw.split(",") if part.strip())

