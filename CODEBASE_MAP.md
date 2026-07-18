# Codebase Map

This document describes every Python file in the `selective_regeneration/` package, the notebook under `notebooks/`, and the test file, including purpose, classes, functions, inputs, outputs, and dependency relationships.

---

## Package: `selective_regeneration/`

### `__init__.py`

- **Purpose**: Package marker. Contains a docstring describing the package.
- **Imports**: None.
- **Imported by**: All modules in the package (implicit package resolution).

---

### `change_model.py`

- **Purpose**: Defines the data structure for a requirement change.
- **Classes**:
  - `RequirementChange` (frozen dataclass)
    - Fields: `change_id: str`, `version: str`, `title: str`, `requirement_delta: str`, `dsl_patch: dict`, `expected_change_types: list[str]`, `allowed_files: list[str]`, `hidden_test_files: dict[str, str]`
- **Functions**: None.
- **Inputs**: None (pure data definition).
- **Outputs**: Instances of `RequirementChange`.
- **Dependencies**: `dataclasses` (stdlib).
- **Imported by**: `context_builder.py`, `experiment_runner.py`, `output_parser.py`, notebook cells.

---

### `ch_003_definition.py`

- **Purpose**: Defines the CH-003 requirement change (overdue rule update).
- **Constants**:
  - `CHANGE_3`: A `RequirementChange` instance for changing the overdue rule to include tasks due on the current date.
- **Functions**: None.
- **Inputs**: None (pure data definition).
- **Outputs**: The `CHANGE_3` constant.
- **Dependencies**: `change_model.py` (for `RequirementChange`).
- **Imported by**: Notebook cells.

---

### `dsl.py`

- **Purpose**: Read, write, and patch YAML-based DSL files.
- **Functions**:
  - `read_yaml(path: Path) -> dict` — Parses YAML file.
  - `write_yaml(path: Path, data: dict) -> None` — Writes YAML file.
  - `set_nested_value(data: dict, dotted_path: str, value: Any) -> None` — Sets a value at a dot-separated path.
  - `apply_dsl_patch(current_dsl: dict, patch: dict) -> dict` — Returns a new dict with patches applied.
- **Inputs**: `Path` to YAML file, dicts.
- **Outputs**: Parsed/patched dicts.
- **Dependencies**: `pyyaml`, `copy` (stdlib).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `diff.py`

- **Purpose**: Compute structural diffs between two DSL versions.
- **Functions**:
  - `flatten_dict(data: Any, prefix: str = "") -> dict[str, Any]` — Recursively flattens nested dicts with dot-separated keys.
  - `structural_diff(old: dict, new: dict) -> list[dict]` — Returns list of `{path, operation, old, new}` where operation is `"add"`, `"delete"`, or `"modify"`.
- **Inputs**: Two dicts (old and new DSL).
- **Outputs**: List of change dicts.
- **Dependencies**: `typing` (stdlib).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `dependency.py`

- **Purpose**: Resolve which source files are affected by DSL changes using a prefix-matching rule graph.
- **Functions**:
  - `resolve_affected_files(changes: list[dict], rules: dict) -> list[str]` — Takes diff output and dependency rules, returns sorted list of affected file paths.
- **Inputs**: Diff list (from `structural_diff`), rules dict (from notebook).
- **Outputs**: Sorted list of relative file paths.
- **Dependencies**: None (pure Python).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `patching.py`

- **Purpose**: File system operations for reading, writing, and applying generated payloads.
- **Functions**:
  - `write_files(base_dir: Path, files: dict[str, str]) -> None` — Creates files from a path-to-content dict.
  - `read_selected_files(project_dir: Path, relative_paths: list[str]) -> dict[str, str]` — Reads specified files, returns empty string for missing files.
  - `apply_generated_payload(staging_dir: Path, payload: dict) -> list[str]` — Applies `"replace"`, `"create"`, or `"delete"` operations from LLM output.
- **Inputs**: Paths, file dicts, JSON payload.
- **Outputs**: Modified paths list.
- **Dependencies**: `pathlib` (stdlib).
- **Imported by**: `experiment_runner.py`, `context_builder.py`, notebook cells.

---

