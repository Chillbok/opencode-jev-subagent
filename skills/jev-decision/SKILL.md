---
name: jev-decision
description: Decide, choose, classify, rank, score, or judge yes/no with Jev before deliberating. Use for 결정, 선택, 분류, 우선순위, 점수, 충족 여부 판단 when the answer changes the next action and the state fits in about 150 words. TypeSafe-only; no fallback source.
license: MIT
compatibility: Requires Python 3 and a TypeSafe API key (no third-party packages)
metadata:
  author: Junho
  version: "2.0.0"
allowed-tools:
  - Bash
---

# Jev decision skill

Use Jev when an agent needs a small, well-scoped judgment that a typed answer can replace with less reasoning. Jev is a TypeSafe System One decision model, not a chat, summarization, or code-generation model: it returns typed values and probabilities instead of generated text.

Before writing a long deliberation, check two conditions. Call Jev when both hold: (a) the answer changes the next action (a branch, a classification, an accept/reject), and (b) the relevant state fits in roughly 150 words built from the option set and the decisive facts. If unsure whether a case qualifies, call it; a few small calls per session is normal.

## Good fits

- `choice`: classify an item or select one option from a fixed set (up to 255 options).
- `score`: rate one dimension against an explicit ordered rubric (2 to 10 levels).
- `noul`: estimate whether a clearly worded statement is true.
- Confidence-aware routing: act on clear, low-impact results and escalate uncertain or consequential cases to a person or a stronger process.

Follow these rules for effectiveness and cost:

- Ask atomic questions. Split multi-factor judgments into independent questions and combine their answers in your own logic. Broad questions hide several judgments behind one answer.
- Batch all related independent questions about the same state into one request. Questions run in parallel, which maximizes intelligence per dollar.
- Send only the minimum relevant state. Do not paste large documents or unrelated context; state + all questions must fit 64k tokens total (32k per single question).
- Use Jev early, before extended deliberation. Do not reason to an answer first and then check with Jev.

Do not use Jev to generate prose or code, perform open-ended analysis, decide exact facts that ordinary code can check, accept long inputs whose transfer cost outweighs the decision, or make high-impact/destructive decisions without deterministic safeguards or human confirmation. Never send secrets or unnecessary sensitive data.

## Calling Jev

The helper reads a JSON request from stdin with `state` and `questions` fields and calls one source:

**TypeSafe API** (`POST https://api.typesafe.ai/v1/systemone`, model `jev-latest`) when `TYPESAFE_API_KEY` is set in the environment or `~/.config/opencode/jev-decision/typesafe_key` exists. Billed to the user's TypeSafe balance.

There is no fallback source. If the key is missing or the request fails, the helper exits 1 with a reason on stderr (`401/403` key, `402` balance, `429` rate limit, `5xx` service) and prints nothing to stdout. Report the failure and fall back to a conservative answer yourself instead of inventing a Jev result. Use only the user's own TypeSafe key; do not request or store other API keys.

```sh
python3 ~/.config/opencode/jev-decision/opencode_decisions.py <<'JSON'
{
  "state": "The deployment failed because the database migration timed out.",
  "questions": {
    "category": {
      "type": "choice",
      "instructions": "Which team should investigate this failure?",
      "criteria": {
        "database": "Database schema, migration, or query issue",
        "deployment": "Build, release, or deployment infrastructure issue",
        "application": "Application code or runtime issue",
        "other": "None of the above"
      }
    },
    "urgent": {
      "type": "noul",
      "instructions": "This failure blocks a production deployment right now."
    }
  }
}
JSON
```

Requirements: Python 3 and a TypeSafe API key. The helper writes the response as JSON to stdout, with `data.answers` in one shape and `source` set to `typesafe`; it reports the model used and TypeSafe input tokens to stderr. It also appends one metadata-only line per call to `~/.local/state/jev/usage.jsonl` (timestamp, model, question count and types, state byte size, input tokens, elapsed ms, outcome). State and question text are never logged.

Note on `noul` wording: write a statement, not a question with a question mark; higher values mean the statement is more likely true.

## Interpreting and acting on answers

- Validate each answer against its question type (`choice`, `score`, `noul`).
- `choice` and `score` return `probabilities` plus `confidence`. `confidence` measures how concentrated the distribution is; it is not a correctness guarantee. Low confidence should lead to a safe fallback, not a forced decision.
- `noul` returns a probability from 0 to 1 with no separate confidence field. Rough starting thresholds: 0.7 for yes, 0.3 for no; tune them to the cost of each mistake.
- `score` may be fractional between rubric levels (for example 1.4 between level 1 and 2); consume it as-is.
- Jev advises; your application logic remains responsible for permissions, invariants, confirmations, and final actions. Never use a Jev answer as the sole basis for a high-impact or destructive action.
- If credentials are missing or the request fails, say Jev was unavailable and use a concise conservative fallback. Do not fabricate a Jev result.

## Measuring cost

Each call appends one JSON line to `~/.local/state/jev/usage.jsonl`, for example `input_tokens` and `elapsed_ms`. Aggregate it before claiming any token saving, for example:

```sh
jq -s 'map(select(.outcome=="ok")) | {calls:length, tokens:(map(.input_tokens // 0)|add), avg_ms:(map(.elapsed_ms)|add/length)}' ~/.local/state/jev/usage.jsonl
```

A Jev call is only a net token saving when the deliberation it replaces would have been longer than the state sent plus the result round-trip. Measure, do not assume.
