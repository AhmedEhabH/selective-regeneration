# Changelog

All notable changes to the Selective Regeneration Pipeline are documented here.

---

## [2.2.0] - 2026-07-18

### Release Candidate Preparation

- **Added**: Module-level header comments to all 15 package modules and test file.
- **Added**: Docstrings to all 22 public functions and 3 public classes.
- **Added**: `PROJECT_SUMMARY.md` executive overview for new developers.
- **Added**: `RELEASE_CHECKLIST.md` pre-release verification checklist.
- **Removed**: `archive/__init__.py.bak` obsolete backup file.
- **Removed**: `__pycache__` and `.pytest_cache` build artifacts from repository.

### Documentation Fixes

- **Fixed**: `ARCHITECTURE.md` repository tree now lists all 15 package modules, tests/, config/, and all 9 documentation files.
- **Fixed**: `ARCHITECTURE.md` scoring table replaced with actual path-keyword matching implementation (12 criteria).
- **Fixed**: `README.md` repository tree removed non-existent `runtime/`, `results/`, `snapshots/` directories.
- **Fixed**: `TODO.md` marked items #35 (Kaggle deployment guide) and #37 (v1.0 notebook archive) as Done.
- **Fixed**: `CODEBASE_MAP.md` added `ch_003_definition.py` module documentation and dependency graph entry.
- **Fixed**: `CODEBASE_MAP.md` corrected test coverage claims to match actual test file contents.
- **Fixed**: `README-KAGGLE.md` expanded scoring criteria to include all 12 keyword matches.
- **Fixed**: `PROJECT_SUMMARY.md` corrected documentation file count from 8 to 9.

### Package Quality

- **Removed**: `print(CHANGE_3.change_id, CHANGE_3.title)` side-effect from `ch_003_definition.py` import.

### Git Integration

- **Added**: `.gitignore` with comprehensive Python, Jupyter, IDE, OS, and Kaggle artifact rules.
- **Added**: `CONTRIBUTING.md` with coding style, commit convention, branching strategy, and testing expectations.
- **Added**: `VERSIONING.md` with semantic versioning policy and research milestone mapping.
- **Added**: `RELEASE_NOTES_v2.2.0.md` with full release documentation.

---

## [2.1.0] - 2026-07-18

### Repository Restructuring

- **Changed**: Moved all Python modules into `selective_regeneration/` package directory.
- **Changed**: Moved notebooks into `notebooks/` directory.
- **Changed**: Moved archived notebooks into `notebooks/archive/`.
- **Changed**: Created `tests/` directory with model discovery unit tests.
- **Changed**: Created `config/` directory with `experiment_config.json`.
- **Added**: `MANIFEST.json` for repository structure documentation.
- **Added**: `requirements-kaggle.txt` for dependency listing.
- **Added**: `README-KAGGLE.md` with Kaggle deployment guide.
- **Added**: `TODO.md` with 45 development tasks across 14 sections.

### Model Discovery Fixes

- **Fixed**: `find_kaggle_model()` now searches recursively under all `/kaggle/input` paths.
- **Fixed**: Keyword matching now checks the full path string, not just individual directory components.
- **Fixed**: Numeric version directories (e.g., `1`) are no longer the sole match criterion.
- **Added**: Tokenizer file validation (`tokenizer.json`, `tokenizer_config.json`, `tokenizer.model`).
- **Added**: GGUF directory rejection.
- **Added**: Priority scoring: Qwen2.5-Coder GPTQ INT4 > other Qwen GPTQ > plain Transformers.
- **Added**: `debug_kaggle_models()` diagnostics helper function.
- **Added**: Detailed error messages in `load_model()` with paths searched, candidates found, rejection reasons, and Kaggle attach instructions.

### Testing

- **Added**: `tests/test_model_discovery.py` with 19 unit tests.
- **Added**: Tests for tokenizer file detection, candidate scoring, GGUF rejection, missing tokenizer rejection, multiple candidate priority, empty directories, and exact target path discovery.
- **Added**: Tests run without GPU (torch/transformers imports are lazy).

### Code Quality

- **Changed**: `torch` and `transformers` imports are now lazy (inside functions) to allow testing without GPU.
- **Changed**: Notebook Cell 4 updated for new directory structure and sys.path setup.
- **Changed**: Notebook Cell 10 now calls `debug_kaggle_models()` before `load_model()`.
- **Changed**: Notebook Cell 6 imports `debug_kaggle_models` from `llm_runner`.

---

## [2.0.0] - 2026-07-18

### Migration from Hugging Face to Kaggle Model Loading

