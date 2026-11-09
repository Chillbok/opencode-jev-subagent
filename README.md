# OpenCode Jev Subagent

This repository provides an OpenCode subagent that sends bounded decisions to Jev, plus a global skill for maintaining this repository from an OpenCode installation.

The subagent replaces the global `jev-decision` usage skill. The installed package consists of:

- `jev-decider` agent: `~/.config/opencode/agents/jev-decider.md`
- Jev request helper: `~/.config/opencode/jev-decision/opencode_decisions.py`
- `jev-sync` skill: `~/.config/opencode/skills/jev-sync/SKILL.md`
- Global OpenCode instructions: `~/.config/opencode/AGENTS.md`

Jev Free is used by default. The helper does not automatically retry with paid Jev. Paid fallback requires explicit user approval and the `--allow-paid-fallback` option. Jev Free is currently listed as free and limited-time; check the [OpenCode Console model catalog](https://opencode.ai/v2/docs/console/models) for current availability and prices.

## Install with an OpenCode agent

Clone this repository, then copy and send the following prompt to your OpenCode agent:

```text
Read this repository's README.md and install this OpenCode Jev subagent. Inspect the existing global OpenCode configuration and preserve unrelated settings and files. Install the jev-decider agent, its helper script, and the jev-sync skill; update ~/.config/opencode/AGENTS.md to require jev-decider for applicable bounded decisions and jev-sync after Jev component changes; then remove the old global jev-decision usage skill only after the new agent and helper are in place. Do not connect accounts or services. Validate the agent configuration, helper syntax and mocked Free-only request path. If you need a live Jev request to confirm service access, ask me first. Report all changed paths and validation results.
```

This repository currently supports OpenCode only. Claude Code and Codex support are future roadmap items; their agent formats and installation workflows are not included yet.

## Components

- `agents/jev-decider.md`: OpenCode global subagent definition and its minimal decision workflow.
- `scripts/opencode_decisions.py`: typed Jev API helper. Free-only by default; paid fallback is opt-in.
- `docs/FREE_MODEL_RETIREMENT.md`: maintenance procedure if Jev Free is officially retired.
- `skills/jev-sync/SKILL.md`: bidirectional sync and repository update procedure.

## Updating

When changing Jev agent, helper, or documentation files, invoke the installed `jev-sync` skill. It compares content and Git history, not file modification times (which are unreliable across computers).

- Local installation has changes and the repository is unchanged: sync local changes to the repository, review the exact diff, commit the Jev-only changes, and push.
- The repository has newer committed changes and the local installation is unchanged: update the repository with `git pull --ff-only`, then sync repository files to the local installation.
- Both sides changed, or unrelated repository changes exist: stop and ask which changes to keep; do not overwrite or commit unrelated work.
- If repository files are edited directly, sync them to the local installation after the repository update.

The user has authorized the `jev-sync` skill to commit and push Jev-only changes after reviewing the staged diff. Never force-push. Ask before overwriting conflicts or handling unrelated changes.

## Uninstalling

Remove only the installed Jev components: `~/.config/opencode/agents/jev-decider.md`, `~/.config/opencode/jev-decision/`, and `~/.config/opencode/skills/jev-sync/`. Revert only the Jev-specific additions in `~/.config/opencode/AGENTS.md`. Preserve other global settings and skills.
