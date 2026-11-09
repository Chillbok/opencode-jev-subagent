---
name: jev-sync
description: Sync the installed Jev decision skills and helper with their GitHub repository in either direction, handling conflicts safely and committing/pushing reviewed Jev-only updates. Use after changing any Jev skill, helper, or documentation file.
license: MIT
compatibility: Requires Python 3, git, and the OpenCode CLI
metadata:
  author: Junho
  version: "2.0.0"
allowed-tools:
  - Bash
---

# Jev Sync

Maintain the Jev decision package between local installations and the Git repository.

## Paths

Repository: `/Users/junho/Repositories/opencode-jev-subagent`

Source files in the repository:

- `skills/jev-decision/` (SKILL.md, scripts/opencode_decisions.py, docs/FREE_MODEL_RETIREMENT.md)
- `skills/jev-sync/SKILL.md`

Installed mirrors (sync every one that exists):

| Tool | Skill directory | Path |
|------|-----------------|------|
| OpenCode | jev-decision, jev-sync | `~/.config/opencode/skills/<skill>/` |
| Claude Code | jev-decision, jev-sync | `~/.claude/skills/<skill>/` |
| Codex | jev-decision, jev-sync | `~/.agents/skills/<skill>/` (fallback: `~/.codex/skills/<skill>/`) |

Shared helper (all tools call this one path):

- Local: `~/.config/opencode/jev-decision/opencode_decisions.py`
- Repository: `skills/jev-decision/scripts/opencode_decisions.py`

Global instruction files are NOT synced into the repository; they hold tool-specific wording:

- OpenCode: `~/.config/opencode/AGENTS.md`
- Claude Code: `~/.claude/CLAUDE.md`
- Codex: `~/.codex/AGENTS.md`

## Direction and conflict rules

Do not use file modification times to select a winner. They are not reliable across machines.

1. Inspect `git status --short --branch`, current branch, local changes, and available remote updates. Do not discard or overwrite unrecognized work.
2. Compare every installed mirror and the helper with the repository working tree and committed `HEAD`.
3. If only local installations differ from the repository's committed content, sync local -> repository.
4. If only the repository has committed changes and local mirrors are unchanged from their prior content, sync repository -> local. Fetch and pull with `--ff-only` before applying remote changes, then update every installed mirror.
5. If both sides changed the same component, or the repository has unrelated modified files, stop and ask the user how to resolve it. Never guess based on timestamps.
6. If the user explicitly requests an upload or download, follow that direction only after checking for conflicts.

## Local -> repository

1. Compare files with `diff`; copy only changed Jev package files into the matching repository paths. Do not copy global instruction files or unrelated content into the repository.
2. Review `git status` and `git diff --` for only `skills/jev-decision/`, `skills/jev-sync/`, and relevant README/docs files.
3. If unrelated changes are present, do not stage them. Stage only the Jev package paths, review the staged diff, and create a concise commit.
4. Push the current branch normally. Never force-push. If commit or push fails, report the error and stop; do not retry automatically.
5. Copy the committed repository versions back to every installed mirror so all sides match.

The user has authorized committing and pushing Jev-only changes through this skill after the staged diff is reviewed. This authorization does not include force-pushes, unrelated changes, or conflict resolution.

## Repository -> local

1. Check for local uncommitted changes first. If any installed component differs from the last synchronized repository version, stop and ask before overwriting it.
2. Run `git pull --ff-only` in the repository. If it fails or is not a fast-forward, stop and report the issue.
3. Copy the repository skill directories to every installed mirror that exists, and copy the helper to `~/.config/opencode/jev-decision/opencode_decisions.py`. Preserve unrelated files.
4. Validate the copied files and report the commit and paths updated.

## After syncing

Run `python3 -m py_compile skills/jev-decision/scripts/opencode_decisions.py`, confirm installed mirrors match the repository with `cmp`, and confirm repository cleanliness after upload. Never send a live Jev request as part of syncing unless the user asks for a live check.