- **Removed**: Hugging Face Hub download of `Qwen/Qwen2.5-Coder-7B-Instruct`.
- **Added**: `find_kaggle_model()` that recursively searches `/kaggle/input/` for model directories with `config.json`, scoring by GPTQ/Qwen keywords.
- **Added**: Auto-detection of model path via keyword scoring (GPTQ/int4 variants scored +10, Qwen/coder variants scored +1).
- **Added**: `model_source`, `model_path`, `quantization_backend` fields to `ExperimentConfig`.
- **Removed**: `load_in_4bit`, `quant_type`, `double_quant`, `compute_dtype` from `ExperimentConfig`.
- **Removed**: `model_revision` from `ExperimentConfig`.

### GPTQ Integration

- **Added**: `detect_gptq_backend()` that reads `quantize_config.json` and `config.json` to detect quantization method (`gptq`, `marlin`).
- **Added**: Cascading GPTQ backend selection: `gptqmodel` > `auto_gptq` > `transformers_gptq` > `transformers_marlin`.
- **Added**: `_load_gptq_model()` with three backend paths (gptqmodel, auto_gptq, transformers).
- **Added**: `gptqmodel>=2.0` to installed packages.
- **Verified**: GPTQ models never touch `BitsAndBytesConfig`.

### BNB Fallback

- **Added**: `_load_bnb_model()` with BitsAndBytesConfig NF4, double quant, float16 compute dtype.
- **Added**: Automatic fallback when `detect_gptq_backend()` returns `None`.
- **Added**: `quantization_backend` config field controls routing: `"gptq"` skips BNB, `"bnb"` skips GPTQ detection, `"auto"` does both.
- **Added**: `bitsandbytes>=0.45` retained as fallback dependency.

### Context Length Validation

- **Added**: `check_context_fit()` function that validates prompt + new tokens against both `max_context_tokens` and `model.config.max_position_embeddings`.
- **Changed**: `max_context_tokens` default from `12000` to `8192`.
- **Changed**: `generate_with_qwen()` default `max_context_tokens` from `12000` to `8192`.
- **Added**: Model context length read from `model.config.max_position_embeddings` with fallback to 32768.

### GPU and Memory Reporting

- **Added**: `_print_system_info()` called before model loading: prints GPU name, VRAM total/free, RAM total/available (via psutil).
- **Added**: `_print_memory_stats()` called after model loading: prints allocated/reserved GPU memory.
- **Added**: `psutil>=5.9` to installed packages.
- **Changed**: All CUDA calls gated behind `torch.cuda.is_available()` for CPU-only safety.

### Metrics Changes

- **Changed**: `build_change_metrics()` accepts `quantization` parameter (default `"unknown"`) instead of hardcoding `"bnb_nf4_4bit"`.
- **Changed**: `experiment_runner.py` passes `quantization=getattr(model, "_used_quantization", "unknown")` to metrics.
- **Added**: Model attaches `_used_quantization`, `_model_source`, `_resolved_path` metadata after loading.

### Code Cleanup

- **Removed**: Dead `import os` from `llm_runner.py`.
- **Removed**: Dead `_bytes_to_mb()` function from `llm_runner.py`.
- **Removed**: Unused `model_id` parameter from `load_model()` signature.
- **Removed**: Unused `from dataclasses import asdict` from `experiment_runner.py`.
- **Removed**: Stale `experiment_config.json` artifact.
- **Changed**: `load_model()` signature simplified to `(model_path, model_source, quantization_backend, seed)`.

### Notebook Updates

- **Cell 2**: Added `gptqmodel>=2.0`, `bitsandbytes>=0.45`, `psutil>=5.9` to pip install. Removed old `bitsandbytes` from primary install line.
- **Cell 3**: Added guarded imports for `gptqmodel`, `bitsandbytes`, `psutil` with `"not installed"` fallback.
- **Cell 5**: Replaced `ExperimentConfig` fields: removed HF-centric fields, added Kaggle-centric fields.
- **Cell 6**: Added `find_kaggle_model` to imports from `llm_runner`.
- **Cell 10**: Added `find_kaggle_model()` discovery call before `load_model()`. Updated `load_model()` call to new signature.

### v1.0 Reference Notebook

- **Added**: Deprecation header as first cell.
- **Changed**: `ExperimentConfig` updated to match v2 (removed old HF fields, added Kaggle fields).
- **Changed**: `load_model()` call updated to new signature.
- **Changed**: Install dependencies and version checks updated to match v2.

---

## [1.0.0] - 2026-07-18 (Initial)

### Initial Implementation

- Pilot experiment: ToDo API with FastAPI, Pydantic v2, pytest.
- 3 progressive requirement changes (due date, tags, overdue rule).
- Selective regeneration pipeline: DSL diff -> dependency resolution -> LLM generation -> validation -> repair.
- Deterministic repair for missing imports via ruff F821 detection.
- Multi-stage validation: AST parse, compile, ruff, unit, integration, regression, hidden tests.
- Metrics collection with JSONL logging.
- Model loading via Hugging Face Hub with BitsAndBytes NF4 quantization.
- Reproducibility via seed=42 and greedy decoding.
- Snapshot system for project state tracking.
