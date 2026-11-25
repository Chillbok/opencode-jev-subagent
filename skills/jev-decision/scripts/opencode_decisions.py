#!/usr/bin/env python3
"""Make typed Jev decisions through TypeSafe's systemone API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TYPESAFE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
TYPESAFE_MODEL = "jev-latest"
TYPESAFE_KEY_ENV = "TYPESAFE_API_KEY"
TYPESAFE_KEY_FILE = Path.home() / ".config" / "opencode" / "jev-decision" / "typesafe_key"
USAGE_LOG = Path.home() / ".local" / "state" / "jev" / "usage.jsonl"


class RequestFailure(Exception):
    """A request failed. There is no fallback source by design."""


def _question_types(payload: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for question in payload.get("questions", {}).values():
        name = question.get("type") if isinstance(question, dict) else None
        if isinstance(name, str):
            counts[name] = counts.get(name, 0) + 1
    return counts


def _log_usage(record: dict[str, Any]) -> None:
    """Append one metadata-only line per call. Never stores state or question text."""
    try:
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _choice_list(criteria: Any, question_id: str) -> list[dict[str, Any]]:
    if isinstance(criteria, dict):
        choices = [{"value": value, "description": description} for value, description in criteria.items()]
    elif isinstance(criteria, list):
        choices = [{"value": item, "description": item} for item in criteria]
    else:
        raise ValueError(f"Choice question {question_id!r} needs a criteria object or list.")
    if not choices or any(not isinstance(item["value"], (str, bool)) for item in choices):
        raise ValueError(f"Choice question {question_id!r} needs non-empty string/boolean choice values.")
    if any(not isinstance(item["description"], str) for item in choices):
        raise ValueError(f"Choice descriptions for {question_id!r} must be strings.")
    return choices


def _score_levels(criteria: Any, question_id: str) -> list[dict[str, str]]:
    if not isinstance(criteria, list) or not criteria:
        raise ValueError(f"Score question {question_id!r} needs a non-empty criteria list.")
    levels: list[dict[str, str]] = []
    for item in criteria:
        if isinstance(item, str):
            levels.append({"label": item})
        elif isinstance(item, dict) and isinstance(item.get("label"), str):
            level = {"label": item["label"]}
            if isinstance(item.get("description"), str):
                level["description"] = item["description"]
            levels.append(level)
        else:
            raise ValueError(f"Score criteria for {question_id!r} must be strings or objects with a label.")
    return levels


def to_typesafe_request(payload: Any, model_id: str) -> dict[str, Any]:
    """Validate the shared input shape and build a native TypeSafe systemone request."""
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    state = payload.get("state")
    if state is None or state == "":
        raise ValueError("Input must include a non-empty 'state'.")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("Input must include a non-empty 'questions' object.")

    native_questions: dict[str, Any] = {}
    for question_id, question in questions.items():
        if not isinstance(question, dict) or not isinstance(question.get("instructions"), str):
            raise ValueError(f"Question {question_id!r} needs an instructions string.")
        instructions = question["instructions"]
        question_type = question.get("type")

        if question_type == "choice":
            criteria = {
                item["value"]: item["description"] for item in _choice_list(question.get("criteria"), question_id)
            }
            native_questions[question_id] = {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria,
            }
        elif question_type == "score":
            levels: list[Any] = []
            for level in _score_levels(question.get("criteria"), question_id):
                if "description" in level:
                    levels.append(level)
                else:
                    levels.append(level["label"])
            native_questions[question_id] = {
                "type": "score",
                "instructions": instructions,
                "criteria": levels,
            }
        elif question_type == "noul":
            criteria = question.get("criteria")
            if criteria:
                instructions = f"{instructions}\nClarification: {criteria}"
            native_questions[question_id] = {"type": "noul", "instructions": instructions}
        else:
            raise ValueError(f"Question {question_id!r} needs type choice, score, or noul.")

    return {"model": model_id, "state": state, "questions": native_questions}


def normalize_typesafe_response(response: dict[str, Any], question_ids: list[str]) -> dict[str, Any]:
    """Convert TypeSafe answers into OpenCode's answer-list shape."""
    raw_answers = response.get("answers")
    if not isinstance(raw_answers, dict):
        raise RequestFailure("TypeSafe response did not contain an answers object")

    answers: list[dict[str, Any]] = []
    for question_id in question_ids:
        answer = raw_answers.get(question_id)
        if not isinstance(answer, dict):
            answers.append({"type": "error", "name": question_id, "reason": "no answer returned"})
            continue
        answer_type = answer.get("type")

        if answer_type == "noul":
            answers.append(
                {"type": "predicate", "name": question_id, "probability": answer.get("noul")}
            )
        elif answer_type == "choice":
            probabilities = answer.get("probabilities")
            if not isinstance(probabilities, dict):
                probabilities = {}
            answers.append(
                {
                    "type": "choice",
                    "name": question_id,
                    "choice": answer.get("choice"),
                    "probabilities": [
                        {"value": value, "probability": probability}
                        for value, probability in probabilities.items()
                    ],
                    "confidence": answer.get("confidence"),
                }
            )
        elif answer_type == "score":
            probabilities = answer.get("probabilities")
            legend = answer.get("legend")
            if not isinstance(probabilities, dict):
                probabilities = {}
            if not isinstance(legend, dict):
                legend = {}
            levels = []
            for key, probability in probabilities.items():
                label = legend.get(key, key)
                if isinstance(label, dict) and isinstance(label.get("label"), str):
                    label = label["label"]
                elif not isinstance(label, str):
                    label = json.dumps(label, ensure_ascii=False)
                try:
                    value: Any = int(key)
                except (TypeError, ValueError):
                    value = key
                levels.append({"value": value, "label": label, "probability": probability})
            answers.append(
                {
                    "type": "score",
                    "name": question_id,
                    "score": answer.get("score"),
                    "probabilities": levels,
                    "confidence": answer.get("confidence"),
                }
            )
        else:
            answers.append(
                {"type": "error", "name": question_id, "reason": f"unsupported answer type {answer_type!r}"}
            )

    return {
        "data": {"answers": answers},
        "model": response.get("model"),
        "source": "typesafe",
        "usage": response.get("usage"),
    }