### `snapshots.py`

- **Purpose**: Create file-system snapshots of projects and compare them.
- **Functions**:
  - `hash_file(path: Path) -> str` — SHA-256 hex digest of a file.
  - `build_manifest(project_dir: Path) -> dict[str, str]` — Maps relative paths to SHA-256 hashes.
  - `create_snapshot(project_dir: Path, snapshot_name: str, snapshots_dir: Path | None) -> Path` — Copies project to snapshot directory.
  - `compare_manifests(before_dir: Path, after_dir: Path) -> dict` — Returns `{added, deleted, modified, unchanged}` lists.
- **Inputs**: Project directories, snapshot names.
- **Outputs**: Paths, manifests, diff dicts.
- **Dependencies**: `hashlib`, `shutil` (stdlib).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `validation.py`

- **Purpose**: Multi-stage validation of the project (syntax, linting, tests).
- **Classes**:
  - `CommandResult` (dataclass): `command`, `return_code`, `stdout`, `stderr`, `duration_seconds`, `timed_out`. Property `passed` returns `True` if return code is 0 and not timed out.
- **Functions**:
  - `run_command(command: list[str], cwd: Path, timeout: int) -> CommandResult` — Subprocess wrapper with timeout handling.
  - `validate_project(project_dir: Path, test_timeout: int) -> dict` — Runs 7 stages: `ast_parse`, `compile`, `ruff`, `unit`, `integration`, `regression`, `hidden`. Early-terminates on compile/unit/integration failure. Returns `all_passed` bool.
  - `stage_passed(validation: dict, stage: str) -> bool` — Checks if a specific stage passed.
- **Inputs**: Project directory, timeout.
- **Outputs**: Validation result dict with per-stage `CommandResult` dicts.
- **Dependencies**: `subprocess`, `sys`, `time`, `dataclasses` (stdlib).
- **Imported by**: `deterministic_repair.py`, `experiment_runner.py`, `metrics.py`, notebook cells.

---

### `deterministic_repair.py`

- **Purpose**: Fix common LLM generation errors (missing imports) using ruff output.
- **Functions**:
  - `add_import_to_python_file(file_path: Path, import_statement: str) -> bool` — Inserts an import at the top of a Python file (after shebang/encoding/future).
  - `extract_ruff_undefined_names(ruff_output: str) -> list[tuple[str, str]]` — Parses ruff F821 output for undefined names and their file locations.
  - `run_deterministic_local_repair(project_dir: Path, test_timeout: int) -> dict` — Full repair cycle: `ruff --fix` -> extract undefined names -> add safe imports -> `ruff --fix` again.
- **Constants**:
  - `SAFE_MISSING_IMPORTS`: Maps names to import statements for `date`, `datetime`, `timedelta`, `UUID`, `uuid4`, `Path`, `Any`, `Optional`, `field`, `List`, `Dict`, `Tuple`, `Set`.
- **Inputs**: Project directory, timeout.
- **Outputs**: Repair report dict with `actions` list and ruff return codes.
- **Dependencies**: `validation.py` (for `run_command`).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `output_parser.py`

