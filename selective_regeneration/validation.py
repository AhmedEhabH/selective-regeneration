# validation.py — Multi-stage project validation (syntax, lint, tests).

from dataclasses import dataclass, asdict
import subprocess
import sys
import time
from pathlib import Path


@dataclass
class CommandResult:
    """Result of a subprocess command execution.

    Attributes:
        command: The command string that was executed.
        return_code: Process exit code (0 = success).
        stdout: Captured standard output.
        stderr: Captured standard error.
        duration_seconds: Wall-clock execution time.
        timed_out: Whether the command exceeded the timeout.
    """
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.return_code == 0 and not self.timed_out


def run_command(
    command: list[str],
    cwd: Path,
    timeout: int = 180,
) -> CommandResult:
    """Execute a subprocess command with timeout handling.

    Returns a CommandResult with stdout, stderr, return code, and timing.
    """
    started = time.perf_counter()

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

        return CommandResult(
            command=" ".join(command),
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.perf_counter() - started,
        )

    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=" ".join(command),
            return_code=-1,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            duration_seconds=time.perf_counter() - started,
            timed_out=True,
        )


def validate_project(
    project_dir: Path,
    test_timeout: int = 180,
) -> dict:
    """Run the full multi-stage validation pipeline on a project.

    Stages: ast_parse, compile, ruff, unit, integration, regression, hidden.
    Early-terminates on compile, unit, or integration failure.
    Returns a dict with per-stage results and an all_passed flag.
    """
    ast_script = (
        "import ast, sys, pathlib\n"
        "errors = []\n"
        "for p in sorted(pathlib.Path('.').glob('**/*.py')):\n"
        "    if '__pycache__' in str(p):\n"
        "        continue\n"
        "    try:\n"
        "        ast.parse(p.read_text())\n"
        "    except SyntaxError as e:\n"
        "        errors.append(f'{p}: {e}')\n"
        "if errors:\n"
        "    print('\\n'.join(errors))\n"
        "    sys.exit(1)\n"
    )

    commands = {
        "ast_parse": [
            sys.executable,
            "-c",
            ast_script,
        ],
        "compile": [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "app",
            "tests",
            "hidden_tests",
        ],
        "ruff": [
            "ruff",
            "check",
            "app",
            "tests",
        ],
        "unit": [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit",
            "-q",
        ],
        "integration": [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration",
            "-q",
        ],
        "regression": [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
        ],
        "hidden": [
            sys.executable,
            "-m",
            "pytest",
            "hidden_tests",
            "-q",
        ],
    }

    results = {}

    for name, command in commands.items():
        result = run_command(
            command,
            cwd=project_dir,
            timeout=test_timeout,
        )
        results[name] = asdict(result)

        if not result.passed and name in {
            "compile",
            "unit",
            "integration",
        }:
            break

    results["all_passed"] = all(
        item.get("return_code") == 0
        for key, item in results.items()
        if key != "all_passed"
    )

    return results


def stage_passed(
    validation: dict,
    stage: str,
) -> bool:
    """Check whether a specific validation stage passed."""
    result = validation.get(stage)

    return bool(
        result and result.get("return_code") == 0
    )
