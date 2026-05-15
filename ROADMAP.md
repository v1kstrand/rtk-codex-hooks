# Roadmap

## MVP

- Codex `PreToolUse` hook for Bash commands.
- Deny-with-suggestion flow for commands that RTK can rewrite.
- `NO_RTK` escape hatch for raw output.
- Project/user installer that merges `hooks.json` and installs `NO_RTK`.
- Default selective policy for likely-noisy command prefixes.
- Minimal/default/full policy presets.
- Project config file support for local allow and candidate prefixes.
- Unit tests for hook decisions and installer output.

## Next

- Add end-to-end test notes for `/hooks` trust/activation.
- Add screenshots or terminal transcripts for README.

## Not Planned For MVP

- Transparent `updatedInput` rewrite. Codex currently does not reliably apply it.
- Reimplementing RTK filters. This project delegates rewrite decisions to RTK.
- Codex plugin packaging until plugin-scoped hooks are confirmed stable.
