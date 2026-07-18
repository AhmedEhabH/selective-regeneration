# System State

This document describes the current implementation state of the Selective Regeneration Pipeline. It is written for AI agents and developers who need to continue development without reading the entire codebase.

## Overall Architecture

The system is a Jupyter notebook that orchestrates a Python package (`selective_regeneration/`) to:

1. Define requirement changes as structured deltas against a YAML DSL.
2. Compute which source files are affected via a dependency rule graph.
3. Send the affected context to Qwen2.5-Coder and receive JSON file operations.
4. Apply the operations to a staging copy of the project.
5. Validate the result through a multi-stage pipeline.
6. Attempt repair if validation fails.
7. Commit on success and record metrics.

## Repository Structure

```
project-root/
├── selective_regeneration/     # Python package
│   ├── __init__.py
│   ├── llm_runner.py           # Model loading, discovery, generation
│   ├── experiment_runner.py    # Full change pipeline orchestration
│   ├── context_builder.py      # System prompts, prompt construction
│   ├── output_parser.py        # JSON extraction, schema validation
│   ├── change_model.py         # RequirementChange dataclass
│   ├── dsl.py                  # YAML DSL read/write/patch
│   ├── diff.py                 # Structural diff engine
│   ├── dependency.py           # Dependency rule resolution
│   ├── patching.py             # File read/write/payload application
│   ├── snapshots.py            # Project snapshots, manifest comparison
│   ├── validation.py           # Multi-stage project validation
│   ├── deterministic_repair.py # Ruff-based missing import repair
│   ├── metrics.py              # Metrics collection and JSONL logging
│   └── ch_003_definition.py    # CH-003 requirement change definition
├── notebooks/
│   └── qwen-selective-regeneration-v2.ipynb
├── tests/
│   └── test_model_discovery.py
├── config/
│   └── experiment_config.json
├── MANIFEST.json
├── requirements-kaggle.txt
└── documentation files (README.md, etc.)
```

## Current Implementation Status

### Completed

- Full selective regeneration pipeline (dependency analysis, LLM generation, validation, repair).
- Model loading from Kaggle with GPTQ INT4 (primary) and BNB NF4 (fallback).
- Auto-discovery of model under `/kaggle/input/` with recursive search and keyword scoring.
- Tokenizer file validation for model candidates.
- GGUF directory rejection.
- Priority scoring: Qwen2.5-Coder GPTQ INT4 > other Qwen GPTQ > plain Transformers.
- `debug_kaggle_models()` diagnostics helper.
- Detailed error messages with paths searched, candidates found, rejection reasons.
- GPTQ backend auto-detection via `quantize_config.json` and `config.json`.
- Context length validation against both `max_context_tokens` and `model.config.max_position_embeddings`.
- GPU and RAM reporting before model loading.
- Deterministic repair for missing imports (ruff-based, fixed lookup table).
- Multi-stage validation: AST parse, compile, ruff, unit, integration, regression, hidden tests.
- Metrics collection with JSONL logging (token counts, timing, memory, outcome flags).
- Pilot experiment: ToDo API with 3 progressive requirement changes.
- Reproducibility via `seed=42` and greedy decoding.
- Unit tests for model discovery (19 tests, no GPU required).
- Lazy torch/transformers imports for testability.

### Remaining TODOs

- Automatic dependency extraction from Python imports (currently manual rules).
- Multi-project benchmarks (BFCL, HumanEval).
- Comparative experiment arms (monolithic, agent, compiled-AI, delta-MCP, incremental RTL, code-plan).
- Streaming generation support.
- Multi-repair attempt strategies.
- Larger model testing (32B, DeepSeek-Coder).
- Functional correctness metrics and mutation testing.
- CI/CD integration.
- Test coverage for non-discovery modules.

## Model Loading Strategy

The loading sequence in `llm_runner.py:load_model()`:

1. Print system info (GPU name, VRAM, RAM via psutil).
2. Resolve model path:
   - If `model_path` is provided and exists with `config.json`, use it.
   - Otherwise, if `model_source == "kaggle"`, call `find_kaggle_model()` to search `/kaggle/input/`.
3. `find_kaggle_model()`:
   - Recursively searches all paths under `/kaggle/input` for `config.json` files.
   - Scores each candidate by full path string matching against keywords.
   - Rejects GGUF directories and candidates without tokenizer files.
   - Returns the highest-scoring valid candidate.
4. Detect GPTQ backend via `detect_gptq_backend()`:
   - Check `quantize_config.json` for `quant_method` in `("gptq", "marlin")`.
   - If found, try loading with `gptqmodel` > `auto_gptq` > `transformers`.
   - Also check `config.json` under `quantization_config.quant_method` as fallback.
