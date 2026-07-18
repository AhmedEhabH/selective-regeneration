# output_parser.py — Parse and validate LLM JSON output.

import json
import re
from pathlib import Path

from jsonschema import validate as validate_json_schema

from selective_regeneration.change_model import RequirementChange
from selective_regeneration.context_builder import (
    GENERATION_SCHEMA,
)


def strip_markdown_fence(text: str) -> str:
    """Remove markdown code fences (```json ... ```) from model output."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

    return cleaned.strip()


def extract_json_object(text: str) -> dict:
    """Extract a JSON object from model output text.

    Tries direct parse first, then falls back to brace-matching
    to find the outermost { ... } block.
    """
    cleaned = strip_markdown_fence(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "No complete JSON object found in model output."
            )

        return json.loads(cleaned[start : end + 1])


def validate_payload_schema(payload: dict) -> None:
    """Validate a payload dict against the GENERATION_SCHEMA.

    Raises jsonschema.ValidationError if the payload does not match.
    """
    validate_json_schema(
        instance=payload,
        schema=GENERATION_SCHEMA,
    )


def validate_generated_scope(
    payload: dict,
    change: RequirementChange,
    affected_files: list[str],
) -> None:
    """Validate that the generated payload stays within allowed scope.

    Checks: no absolute paths, no path traversal, all paths in allowlist,
    no duplicate paths, correct change_id. Raises ValueError on violation.
    """
    allowed = set(affected_files)
    returned_paths = []

    for file_item in payload["files"]:
        relative_path = file_item["path"]

        if relative_path.startswith("/"):
            raise ValueError(
                f"Absolute path not allowed: {relative_path}"
            )

        if ".." in Path(relative_path).parts:
            raise ValueError(
                f"Path traversal not allowed: {relative_path}"
            )

        if relative_path not in allowed:
            raise ValueError(
                f"Model attempted to modify unapproved file: "
                f"{relative_path}"
            )

        returned_paths.append(relative_path)

    if len(returned_paths) != len(set(returned_paths)):
        raise ValueError("Duplicate file paths in output")

    if payload["change_id"] != change.change_id:
        raise ValueError("Incorrect change_id returned")
