"""Command policy for the Codex RTK guard."""

from __future__ import annotations

import json
import os
import pathlib
import shlex


DEFAULT_PRESET = "default"

BASE_ALLOW_PREFIXES = (
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

MINIMAL_CANDIDATE_PREFIXES = (
    "git status",
    "git diff",
    "git show",
    "git log",
    "ls",
    "rg",
    "grep",
    "wc",
)

DEFAULT_EXTRA_CANDIDATE_PREFIXES = (
    "tree",
    "find",
    "fd",
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
)

FULL_EXTRA_CANDIDATE_PREFIXES = (
    "npm run",
    "pnpm run",
    "yarn run",
    "bun run",
    "cargo",
    "python -m",
    "python3 -m",
    "npx",
    "docker",
    "kubectl",
    "aws",
    "terraform",
    "make",
)

PRESET_CANDIDATE_PREFIXES = {
    "minimal": MINIMAL_CANDIDATE_PREFIXES,
    "default": MINIMAL_CANDIDATE_PREFIXES + DEFAULT_EXTRA_CANDIDATE_PREFIXES,
    "full": (
        MINIMAL_CANDIDATE_PREFIXES
        + DEFAULT_EXTRA_CANDIDATE_PREFIXES
        + FULL_EXTRA_CANDIDATE_PREFIXES
    ),
}

CONFIG_NAMES = (
    ".codex/rtk-guard.json",
    "rtk-guard.json",
)


def should_consider(command: str, cwd: str | os.PathLike[str] | None = None) -> bool:
    stripped = command.strip()
    if not stripped:
        return False

    config = load_config(cwd)
    preset = config_preset(config)
    allow_prefixes = (
        BASE_ALLOW_PREFIXES
        + config_prefixes(config, "allow_prefixes")
        + env_prefixes("RTK_CODEX_EXTRA_ALLOW_PREFIXES")
    )
    candidate_prefixes = (
        PRESET_CANDIDATE_PREFIXES[preset]
        + config_prefixes(config, "candidate_prefixes")
        + env_prefixes("RTK_CODEX_EXTRA_CANDIDATE_PREFIXES")
    )

    if matches_any(stripped, allow_prefixes):
        return False
    return matches_any(stripped, candidate_prefixes)


def matches_any(command: str, prefixes: tuple[str, ...] | list[str]) -> bool:
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


def load_config(cwd: str | os.PathLike[str] | None = None) -> dict:
    explicit = os.environ.get("RTK_CODEX_CONFIG")
    paths = [pathlib.Path(explicit)] if explicit else config_paths(cwd)
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def config_paths(cwd: str | os.PathLike[str] | None = None) -> tuple[pathlib.Path, ...]:
    root = pathlib.Path(cwd or os.getcwd())
    return tuple(root / name for name in CONFIG_NAMES)


def config_preset(config: dict) -> str:
    preset = str(
        config.get("preset") or os.environ.get("RTK_CODEX_PRESET") or DEFAULT_PRESET
    )
    return preset if preset in PRESET_CANDIDATE_PREFIXES else DEFAULT_PRESET


def config_prefixes(config: dict, name: str) -> tuple[str, ...]:
    value = config.get(name)
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )
