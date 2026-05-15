# RTK Codex Guard

Codex-specific RTK hook adapter.

RTK can reduce noisy command output, but RTK's Codex integration is currently
instruction-based. That means Codex can forget to use RTK. Codex hooks also do
not currently support silent command replacement, so this project uses the
reliable Codex path: deny the noisy raw command and tell Codex exactly how to
retry with RTK.

## Behavior

```text
Codex proposes a noisy shell command
Codex handler runs this PreToolUse hook
Hook asks `rtk rewrite` for the compact command
Handler blocks the raw command
Codex sees: retry with RTK, or use NO_RTK for raw output
```

This is not a transparent Claude-style rewrite. It is a Codex-specific guard
that makes the RTK choice explicit.

## Why This Exists

- `AGENTS.md` guidance can be forgotten. A trusted hook cannot.
- RTK is the default for supported noisy commands.
- `NO_RTK` gives Codex a full-fidelity escape hatch when raw output is needed.

## Install Prerequisites

- Codex CLI with hooks enabled.
- RTK installed and callable as `rtk`, or available at `/root/.local/bin/rtk`.
- Python 3.

Check:

```bash
codex --version
rtk --version
python3 --version
```

## Install

Install into the current project:

```bash
python3 install.py --target project
```

Or install globally for the current Codex user:

```bash
python3 install.py --target user
```

By default the installer:

- backs up existing `hooks.json`
- merges this hook with existing `PreToolUse` hooks
- installs `NO_RTK` to `~/.local/bin/NO_RTK`

Then restart Codex, open `/hooks`, and trust/enable the hook named:

```text
Suggesting RTK for noisy command
```

## Test The Flow

Ask Codex to run a command RTK can rewrite:

```bash
wc -l README.md
```

Expected first response:

```text
Command blocked by PreToolUse hook:
RTK can reduce token-heavy output.
Retry with: /root/.local/bin/rtk wc -l README.md.
Need raw output? Retry with: /home/you/.local/bin/NO_RTK -- 'wc -l README.md'.
```

Codex should then retry with the RTK command. If the compact output is not
enough, use the raw escape hatch shown in the message.

## Raw Output Escape Hatch

The hook never blocks commands that use `NO_RTK` or `RTK_DISABLED=1`.

```bash
bin/NO_RTK git diff
bin/NO_RTK -- 'git diff && git status'
RTK_DISABLED=1 git diff
```

The hook suggestion includes both paths:

```text
Retry with: /root/.local/bin/rtk git diff.
Need raw output? Retry with: /path/to/bin/NO_RTK -- 'git diff'.
```

## Uninstall

Remove this project’s hook entry while keeping unrelated hooks:

```bash
python3 uninstall.py --target project
```

Use `/hooks` to disable it manually if you prefer.

## Default Policy

The hook is intentionally selective.

Allowed without asking RTK:

```text
echo, pwd, date, cd, mkdir, touch, chmod, git rev-parse, git branch, git remote
```

Candidate commands:

```text
git status, git diff, git show, git log
ls, tree, find, fd, rg, grep, wc, cat, head, tail
npm/pnpm/yarn/bun tests
cargo test/build/check
pytest, vitest, jest, tsc, eslint, ruff, mypy
go test/build
docker, kubectl, aws
```

You can add local prefixes without editing code:

```bash
RTK_CODEX_EXTRA_CANDIDATE_PREFIXES="terraform,make test" codex
RTK_CODEX_EXTRA_ALLOW_PREFIXES="git blame,my-tool" codex
```

The hook still asks `rtk rewrite` before blocking. If RTK has no rewrite, the
raw command runs normally.

## Development

```bash
python3 -m unittest discover -s tests
```

## Current Codex Limitation

Codex currently parses but does not reliably apply `PreToolUse.updatedInput`.
That is why this project uses deny-with-suggestion instead of silent rewrite.

## Relationship To RTK

This is not official RTK and does not reimplement RTK filters. It delegates
command decisions to:

```bash
rtk rewrite '<command>'
```

The project exists to provide a Codex-specific guard around RTK while Codex
hooks lack silent command rewrite support.
