# Roadmap

## MVP

- Codex `PreToolUse` hook for Bash commands.
- Deny-with-suggestion flow for commands that RTK can rewrite.
- `NO_RTK` escape hatch for raw output.
- Project/user installer that writes `hooks.json`.
- Unit tests for hook decisions and installer output.

## Next

- Add a default allow/block policy so tiny commands are not sent through RTK.
- Add config file support for excludes and additional bypass prefixes.
- Add shell integration option to put `NO_RTK` on `PATH`.
- Add end-to-end test notes for `/hooks` trust/activation.
- Add screenshots or terminal transcripts for README.

## Not Planned For MVP

- Transparent `updatedInput` rewrite. Codex currently does not reliably apply it.
- Reimplementing RTK filters. This project delegates rewrite decisions to RTK.
- Codex plugin packaging until plugin-scoped hooks are confirmed stable.

