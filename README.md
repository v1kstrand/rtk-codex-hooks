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

## Recommended Setup

There are two ways to use this project:

- **Project setup:** use RTK Codex Guard in one repo only. This is the
  recommended choice for most people.
- **Global setup:** make RTK Codex Guard available everywhere Codex runs for
  your current computer user. Use this only if you already know you want it in
  most of your Codex sessions.

Most users should install RTK Codex Guard into one project at a time. That
means it only affects Codex when you are working inside that project.

First download this repo somewhere on your computer:

```bash
git clone https://github.com/v1kstrand/rtk-codex-hooks.git
```

You can also use GitHub's **Download ZIP** button and unpack it somewhere
instead.

Then go to the project where you want to use it:

```bash
cd /path/to/your/project
```

Install the hook into that project:

```bash
python3 /path/to/rtk-codex-hooks/install.py --target project
```

This creates or updates:

```text
/path/to/your/project/.codex/hooks.json
```

Now start Codex from that same project:

```bash
codex
```

Open:

```text
/hooks
```

Review, trust, and enable the hook.

This is the safest default because it does not change how Codex behaves in
your other projects.

### Choose A Preset

RTK Codex Guard has three built-in presets:

| Preset | Best For | What It Covers |
| --- | --- | --- |
| `minimal` | First-time users or cautious projects | Common noisy exploration commands like `git diff`, `git log`, `rg`, `grep`, `ls`, and `wc` |
| `default` | Most coding sessions | `minimal` plus common file viewing, search, test, build, lint, and type-check commands |
| `full` | Users who want RTK used as often as possible | `default` plus broader command families like `cargo`, `npx`, `make`, `terraform`, `docker`, `kubectl`, and `aws` |

The installer uses `default` unless you choose another preset:

```bash
python3 /path/to/rtk-codex-hooks/install.py --target project --preset minimal
python3 /path/to/rtk-codex-hooks/install.py --target project --preset default
python3 /path/to/rtk-codex-hooks/install.py --target project --preset full
```

Use `minimal` if you want the guard to be cautious. Use `default` if you are
not sure. Use `full` if you are comfortable with the guard interrupting more
commands and using `NO_RTK` when you need raw output.

Important: presets decide which commands the guard asks RTK about. The hook
still only blocks a command when RTK actually knows how to rewrite it.

### Project Config

For a project-specific setup, you can fine-tune behavior with:

```text
.codex/rtk-guard.json
```

Use this when one repo needs different behavior from your normal preset.

Example 1: choose a preset for this repo:

```json
{
  "preset": "minimal"
}
```

Example 2: let one command stay raw:

```json
{
  "preset": "default",
  "allow_prefixes": ["git diff"]
}
```

This means `git diff` will run normally instead of being routed through RTK.

Example 3: add extra commands for this repo:

```json
{
  "preset": "default",
  "candidate_prefixes": ["terraform plan", "make test"]
}
```

This means the guard will also ask RTK about `terraform plan` and `make test`.

Example 4: combine both:

```json
{
  "preset": "default",
  "allow_prefixes": ["git diff"],
  "candidate_prefixes": ["terraform plan", "make test"]
}
```

Available config fields:

| Field | Meaning |
| --- | --- |
| `preset` | One of `minimal`, `default`, or `full` |
| `allow_prefixes` | Commands that should stay raw |
| `candidate_prefixes` | Extra commands that should be checked with RTK |

The examples in `examples/rtk-guard.*.json` can be copied into a project's
`.codex/rtk-guard.json`.

## Global Setup

You can also install RTK Codex Guard globally:

```bash
cd /path/to/rtk-codex-hooks
python3 install.py --target user
```

This creates or updates:

```text
~/.codex/hooks.json
```

Use global setup if you want the guard available in all Codex projects for
your current Linux/macOS user.

Important: once you trust and enable a global hook in Codex, that choice may
persist across future Codex sessions. If you only want to try the guard in one
repo, use the project setup above instead.

By default the installer:

- backs up existing `hooks.json`
- merges this hook with existing `PreToolUse` hooks
- installs `NO_RTK` to `~/.local/bin/NO_RTK`

In `/hooks`, look for the hook named:

```text
RTK Codex Guard
```

Some Codex versions still show numbered rows such as `Hook 1`; in that case,
check the detail field `Status`/`Command` for `Suggesting RTK for noisy command`.

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

Remove a project install while keeping unrelated hooks:

```bash
cd /path/to/your/project
python3 /path/to/rtk-codex-hooks/uninstall.py --target project
```

Remove a global install:

```bash
cd /path/to/rtk-codex-hooks
python3 uninstall.py --target user
```

Use `/hooks` to disable it manually if you prefer.

## Default Policy

The hook is intentionally selective.

Allowed without asking RTK in every preset:

```text
echo, pwd, date, cd, mkdir, touch, chmod, git rev-parse, git branch, git remote
```

Candidate commands in the default preset:

```text
git status, git diff, git show, git log
ls, tree, find, fd, rg, grep, wc, cat, head, tail
npm/pnpm/yarn/bun tests
cargo test/build/check
pytest, vitest, jest, tsc, eslint, ruff, mypy
go test/build
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