5. If GPTQ detected: call `_load_gptq_model()` (no `BitsAndBytesConfig` involved).
6. If no GPTQ detected: call `_load_bnb_model()` with NF4 + double quant + float16 compute.
7. Call `model.eval()`, print memory stats, attach metadata attributes to model.

**Key invariant**: GPTQ models never touch `BitsAndBytesConfig`. BNB fallback only activates when `detect_gptq_backend()` returns `None`.

## Important Design Decisions

1. **Kaggle-first model loading**: Models are loaded from `/kaggle/input/` (local), never downloaded from Hugging Face Hub. This avoids network dependency and HF token requirements.

2. **GPTQ preferred over BNB**: GPTQ INT4 is already quantized on disk, so it loads faster and uses less VRAM than BNB NF4 which quantizes at load time.

3. **`quantization_backend` config field is a hint, not a directive**: The function auto-detects regardless. If `quantization_backend="gptq"` is set but the model lacks GPTQ config, BNB fallback activates automatically.

4. **Complete file generation**: The LLM generates complete file contents for each affected file, not line-level diffs. This is simpler to validate and less error-prone than diff generation.

5. **Staging directory pattern**: Changes are applied to a staging copy, validated there, and only committed to the working project on full pass. This prevents partial corruption.

6. **Deterministic repair before LLM repair**: Missing imports are fixed by a deterministic ruff-based repair (cheap, fast) before falling back to an LLM repair call (expensive, slow).

7. **Context length gate**: `check_context_fit()` raises `ValueError` if prompt tokens exceed `max_context_tokens` or if `prompt + new` exceeds `model.config.max_position_embeddings`. This prevents OOM from oversized prompts.

8. **Lazy imports**: `torch` and `transformers` are imported inside functions, not at module level. This allows model discovery functions to be tested without GPU dependencies.

## Current Experiment Pipeline

The pilot experiment runs 3 changes on a ToDo API:

| Change | Description | DSL Impact |
|--------|-------------|------------|
| CH-001 | Add due date + overdue listing | Add field, change signature, add endpoint, add business rule |
| CH-002 | Add task tags + filter by tag | Add field, change signature, add query filter, add business rule |
| CH-003 | Overdue includes current date | Modify business rule |

Each change: `compute diff -> resolve files -> LLM generate -> validate -> deterministic repair -> optional LLM repair -> commit/snapshot -> metrics`.

## Important Classes and Functions

### `llm_runner.py`

- `GenerationResult` (dataclass): `text`, `prompt_tokens`, `output_tokens`, `total_tokens`, `duration_seconds`, `peak_gpu_memory_mb`, `finish_reason`.
- `load_model(model_path, model_source, quantization_backend, seed) -> (tokenizer, model)`: Main entry point. Attaches `_used_quantization`, `_model_source`, `_resolved_path` to model.
- `generate_with_qwen(tokenizer, model, system_prompt, user_prompt, max_new_tokens, max_context_tokens) -> GenerationResult`: Single generation call with context validation.
- `find_kaggle_model(search_root) -> Path | None`: Searches `/kaggle/input` recursively, scores by path keywords, validates tokenizer files, rejects GGUF.
- `debug_kaggle_models(search_root) -> None`: Prints detailed diagnostics of model discovery.
- `detect_gptq_backend(model_dir) -> str | None`: Returns `"gptqmodel"`, `"auto_gptq"`, `"transformers_gptq"`, `"transformers_marlin"`, or `None`.
- `check_context_fit(prompt_tokens, max_new_tokens, max_context_tokens, model_context_length)`: Raises on overflow.
- `_raise_model_not_found(model_path, search_root)`: Raises detailed `FileNotFoundError` with diagnostics.

### `experiment_runner.py`

- `run_selective_change(project_dir, change, dependency_rules, tokenizer, model, config, ...) -> dict`: Orchestrates the full pipeline for one change.

### `context_builder.py`

- `SYSTEM_PROMPT`, `REPAIR_SYSTEM_PROMPT`: Fixed prompts for generation and repair.
- `GENERATION_SCHEMA`: JSON schema the LLM output must match.
- `build_generation_prompt(change, old_dsl, new_dsl, dsl_diff, affected_files, file_contents) -> str`
- `build_repair_prompt(change, staging_dir, affected_files, validation) -> str`

### `output_parser.py`

