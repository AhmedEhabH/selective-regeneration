# deterministic_repair.py — Ruff-based repair for missing imports.

import re
from pathlib import Path

from selective_regeneration.validation import run_command


SAFE_MISSING_IMPORTS = {
    "date": "from datetime import date",
    "datetime": "from datetime import datetime",
    "timedelta": "from datetime import timedelta",
    "UUID": "from uuid import UUID",
    "uuid4": "from uuid import uuid4",
    "Path": "from pathlib import Path",
    "Any": "from typing import Any",
    "Optional": "from typing import Optional",
    "field": "from dataclasses import field",
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Tuple": "from typing import Tuple",
    "Set": "from typing import Set",
}


def add_import_to_python_file(
    file_path: Path,
    import_statement: str,
) -> bool:
    """Insert an import statement at the top of a Python file.

    The import is placed after any shebang, encoding declaration,
    or __future__ import. Returns True if the file was modified.
    """
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")

    if import_statement in content:
        return False

    lines = content.splitlines()

    insertion_index = 0

    while insertion_index < len(lines):
        line = lines[insertion_index].strip()

        if (
            line.startswith("#!")
            or "coding:" in line
            or line.startswith("from __future__ import")
        ):
            insertion_index += 1
            continue

        break

    lines.insert(insertion_index, import_statement)

    file_path.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

    return True


def extract_ruff_undefined_names(
    ruff_output: str,
) -> list[tuple[str, str]]:
    """Parse ruff F821 output to extract undefined names and their files.

    Returns a list of (name, relative_path) tuples, deduplicated.
    """
    pattern = re.compile(
        r"F821 Undefined name `([^`]+)`"
        r"[\s\S]*?"
        r"--> ([^:\n]+):\d+:\d+"
    )

    matches = pattern.findall(ruff_output)

    unique_matches = []
    seen = set()

    for undefined_name, relative_path in matches:
        key = (undefined_name, relative_path)

        if key not in seen:
            seen.add(key)
            unique_matches.append(key)

    return unique_matches


def run_deterministic_local_repair(
    project_dir: Path,
    test_timeout: int = 180,
) -> dict:
    """Run a full deterministic repair cycle on a project.

    Steps: ruff --fix -> extract undefined names -> add safe imports
    -> ruff --fix again. Returns a report dict with actions taken.
    """
    actions = []

    first_fix = run_command(
        ["ruff", "check", "app", "tests", "--fix"],
        cwd=project_dir,
        timeout=test_timeout,
    )

    inspection = run_command(
        ["ruff", "check", "app", "tests"],
        cwd=project_dir,
        timeout=test_timeout,
    )

    combined_output = (
        inspection.stdout + "\n" + inspection.stderr
    )

    undefined_names = extract_ruff_undefined_names(
        combined_output
    )

    for undefined_name, relative_path in undefined_names:
        import_statement = SAFE_MISSING_IMPORTS.get(
            undefined_name
        )

        if import_statement is None:
            continue

        target_file = project_dir / relative_path

        changed = add_import_to_python_file(
            target_file,
            import_statement,
        )

        if changed:
            actions.append(
                {
                    "type": "add_missing_import",
                    "file": relative_path,
                    "name": undefined_name,
                    "import": import_statement,
                }
            )

    final_fix = run_command(
        ["ruff", "check", "app", "tests", "--fix"],
        cwd=project_dir,
        timeout=test_timeout,
    )

    return {
        "actions": actions,
        "first_ruff_return_code": first_fix.return_code,
        "final_ruff_return_code": final_fix.return_code,
        "final_ruff_stdout": final_fix.stdout,
        "final_ruff_stderr": final_fix.stderr,
    }
