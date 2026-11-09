---
name: jev-sync
description: Sync the installed OpenCode Jev subagent package and this GitHub repository in either direction, handling conflicts safely and committing/pushing reviewed Jev-only updates.
compatibility: opencode
metadata:
  author: Junho
  version: "1.0.0"
allowed-tools:
  - Bash
---

# Jev Sync

Maintain the OpenCode Jev subagent package between the local installation and the Git repository.

## Paths

- Repository: `/Users/junho/Repositories/opencode-jev-subagent`
- Agent: `~/.config/opencode/agents/jev-decider.md` <-> `agents/jev-decider.md`
- Helper: `~/.config/opencode/jev-decision/opencode_decisions.py` <-> `scripts/opencode_decisions.py`
- Retirement guide: `docs/FREE_MODEL_RETIREMENT.md` (repository source; copy to the installation only if needed)
- This skill: `~/.config/opencode/skills/jev-sync/SKILL.md` <-> `skills/jev-sync/SKILL.md`

## Direction and conflict rules

Do not use file modification times to select a winner. They are not reliable across machines.

1. Inspect `git status --short --branch`, current branch, local changes, and available remote updates. Do not discard or overwrite unrecognized work.
2. Compare the installed agent/helper/skill contents with the repository working tree and committed `HEAD`.
3. If only the local installation differs from the repository's committed content, sync local -> repository.
4. If only the repository has committed changes and the local installation is unchanged from its prior content, sync repository -> local. Fetch/pull with `--ff-only` before applying remote changes.
5. If both sides changed the same component, or the repository has unrelated modified files, stop and ask the user how to resolve it. Never guess based on timestamps.
6. If the user explicitly requests an upload or download, follow that direction only after checking for conflicts.

## Local -> repository

1. Compare files with `diff`; copy only changed Jev components into the matching repository paths. Do not sync global `AGENTS.md` or unrelated files into the repository.
2. Review `git status` and `git diff --` for only `agents/jev-decider.md`, `scripts/opencode_decisions.py`, `skills/jev-sync/SKILL.md`, and relevant docs/README files.
3. If unrelated changes are present, do not stage them. Stage only the Jev package paths, review the staged diff, and create a concise commit.
4. Push the current branch normally. Never force-push. If commit or push fails, report the error and stop; do not retry automatically.
5. Copy the committed repository versions back to the local installation if needed, so both sides match.

The user has authorized committing and pushing Jev-only changes through this skill after the staged diff is reviewed. This authorization does not include force-pushes, unrelated changes, or conflict resolution.

## Repository -> local

1. Check for local uncommitted changes first. If any installed component differs from the last synchronized repository version, stop and ask before overwriting it.
2. Run `git pull --ff-only` in the repository. If it fails or is not a fast-forward, stop and report the issue.
3. Copy the repository agent, helper, and skill into their corresponding global locations. Preserve unrelated files.
4. Validate the copied files and report the commit and paths updated.

## After syncing

Run a syntax check on `scripts/opencode_decisions.py`, inspect the installed agent and skill paths, and confirm repository cleanliness after upload. Never send a live Jev request as part of syncing unless the user asks for a live check.
