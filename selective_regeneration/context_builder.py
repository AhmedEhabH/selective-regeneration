# context_builder.py — LLM prompt construction and system prompt definitions.

import json
from pathlib import Path

import yaml

from selective_regeneration.change_model import RequirementChange
from selective_regeneration.patching import read_selected_files


GENERATION_SCHEMA = {
    "type": "object",
    "required": [
        "change_id",
        "summary",
        "files",
    ],
    "properties": {
        "change_id": {
            "type": "string",
        },
        "summary": {
            "type": "string",
        },
        "files": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "path",
                    "operation",
                    "content",
                ],
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "operation": {
                        "enum": [
                            "replace",
                            "create",
                            "delete",
                        ],
                    },
                    "content": {
                        "type": "string",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

SYSTEM_PROMPT = """
You are a deterministic software evolution engine.

Your task is to update only the explicitly allowed files for one
requirement change.

Rules:
1. Return only one valid JSON object.
2. Do not use Markdown fences.
3. Do not include explanations outside JSON.
4. Preserve all existing behavior not changed by the requirement.
5. Update production code and visible tests together.
6. Do not modify hidden tests.
7. Do not modify files outside the allowlist.
8. Each returned file must contain its complete final content.
9. The code must be valid Python 3.11.
10. The project uses FastAPI, Pydantic v2, and pytest.
11. Every referenced class, type, function, and constant must be
    defined or explicitly imported in the same file.
12. Never import a symbol that does not exist in the provided files.
13. Before returning JSON, mentally check every generated Python
    file for missing imports and undefined names.
14. Preserve all unrelated functions, routes, tests, and imports.
15. Do not create additional request models unless the requirement
    explicitly requires them.
""".strip()

REPAIR_SYSTEM_PROMPT = """
You are repairing one failed software evolution change.

Return only valid JSON matching the requested schema.
Modify only the allowed files.
Do not weaken or delete tests to make them pass.
Preserve all unaffected behavior.
Use the validation failure to correct production code or genuinely
incorrect visible tests.
Each returned file must contain its complete final content.
""".strip()


def build_generation_prompt(
    change: RequirementChange,
    old_dsl: dict,
    new_dsl: dict,
    dsl_diff: list[dict],
    affected_files: list[str],
    file_contents: dict[str, str],
) -> str:
    """Build the full prompt for initial code generation.

    Assembles change metadata, DSL diff, current file contents,
    and the output schema into a single prompt string.
    """
    file_sections = []

    for path in affected_files:
        content = file_contents.get(path, "")
        file_sections.append(
            f"FILE: {path}\n"
            f"----- BEGIN CURRENT CONTENT -----\n"
            f"{content}\n"
            f"----- END CURRENT CONTENT -----"
        )

    schema_text = json.dumps(
        GENERATION_SCHEMA,
        indent=2,
    )

    return f"""
CHANGE ID:
{change.change_id}

CHANGE TITLE:
{change.title}

REQUIREMENT DELTA:
{change.requirement_delta}

EXPECTED CHANGE TYPES:
{json.dumps(change.expected_change_types)}

DSL STRUCTURAL DIFF:
{json.dumps(dsl_diff, indent=2, default=str)}

NEW RELEVANT DSL:
{yaml.safe_dump(new_dsl, sort_keys=False)}

ALLOWED FILES:
{json.dumps(affected_files, indent=2)}

CURRENT AFFECTED FILES:
{chr(10).join(file_sections)}

REQUIRED OUTPUT JSON SCHEMA:
{schema_text}

Generate the complete final contents only for files that must change.
Preserve unrelated functions, imports, APIs, and tests.
""".strip()


def build_repair_prompt(
    change: RequirementChange,
    staging_dir: Path,
    affected_files: list[str],
    validation: dict,
) -> str:
    """Build the prompt for LLM repair of a failed change.

    Includes validation failures and the current state of generated
    files so the LLM can correct specific issues.
    """
    current_contents = read_selected_files(
        staging_dir,
        affected_files,
    )

    file_sections = []

    for path, content in current_contents.items():
        file_sections.append(
            f"FILE: {path}\n"
            f"----- BEGIN -----\n"
            f"{content}\n"
            f"----- END -----"
        )

    return f"""
CHANGE ID:
{change.change_id}

REQUIREMENT:
{change.requirement_delta}

VALIDATION FAILURE:
{summarize_validation_failures(validation)}

ALLOWED FILES:
{json.dumps(affected_files, indent=2)}

CURRENT GENERATED FILES:
{chr(10).join(file_sections)}

OUTPUT SCHEMA:
{json.dumps(GENERATION_SCHEMA, indent=2)}

Return only the corrected files.
Do not modify hidden tests.
""".strip()


def summarize_validation_failures(
    validation: dict,
    max_chars_per_stage: int = 3500,
) -> str:
    """Extract failing stage outputs from validation results.

    Returns a concatenated string of stdout/stderr from each failing
    stage, truncated to max_chars_per_stage characters each.
    """
    sections = []

    for stage, result in validation.items():
        if stage == "all_passed":
            continue

        if result["return_code"] == 0:
            continue

        combined = (
            result.get("stdout", "")
            + "\n"
            + result.get("stderr", "")
        )

        sections.append(
            f"STAGE: {stage}\n"
            f"{combined[-max_chars_per_stage:]}"
        )

    return "\n\n".join(sections)
