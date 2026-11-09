#!/usr/bin/env python3
"""Make typed Jev decisions through OpenCode's connected provider account."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from typing import Any


API_PATH = "/api/experimental/generate/decisions"
PROVIDER_ID = "opencode"
FREE_MODEL = "jev-1.13-free"
PAID_MODEL = "jev-1.13"
FALLBACK_STATUSES = {408, 410, 425, 429, 422}


class RequestFailure(Exception):
    def __init__(self, message: str, fallbackable: bool) -> None:
        super().__init__(message)
        self.fallbackable = fallbackable


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


def to_opencode_request(payload: Any, model_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    state = payload.get("state")
    if state is None or state == "":
        raise ValueError("Input must include a non-empty 'state'.")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("Input must include a non-empty 'questions' object.")

    if isinstance(state, str):
        input_parts = [{"type": "text", "text": state}]
    else:
        input_parts = [{"type": "json", "value": state}]

    native_questions = []
    for question_id, question in questions.items():
        if not isinstance(question, dict) or not isinstance(question.get("instructions"), str):
            raise ValueError(f"Question {question_id!r} needs an instructions string.")
        instructions = question["instructions"]
        question_type = question.get("type")
        native: dict[str, Any] = {"name": question_id, "instructions": instructions}

        if question_type == "choice":
            native.update({"type": "choice", "choices": _choice_list(question.get("criteria"), question_id)})
        elif question_type == "score":
            native.update({"type": "score", "levels": _score_levels(question.get("criteria"), question_id)})
        elif question_type == "noul":
            # OpenCode calls a probability-of-truth question a predicate.
            criteria = question.get("criteria")
            if criteria:
                instructions += f"\nClarification: {criteria}"
                native["instructions"] = instructions
            native["type"] = "predicate"
        else:
            raise ValueError(f"Question {question_id!r} needs type choice, score, or noul.")

        native_questions.append(native)

    return {
        "model": {"providerID": PROVIDER_ID, "id": model_id},
        "input": input_parts,
        "questions": native_questions,
    }


def _error_status(output: str) -> int | None:
    match = re.search(r"\bHTTP\s+(\d{3})\b", output, re.IGNORECASE)
    return int(match.group(1)) if match else None


def request_jev(payload: dict[str, Any], model_id: str, timeout: float) -> dict[str, Any]:
    executable = shutil.which("opencode")
    if not executable:
        raise RequestFailure("OpenCode CLI was not found on PATH", False)

    data = json.dumps(to_opencode_request(payload, model_id), ensure_ascii=False)
    try:
        result = subprocess.run(
            [executable, "api", "post", API_PATH, "--data", data],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RequestFailure("OpenCode decision request timed out", True) from None
    except OSError as error:
        raise RequestFailure(f"could not run OpenCode CLI ({type(error).__name__})", False) from None

    if result.returncode != 0:
        combined = f"{result.stdout}\n{result.stderr}"
        status = _error_status(combined)
        fallbackable = (
            status in FALLBACK_STATUSES
            or (status is not None and status >= 500)
            or status in {404}
            or any(word in combined.lower() for word in ("timeout", "timed out", "unavailable", "rate limit"))
        )
        safe_detail = f"HTTP {status}" if status is not None else "OpenCode API request failed"
        raise RequestFailure(safe_detail, fallbackable)

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RequestFailure("OpenCode returned invalid JSON", True) from None
    if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
        raise RequestFailure("OpenCode response did not contain a data object", True)
    answers = response["data"].get("answers")
    if not isinstance(answers, list):
        raise RequestFailure("OpenCode response did not contain an answers list", True)
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-paid-fallback",
        action="store_true",
        help="retry with paid Jev after a fallbackable Free request failure (requires user approval)",
    )
    parser.add_argument("--timeout", type=float, default=45.0, help="per-request timeout in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        payload = json.load(sys.stdin)
        # Validate/normalize before starting OpenCode or making a model request.
        to_opencode_request(payload, FREE_MODEL)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return 2

    if args.allow_paid_fallback:
        models = [FREE_MODEL, PAID_MODEL]
    else:
        models = [FREE_MODEL]
    for index, model_id in enumerate(models):
        try:
            response = request_jev(payload, model_id, args.timeout)
        except RequestFailure as error:
            can_fallback = index == 0 and len(models) > 1 and error.fallbackable
            if can_fallback:
                print(f"{model_id} unavailable ({error}); retrying once with {PAID_MODEL}.", file=sys.stderr)
                if "HTTP 404" in str(error) or "HTTP 410" in str(error):
                    print(
                        "This may indicate retirement; verify the official model list before changing the skill.",
                        file=sys.stderr,
                    )
                continue
            print(f"Jev request failed for {model_id}: {error}", file=sys.stderr)
            return 1

        print(f"Jev answered using opencode/{model_id}.", file=sys.stderr)
        json.dump(response, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
