# snapshots.py — Project snapshot creation and manifest comparison.

import hashlib
import shutil
from pathlib import Path


def hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_manifest(project_dir: Path) -> dict[str, str]:
    """Build a manifest mapping relative file paths to SHA-256 hashes."""
    manifest = {}

    for path in sorted(project_dir.rglob("*")):
        if path.is_file():
            relative = str(
                path.relative_to(project_dir)
            ).replace("\\", "/")
            manifest[relative] = hash_file(path)

    return manifest


def create_snapshot(
    project_dir: Path,
    snapshot_name: str,
    snapshots_dir: Path | None = None,
) -> Path:
    """Copy a project directory to a named snapshot location.

    Ignores __pycache__, .pytest_cache, .ruff_cache, and *.pyc files.
    Returns the path to the created snapshot.
    """
    if snapshots_dir is None:
        snapshots_dir = (
            project_dir.parent.parent / "snapshots"
        )

    snapshots_dir.mkdir(parents=True, exist_ok=True)

    destination = snapshots_dir / snapshot_name

    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(
        project_dir,
        destination,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "*.pyc",
        ),
    )

    return destination


def compare_manifests(
    before_dir: Path,
    after_dir: Path,
) -> dict:
    """Compare two directory manifests and return added/deleted/modified/unchanged lists."""
    before = build_manifest(before_dir)
    after = build_manifest(after_dir)

    all_paths = sorted(set(before) | set(after))

    added = []
    deleted = []
    modified = []
    unchanged = []

    for path in all_paths:
        if path not in before:
            added.append(path)
        elif path not in after:
            deleted.append(path)
        elif before[path] != after[path]:
            modified.append(path)
        else:
            unchanged.append(path)

    return {
        "added": added,
        "deleted": deleted,
        "modified": modified,
        "unchanged": unchanged,
    }
