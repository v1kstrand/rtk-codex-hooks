# RTK Codex Guard

Codex-focused guard hooks for [RTK](https://github.com/rtk-ai/rtk).

[RTK](https://github.com/rtk-ai/rtk) is a tool for reducing noisy command
output before it reaches an AI coding agent's context. That matters because
common coding commands like `git diff`, `rg`, `pytest`, `cargo test`, and
`npm test` can produce a lot of text. Less noise usually means less token
usage and a cleaner working context for the agent.

This repo exists because RTK's Codex setup is currently mostly instruction
based: you tell Codex to use RTK, but Codex can still forget and run the raw
command. RTK Codex Guard makes that harder to forget. It uses Codex hooks to
catch supported noisy commands before they run, block the raw command, and tell
Codex exactly how to retry with RTK.

This is not official RTK. It is a Codex-specific companion project for people
who want RTK behavior to be more explicit inside Codex.

RTK's own README claims large token savings on common development commands:
roughly 60-90% less token usage overall, with their example 30-minute coding
session going from about 118k raw tokens to about 24k RTK-filtered tokens. The
most noticeable examples they highlight are search and git commands around
75-80% smaller, and test commands such as `pytest`, `go test`, `cargo test`, and
`npm test` around 90% smaller. Actual savings will depend on the project and
commands being run.

## Why This Exists

- `AGENTS.md` guidance can be forgotten. A trusted hook cannot.
- RTK is the default for supported noisy commands.
- Raw command output is still available when the compact RTK output is not
  enough.

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

For project-specific behavior, add:

```text
.codex/rtk-guard.json
```

Use this when one repo needs a different preset, extra RTK candidates, or a few
commands that should stay raw.

```json
{
  "preset": "default",
  "allow_prefixes": ["git diff"],
  "candidate_prefixes": ["terraform plan", "make test"]
}
```

In this example, the repo uses the `default` preset, lets `git diff` run raw,
and also asks RTK about `terraform plan` and `make test`.

Fields:

| Field | Meaning |
| --- | --- |
| `preset` | One of `minimal`, `default`, or `full` |
| `allow_prefixes` | Commands that should run raw |
| `candidate_prefixes` | Extra commands that should be checked with RTK |

The examples in `examples/rtk-guard.*.json` can be copied into a project's
`.codex/rtk-guard.json`.

## Global Setup

You can also install RTK Codex Guard for your current computer user. In this
repo, "global" means Codex can see the hook from any project you open as that
same Linux/macOS user. It does not mean every user on the machine.

```bash
cd /path/to/rtk-codex-hooks
python3 install.py --target user
```

This creates or updates:

```text
~/.codex/hooks.json
```

Use this if you want the guard available across most or all of your Codex
projects.

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
