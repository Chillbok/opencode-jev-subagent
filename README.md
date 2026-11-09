# Jev Decision Skills for Coding Agents

Portable Agent Skills that send bounded decisions (classification, fixed-choice selection, rubric scoring, prioritization, yes/no checks) to Jev, TypeSafe's System One decision model, plus a sync skill that keeps local installs and this repository aligned.

Jev returns typed values and probabilities instead of generated text, so it replaces the prompt-and-parse step for narrow judgments. `jev-1.13-free` is used by default (currently free, limited-time); paid Jev fallback requires explicit user approval. Current availability and pricing: https://opencode.ai/v2/docs/console/models

## Requirements

For every tool:

- Python 3 (no third-party packages)
- OpenCode CLI installed and connected once with `/connect` — the helper calls OpenCode's local decisions API, which reuses your connected Console credentials. No separate API key.

## Install with your coding agent

Clone this repository, then copy and send the prompt for your tool to that agent. The agent reads this README, installs the skills, updates its global instruction file, and validates the result.

### OpenCode

```text
Read this repository's README.md and install the Jev decision skills for OpenCode. Copy skills/jev-decision and skills/jev-sync to ~/.config/opencode/skills/ (create directories as needed), copy skills/jev-decision/scripts/opencode_decisions.py to ~/.config/opencode/jev-decision/opencode_decisions.py, and update ~/.config/opencode/AGENTS.md with the Jev usage rules from this README's "Global instruction block" section, preserving all unrelated content. Remove ~/.config/opencode/agents/jev-decider.md if it exists. Do not connect accounts or services. Validate: python3 syntax check and --help on the helper, cmp of installed files against the repository, and confirm the instruction file contains the rules. If you want a live Jev request to confirm service access, ask me first. Report all changed paths and validation results.
```

### Claude Code

```text
Read this repository's README.md and install the Jev decision skills for Claude Code. Copy skills/jev-decision and skills/jev-sync to ~/.claude/skills/ (create if needed), copy skills/jev-decision/scripts/opencode_decisions.py to ~/.config/opencode/jev-decision/opencode_decisions.py, and append the Jev usage rules from this README's "Global instruction block" section to ~/.claude/CLAUDE.md without deleting or rewriting any existing content. Do not connect accounts or services. Validate: python3 syntax check and --help on the helper, cmp of installed files against the repository, and confirm CLAUDE.md now contains the rules. Then tell me to run /skills (or /doctor) to confirm the skills are listed. Report all changed paths and validation results.
```

### Codex

```text
Read this repository's README.md and install the Jev decision skills for Codex. Copy skills/jev-decision and skills/jev-sync to ~/.agents/skills/ (create if needed; use ~/.codex/skills/ only if ~/.agents/skills/ is not the active location), copy skills/jev-decision/scripts/opencode_decisions.py to ~/.config/opencode/jev-decision/opencode_decisions.py, and append the Jev usage rules from this README's "Global instruction block" section to ~/.codex/AGENTS.md without deleting existing content. If ~/.codex/AGENTS.override.md exists and is non-empty, stop and warn me, because it would hide AGENTS.md. Do not connect accounts or services. Validate: python3 syntax check and --help on the helper, cmp of installed files against the repository, and confirm AGENTS.md contains the rules. Then suggest I run: codex --ask-for-approval never "Summarize the current instructions." to confirm Codex reads them. Report all changed paths and validation results.
```

### Other tools

Manual installation: copy each directory under `skills/` into your agent's global skills directory (the Agent Skills convention is `~/.agents/skills/`), copy the helper to `~/.config/opencode/jev-decision/opencode_decisions.py`, and add the global instruction block below to your agent's always-loaded instructions file. The SKILL.md frontmatter uses only the six portable Agent Skills fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).

## Global instruction block

Add these lines to your tool's global instructions file (OpenCode `~/.config/opencode/AGENTS.md`, Claude Code `~/.claude/CLAUDE.md`, Codex `~/.codex/AGENTS.md`). They make the agent use Jev early instead of after long deliberation:

```markdown
- Bounded decisions (classification, selecting among fixed options, rubric scoring, prioritization, and clearly stated yes/no checks): you MUST use the jev-decision skill early, before extended model deliberation, whenever its structured answer can replace that deliberation. Batch related atomic questions in one request and send only the minimum relevant state; do not decide first and use Jev as a post-hoc check. Do not use Jev for facts that code can directly verify, open-ended analysis or generation, large inputs whose transfer cost outweighs the decision, or high-impact/destructive decisions without deterministic safeguards and human confirmation. Use Jev Free only; do not authorize paid Jev unless the user explicitly approves its cost. If Jev is unavailable, use a concise conservative fallback and report the limitation. Never send secrets or unnecessary sensitive data.
- After changing the jev-decision skill, its helper, or its documentation, use the jev-sync skill to synchronize the package with its repository. It may commit and push reviewed Jev-only changes; never include unrelated changes or force-push.
```

## Components

- `skills/jev-decision/` — Jev usage skill: when and how to ask, how to read answers, Free-only helper.
- `skills/jev-decision/scripts/opencode_decisions.py` — typed Jev API helper (installed to the fixed path `~/.config/opencode/jev-decision/`).
- `skills/jev-decision/docs/FREE_MODEL_RETIREMENT.md` — maintenance procedure if Jev Free ends.
- `skills/jev-sync/` — bidirectional sync between installed mirrors and this repository.

## Updating

After changing any Jev skill, helper, or documentation file, invoke the `jev-sync` skill (say "sync Jev"). It compares content and Git history, not file modification times:

- Only local changed: copy to repository, review the diff, commit Jev-only paths, push.
- Only repository changed: `git pull --ff-only`, then update every installed mirror.
- Both changed or unrelated files present: stops and asks you.

The sync skill is authorized to commit and push reviewed Jev-only changes. Never force-push.

## Uninstalling

Remove the skill directories from each tool's global skills directory (`~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`), delete `~/.config/opencode/jev-decision/`, and remove only the two Jev lines from your global instruction file. Preserve everything else.

## Roadmap

- [x] OpenCode
- [x] Claude Code
- [x] Codex
- [ ] Additional Agent Skills-compatible tools
