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

## Install

Install into the current project:

```bash
python3 install.py --target project --force
```

Or install globally for the current Codex user:

```bash
python3 install.py --target user --force
```

Then restart Codex, open `/hooks`, and trust/enable the hook named:

```text
Suggesting RTK for noisy command
```

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

If the installed `hooks.json` still matches this project:

```bash
python3 uninstall.py --target project
```

Use `/hooks` to disable the hook if you have edited or merged it with other
hook entries.

## Development

```bash
python3 -m unittest discover -s tests
```

## Current Codex Limitation

Codex currently parses but does not reliably apply `PreToolUse.updatedInput`.
That is why this project uses deny-with-suggestion instead of silent rewrite.

