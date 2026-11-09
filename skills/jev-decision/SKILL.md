---
name: jev-decision
description: Use Jev early for bounded, structured decisions in agent workflows: classify, choose among fixed options, score a rubric, prioritize, or judge a yes/no statement. Uses Jev Free only; paid Jev requires explicit user approval. Requires the OpenCode CLI connected to OpenCode Console.
license: MIT
compatibility: Requires Python 3 and the OpenCode CLI connected via /connect
metadata:
  author: Junho
  version: "2.0.0"
allowed-tools:
  - Bash
---

# Jev decision skill

Use Jev when an agent needs a small, well-scoped judgment that a typed answer can replace with less reasoning. Jev is a TypeSafe System One decision model, not a chat, summarization, or code-generation model: it returns typed values and probabilities instead of generated text.

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

The helper reads a JSON request from stdin with `state` and `questions` fields and calls the OpenCode local API, which reuses your connected OpenCode Console credentials. Do not request, add, or store a separate API key.

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

Requirements: Python 3 and the OpenCode CLI on PATH, connected once with `/connect`. No third-party packages. The helper uses `jev-1.13-free` only and does not retry with paid Jev; pass `--allow-paid-fallback` only when the user has explicitly approved paid cost. The helper writes the response as JSON to stdout and reports the model used to stderr. The CLI carries the state in local process arguments, so keep the state minimal.

Note on `noul` wording: write a statement, not a question with a question mark; higher values mean the statement is more likely true.

## Interpreting and acting on answers

- Validate each answer against its question type (`choice`, `score`, `noul`).
- `choice` and `score` return `probabilities` plus `confidence`. `confidence` measures how concentrated the distribution is; it is not a correctness guarantee. Low confidence should lead to a safe fallback, not a forced decision.
- `noul` returns a probability from 0 to 1 with no separate confidence field. Rough starting thresholds: 0.7 for yes, 0.3 for no; tune them to the cost of each mistake.
- `score` may be fractional between rubric levels (for example 1.4 between level 1 and 2); consume it as-is.
- Jev advises; your application logic remains responsible for permissions, invariants, confirmations, and final actions. Never use a Jev answer as the sole basis for a high-impact or destructive action.
- If credentials are missing or the request fails, say Jev was unavailable and use a concise conservative fallback. Do not fabricate a Jev result.

## Maintenance

`jev-1.13-free` is a limited-time model. A single 404, 410, timeout, or rate limit does not prove permanent retirement. If OpenCode's official model catalog confirms the free model ended, read [`docs/FREE_MODEL_RETIREMENT.md`](docs/FREE_MODEL_RETIREMENT.md) and follow it with user approval. Current availability and pricing: https://opencode.ai/v2/docs/console/models
