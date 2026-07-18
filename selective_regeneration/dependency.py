# dependency.py — Resolve affected source files via prefix-matching rule graph.


def resolve_affected_files(
    changes: list[dict],
    rules: dict,
) -> list[str]:
    """Map DSL diff entries to affected source files using dependency rules.

    For each changed path in the diff, checks if any dependency rule
    prefix matches. Collects all rule artifacts into a sorted list.
    """
    affected = set()

    for change in changes:
        changed_path = change["path"]

        for dependency_prefix, rule in rules.items():
            if changed_path.startswith(dependency_prefix):
                affected.update(rule["artifacts"])

    return sorted(affected)