def _typesafe_key() -> str | None:
    key = os.environ.get(TYPESAFE_KEY_ENV, "").strip()
    if key:
        return key
    try:
        key = TYPESAFE_KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return key or None


def _typesafe_hint(status: int) -> str:
    if status in {401, 403}:
        return f"HTTP {status} (check {TYPESAFE_KEY_ENV} or {TYPESAFE_KEY_FILE})"
    if status == 402:
        return "HTTP 402 (check the TypeSafe balance)"
    if status == 429:
        return "HTTP 429 (rate limited)"
    if status >= 500:
        return f"HTTP {status} (TypeSafe service error)"
    return f"HTTP {status}"


def request_typesafe(payload: dict[str, Any], model_id: str, key: str, timeout: float) -> dict[str, Any]:
    request = to_typesafe_request(payload, model_id)
    body = json.dumps(request, ensure_ascii=False).encode("utf-8")
    http_request = urllib.request.Request(
        TYPESAFE_ENDPOINT,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise RequestFailure(_typesafe_hint(error.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RequestFailure(f"TypeSafe request failed ({type(error).__name__})") from None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise RequestFailure("TypeSafe returned invalid JSON") from None
    if not isinstance(parsed, dict):
        raise RequestFailure("TypeSafe returned a non-object response") from None
    return normalize_typesafe_response(parsed, list(payload["questions"].keys()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=45.0, help="per-request timeout in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        payload = json.load(sys.stdin)
        # Validate before starting any request.
        to_typesafe_request(payload, TYPESAFE_MODEL)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return 2

    # Single source: TypeSafe. There is no fallback by design, so failures are reported.
    key = _typesafe_key()
    base: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": TYPESAFE_MODEL,
        "questions": len(payload["questions"]),
        "types": _question_types(payload),
        "state_bytes": len(json.dumps(payload.get("state"), ensure_ascii=False).encode("utf-8")),
    }
    if not key:
        _log_usage({**base, "outcome": "error", "error": "no_key", "elapsed_ms": 0})
        print(
            f"Jev unavailable: no TypeSafe key ({TYPESAFE_KEY_ENV} or {TYPESAFE_KEY_FILE}). "
            "No fallback is configured.",
            file=sys.stderr,
        )
        return 1

    started = time.monotonic()
    try:
        response = request_typesafe(payload, TYPESAFE_MODEL, key, args.timeout)
    except RequestFailure as error:
        elapsed = int((time.monotonic() - started) * 1000)
        _log_usage({**base, "outcome": "error", "error": str(error), "elapsed_ms": elapsed})
        print(
            f"Jev unavailable: typesafe/{TYPESAFE_MODEL} {error}. No fallback is configured.",
            file=sys.stderr,
        )
        return 1

    elapsed = int((time.monotonic() - started) * 1000)
    usage = response.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    model_used = response.get("model") or TYPESAFE_MODEL
    _log_usage(
        {
            **base,
            "model": model_used,
            "outcome": "ok",
            "input_tokens": tokens,
            "elapsed_ms": elapsed,
        }
    )
    suffix = f" (input_tokens={tokens})" if isinstance(tokens, int) else ""
    print(f"Jev answered using typesafe/{model_used}{suffix}.", file=sys.stderr)
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
