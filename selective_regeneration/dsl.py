# dsl.py — Read, write, and patch YAML-based DSL files.

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def read_yaml(path: Path) -> dict:
    """Parse a YAML file and return the content as a dict."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, data: dict) -> None:
    """Write a dict to a YAML file with sorted keys and unicode support."""
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            sort_keys=False,
            allow_unicode=True,
        )


def set_nested_value(
    data: dict,
    dotted_path: str,
    value: Any,
) -> None:
    """Set a value in a nested dict using a dot-separated path.

    Creates intermediate dicts as needed. Uses deepcopy for the value.
    """
    keys = dotted_path.split(".")
    current = data

    for key in keys[:-1]:
        current = current.setdefault(key, {})

    current[keys[-1]] = deepcopy(value)


def apply_dsl_patch(
    current_dsl: dict,
    patch: dict,
) -> dict:
    """Apply a patch dict (dotted-path -> value) to a DSL dict.

    Returns a new dict with all patches applied. Original is not modified.
    """
    updated = deepcopy(current_dsl)

    for path, value in patch.items():
        set_nested_value(updated, path, value)

    return updated