- **Purpose**: Parse and validate LLM JSON output.
- **Functions**:
  - `strip_markdown_fence(text: str) -> str` — Removes ````json` wrappers.
  - `extract_json_object(text: str) -> dict` — Robust JSON extraction: try direct parse, then brace-matching fallback.
  - `validate_payload_schema(payload: dict) -> None` — Validates against `GENERATION_SCHEMA` using jsonschema.
  - `validate_generated_scope(payload: dict, change: RequirementChange, affected_files: list[str]) -> None` — Checks: no absolute paths, no path traversal, all paths in allowlist, no duplicates, correct `change_id`.
- **Inputs**: LLM text output, payload dict, change model, affected files list.
- **Outputs**: Parsed dict or raises `ValueError`.
- **Dependencies**: `json`, `re`, `jsonschema`, `change_model.py`, `context_builder.py`.
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `context_builder.py`

- **Purpose**: Construct prompts for the LLM, define system prompts and output schemas.
- **Constants**:
  - `GENERATION_SCHEMA`: JSON schema requiring `change_id` (string), `summary` (string), `files` (array of `{path, operation, content}`).
  - `SYSTEM_PROMPT`: 15-rule prompt for deterministic code transformation.
  - `REPAIR_SYSTEM_PROMPT`: 6-rule prompt for failed change repair.
- **Functions**:
  - `build_generation_prompt(change, old_dsl, new_dsl, dsl_diff, affected_files, file_contents) -> str` — Full generation prompt with change details, DSL diff, current files, and output schema.
  - `build_repair_prompt(change, staging_dir, affected_files, validation) -> str` — Repair prompt with validation failures and current generated files.
  - `summarize_validation_failures(validation, max_chars_per_stage) -> str` — Extracts failing stage output.
- **Inputs**: Change model, DSL dicts, diff list, file contents, validation results.
- **Outputs**: Prompt strings.
- **Dependencies**: `json`, `yaml`, `change_model.py`, `patching.py`.
- **Imported by**: `output_parser.py`, `experiment_runner.py`, notebook cells.

---

### `llm_runner.py`

- **Purpose**: Model loading (GPTQ/BNB), generation, and memory management.
- **Classes**:
  - `GenerationResult` (dataclass): `text`, `prompt_tokens`, `output_tokens`, `total_tokens`, `duration_seconds`, `peak_gpu_memory_mb`, `finish_reason`.
- **Constants**:
  - `_TOKENIZER_FILES`: Set of required tokenizer filenames (`tokenizer.json`, `tokenizer_config.json`, `tokenizer.model`).
- **Functions**:
  - `_bytes_to_gb(n: int) -> float` — Internal helper.
  - `_print_system_info() -> None` — Prints GPU name, VRAM, RAM.
  - `_has_tokenizer_files(model_dir) -> bool` — Checks if a model directory contains the necessary tokenizer files.
  - `_score_candidate(model_dir) -> tuple[int, list[str]]` — Scores a candidate model directory by GPTQ/Qwen keyword matches.
  - `find_kaggle_model(search_root: str) -> Path | None` — Recursively searches `/kaggle/input` for model directories with `config.json`, scored by GPTQ/Qwen keywords.
  - `debug_kaggle_models(search_root) -> None` — Prints debug information about discovered Kaggle model directories.
  - `_print_limited_tree(root, max_depth, current_depth) -> None` — Prints a limited directory tree view for debugging.
  - `_raise_model_not_found(model_path, search_root) -> None` — Raises a descriptive error when no model is found.
  - `detect_gptq_backend(model_dir: Path) -> str | None` — Reads `quantize_config.json` and `config.json` to detect quantization method. Returns backend name or None.
  - `load_model(model_path, model_source, quantization_backend, seed) -> tuple` — Main entry point. Prints system info, resolves path, loads model, calls `model.eval()`, prints memory stats.
  - `_load_gptq_model(model_dir, backend, seed) -> tuple` — Loads via gptqmodel, auto_gptq, or transformers.
  - `_load_bnb_model(model_dir, seed) -> tuple` — Loads with BitsAndBytesConfig NF4.
  - `_print_memory_stats() -> None` — Prints allocated/reserved GPU memory.
  - `check_context_fit(prompt_tokens, max_new_tokens, max_context_tokens, model_context_length) -> None` — Raises on overflow.
  - `generate_with_qwen(tokenizer, model, system_prompt, user_prompt, max_new_tokens, max_context_tokens) -> GenerationResult` — Single generation with context validation and memory tracking.
- **Inputs**: Model path, generation parameters.
- **Outputs**: Tokenizer + model (from `load_model`), `GenerationResult` (from `generate_with_qwen`).
- **Dependencies**: `torch`, `transformers` (`AutoModelForCausalLM`, `AutoTokenizer`, `set_seed`, `BitsAndBytesConfig`), `json`, `gc`, `time`, `pathlib`. Optional: `gptqmodel`, `auto_gptq`, `psutil`.
- **Imported by**: `experiment_runner.py`, `tests/test_model_discovery.py`, notebook cells.

---

### `metrics.py`

- **Purpose**: Build, store, and load experiment metrics.
- **Functions**:
  - `build_change_metrics(...) -> dict` — Constructs the full metrics record from change metadata, generation results, validation results, timing, and file diffs. Accepts `quantization` parameter.
  - `_classify_failure(first_pass, local_repair_used, accepted_after_local, llm_repair_used, final_passed) -> str` — Returns one of 7 failure category strings.
  - `append_metrics_jsonl(metrics_path, metrics_record) -> None` — Appends a JSON line.
  - `load_metrics_jsonl(metrics_path) -> list[dict]` — Reads all JSON lines.
- **Inputs**: Change model, generation results, validation results, timing, file diffs.
- **Outputs**: Metrics dict, JSONL files.
- **Dependencies**: `json`, `datetime`, `validation.py` (for `stage_passed`).
- **Imported by**: `experiment_runner.py`, notebook cells.

---

### `experiment_runner.py`

- **Purpose**: Orchestrates the complete selective regeneration pipeline for a single change.
- **Functions**:
  - `run_selective_change(*, project_dir, change, dependency_rules, tokenizer, model, config, results_path, snapshots_dir) -> dict` — Full pipeline: DSL patch -> diff -> affected files -> LLM generate -> parse -> validate -> deterministic repair -> optional LLM repair -> snapshot -> commit -> metrics.
- **Inputs**: Project directory, change model, dependency rules, tokenizer, model, config, output paths.
- **Outputs**: Result dict with `change_id`, `version`, `passed`, `first_pass_acceptance`, `local_repair_used`, `accepted_after_local_repair`, `llm_repair_used`, `affected_files`, `dsl_diff`, `metrics`, `first_validation`, `final_validation`, `snapshot`.
- **Dependencies**: All other modules in the package.
- **Imported by**: Notebook cells only.

---

## Tests: `tests/`

### `test_model_discovery.py`

- **Purpose**: Unit tests for model discovery logic in `llm_runner.py`.
- **Functions**:
  - Tests for `_has_tokenizer_files`, `_score_candidate`, `find_kaggle_model`.
- **Inputs**: Uses temporary directories with mock model files.
- **Outputs**: Test pass/fail (pytest).
- **Dependencies**: `llm_runner.py`, `pytest`, `pathlib` (stdlib).
- **Imported by**: None (test runner).

---

## Notebook: `notebooks/qwen-selective-regeneration-v2.ipynb`

49 cells (markdown + code). The notebook is the experiment driver. It:

1. Checks hardware (Cell 1).
2. Installs packages (Cell 2-3).
3. Sets up directories and module path (Cell 4).
4. Defines `ExperimentConfig` (Cell 5).
5. Imports all modules (Cell 6).
6. Creates initial ToDo API project (Cell 7).
7. Validates initial project (Cell 8).
8. Saves initial snapshot (Cell 9).
9. Discovers and loads model (Cell 10).
10. Runs smoke test (Cell 11).
11. Defines dependency rules (Cell 12).
12. Defines and runs 3 changes (Cells 13-21).
13. Shows summary and metrics (Cells 22-24).

---

## Dependency Graph

```
experiment_runner.py
├── change_model.py
├── context_builder.py
│   ├── change_model.py
│   └── patching.py
├── dependency.py
├── deterministic_repair.py
│   └── validation.py
├── diff.py
├── dsl.py
├── llm_runner.py
├── metrics.py
│   └── validation.py
├── output_parser.py
│   ├── change_model.py
│   └── context_builder.py
├── patching.py
├── snapshots.py
└── validation.py

llm_runner.py
├── torch
└── transformers

tests/test_model_discovery.py
└── llm_runner.py

metrics.py
└── validation.py

validation.py
└── subprocess, sys (stdlib)

patching.py
└── pathlib (stdlib)

snapshots.py
└── hashlib, shutil (stdlib)

dsl.py
└── yaml

diff.py
└── typing (stdlib)

dependency.py
└── (none)

change_model.py
└── dataclasses (stdlib)

ch_003_definition.py
└── change_model.py
```

**Leaf modules** (no internal dependencies): `change_model.py`, `dependency.py`, `diff.py`, `patching.py`, `snapshots.py`.

**Hub module** (depends on most others): `experiment_runner.py` (imports 10 of 12 modules).