- `strip_markdown_fence(text) -> str`: Removes ```json fences.
- `extract_json_object(text) -> dict`: Robust JSON extraction with brace-matching fallback.
- `validate_payload_schema(payload)`: Validates against `GENERATION_SCHEMA`.
- `validate_generated_scope(payload, change, affected_files)`: Ensures all paths are in allowlist, no traversal, no duplicates.

### `dsl.py`

- `read_yaml(path) -> dict`, `write_yaml(path, data)`.
- `apply_dsl_patch(current_dsl, patch) -> dict`: Applies dotted-path patches via `set_nested_value`.

### `diff.py`

- `flatten_dict(data, prefix) -> dict[str, Any]`: Recursive flatten with dot-separated keys.
- `structural_diff(old, new) -> list[dict]`: Returns list of `{path, operation, old, new}` dicts.

### `dependency.py`

- `resolve_affected_files(changes, rules) -> list[str]`: Maps DSL changes to source files via prefix-matching rules.

### `patching.py`

- `write_files(base_dir, files)`, `read_selected_files(project_dir, paths)`.
- `apply_generated_payload(staging_dir, payload) -> list[str]`: Writes/deletes files per JSON payload.

### `snapshots.py`

- `hash_file(path) -> str` (SHA-256), `build_manifest(project_dir) -> dict`.
- `create_snapshot(project_dir, name, snapshots_dir) -> Path`.
- `compare_manifests(before, after) -> dict` with `added`, `deleted`, `modified`, `unchanged`.

### `validation.py`

- `run_command(command, cwd, timeout) -> CommandResult`: Subprocess wrapper with timeout.
- `validate_project(project_dir, test_timeout) -> dict`: Runs 7 stages with early termination.
- `stage_passed(validation, stage) -> bool`.

### `deterministic_repair.py`

- `SAFE_MISSING_IMPORTS`: Dict mapping names to import statements.
- `run_deterministic_local_repair(project_dir, test_timeout) -> dict`: Runs `ruff --fix`, extracts F821 undefined names, adds safe imports, runs `ruff --fix` again.

### `metrics.py`

- `build_change_metrics(...) -> dict`: Builds the full metrics record. Accepts `quantization` parameter.
- `append_metrics_jsonl(path, record)`, `load_metrics_jsonl(path) -> list[dict]`.
- `_classify_failure(...)`: Returns one of 7 failure category strings.

### `change_model.py`

- `RequirementChange` (frozen dataclass): `change_id`, `version`, `title`, `requirement_delta`, `dsl_patch`, `expected_change_types`, `allowed_files`, `hidden_test_files`.

## Where Future Changes Should Be Made

| Area | File to modify |
|------|---------------|
| Add a new experiment arm | Create new notebook, reuse `experiment_runner.run_selective_change()` |
| Change model loading | `llm_runner.py` (load functions) |
| Change model discovery | `llm_runner.py` (`find_kaggle_model`, `_score_candidate`) |
| Add new validation stages | `validation.py:validate_project()` |
| Add new repair strategies | `deterministic_repair.py` or create new repair module |
| Change prompt engineering | `context_builder.py` |
| Modify output parsing | `output_parser.py` |
| Add new metrics | `metrics.py:build_change_metrics()` |
| Change DSL schema | `dsl.py` and `context_builder.py:GENERATION_SCHEMA` |
| Add new requirement changes | Notebook cells (define `RequirementChange` instances) |
| Change dependency rules | Notebook cell 12 (dict definition) |

## Things That Should NOT Be Changed

- `GenerationResult` dataclass fields (consumed by `metrics.py` and notebook display).
- `RequirementChange` dataclass fields (used everywhere).
- `GENERATION_SCHEMA` structure (validated against by `output_parser.py`).
- `validate_project()` stage names (`"ast_parse"`, `"compile"`, `"ruff"`, `"unit"`, `"integration"`, `"regression"`, `"hidden"`, `"all_passed"`) - these are used by `metrics.py` for stage-level pass/fail.
- `run_selective_change()` return dict keys - consumed by notebook display cells.
- Snapshot naming convention (`{version}_{change_id}` for pass, `failed_{version}_{change_id}` for fail).
- `selective_regeneration/` as the package name (used in `sys.path.insert` and all imports).

## Assumptions

1. The project being modified is a Python 3.11+ project using FastAPI, Pydantic v2, and pytest.
2. The project has `app/`, `tests/`, `tests/unit/`, `tests/integration/`, and `hidden_tests/` directories.
3. The project has a `dsl.yaml` at the root.
4. GPU is available on the Kaggle runtime (T4 or P100).
5. The Qwen2.5-Coder 7B model fits in 16GB VRAM with GPTQ INT4 quantization (~4-5 GB).
6. The model's context length is 32768 tokens (Qwen2.5-Coder default).
7. The DSL structure uses dot-separated paths (e.g., `"entities.Task.fields"`) for dependency rule matching.
8. All hidden tests are pre-defined per change and written to the project before validation.
9. The LLM generates complete file contents, not partial diffs.
10. Only one change is applied at a time (sequential, not concurrent).
