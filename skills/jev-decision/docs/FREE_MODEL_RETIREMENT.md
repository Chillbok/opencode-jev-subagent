# Jev free-model retirement procedure

Use this procedure when the limited-time `jev-1.13-free` model may have ended. The helper does not automatically fall back to paid Jev, and a transient request failure does not change future behavior.

## Confirm retirement first

1. Check the current OpenCode Console [model catalog](https://opencode.ai/v2/docs/console/models) and official notices for Jev 1.13 Free.
2. Treat a single HTTP 404/410, 429, timeout, or 5xx as an availability signal, not proof of permanent retirement.
3. If official information is unclear, keep Free-only default behavior and report the uncertainty. Do not change the agent or helper based only on a transient failure.

## Update the package after official confirmation

Once official retirement is confirmed:

1. Ask the user whether to stop using Jev or explicitly authorize paid Jev. Do not make paid Jev the default without their approval.
2. If the user approves paid use, update `scripts/opencode_decisions.py`, `agents/jev-decider.md`, the README, and sync instructions consistently. Paid fallback must still require explicit authorization unless the user explicitly approves a new default.
3. Update any installation or maintenance documentation that describes Jev Free as currently available. Preserve this procedure as historical maintenance context or revise it to match the model lifecycle.
4. Run local checks without sending a live request: parse the Python source, run `python3 scripts/opencode_decisions.py --help`, and run mocked request tests if available. Do not send user state during tests.
5. Summarize the official source and date of confirmation. Do not silently change the paid-use policy during a normal Jev decision call.

Do not push changes unless explicitly requested through the repository's `jev-sync` skill. Commit only reviewed Jev-package changes and leave unrelated work untouched.
