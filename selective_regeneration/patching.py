# patching.py — File system operations for reading, writing, and applying payloads.

from pathlib import Path


def write_files(
    base_dir: Path,
    files: dict[str, str],
) -> None:
    """Write files from a path-to-content dict, creating parent directories as needed."""
    for relative_path, content in files.items():
        destination = base_dir / relative_path
        destination.parent.mkdir(
            parents=True, exist_ok=True
        )
        destination.write_text(
            content, encoding="utf-8"
        )


def read_selected_files(
    project_dir: Path,
    relative_paths: list[str],
) -> dict[str, str]:
    """Read specified files from a project directory.

    Returns a dict mapping relative paths to file contents.
    Missing files are mapped to empty strings.
    """
    result = {}

    for relative_path in relative_paths:
        path = project_dir / relative_path

        if not path.exists():
            result[relative_path] = ""
        else:
            result[relative_path] = path.read_text(
                encoding="utf-8"
            )

    return result


def apply_generated_payload(
    staging_dir: Path,
    payload: dict,
) -> list[str]:
    """Apply LLM-generated file operations to a staging directory.

    Supports "replace", "create", and "delete" operations.
    Returns the list of modified relative paths.
    """
    modified_paths = []

    for file_item in payload["files"]:
        relative_path = file_item["path"]
        operation = file_item["operation"]
        content = file_item["content"]

        destination = staging_dir / relative_path

        if operation in {"replace", "create"}:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_text(
                content.rstrip() + "\n",
                encoding="utf-8",
            )

        elif operation == "delete":
            if destination.exists():
                destination.unlink()

        else:
            raise ValueError(
                f"Unsupported operation: {operation}"
            )

        modified_paths.append(relative_path)

    return modified_paths
