# diff.py — Structural diff engine for YAML DSL dictionaries.

from typing import Any


def flatten_dict(
    data: Any,
    prefix: str = "",
) -> dict[str, Any]:
    """Recursively flatten a nested dict/list structure into dot-separated keys.

    Lists are kept as values (not expanded). Returns a flat dict.
    """
    flattened = {}

    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_dict(value, path))

    elif isinstance(data, list):
        flattened[prefix] = data

    else:
        flattened[prefix] = data

    return flattened


def structural_diff(
    old: dict,
    new: dict,
) -> list[dict]:
    """Compute the structural diff between two nested dicts.

    Returns a list of dicts with keys: path, operation ("add"/"delete"/"modify"), old, new.
    """
    old_flat = flatten_dict(old)
    new_flat = flatten_dict(new)

    all_keys = sorted(set(old_flat) | set(new_flat))
    changes = []

    for key in all_keys:
        old_value = old_flat.get(key, "__MISSING__")
        new_value = new_flat.get(key, "__MISSING__")

        if old_value == new_value:
            continue

        if old_value == "__MISSING__":
            operation = "add"
        elif new_value == "__MISSING__":
            operation = "delete"
        else:
            operation = "modify"

        changes.append(
            {
                "path": key,
                "operation": operation,
                "old": old_value,
                "new": new_value,
            }
        )

    return changes
