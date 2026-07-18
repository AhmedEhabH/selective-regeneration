# Release Checklist

Pre-release verification for the Selective Regeneration Pipeline v2.2.0.

---

## Repository Structure

- [x] All Python modules in `selective_regeneration/` package
- [x] All notebooks in `notebooks/` (main) and `notebooks/archive/` (deprecated)
- [x] All tests in `tests/`
- [x] All config in `config/`
- [x] No duplicate files
- [x] No obsolete files outside `notebooks/archive/`
- [x] No `.bak` files
- [x] No `__pycache__` directories committed
- [x] MANIFEST.json matches repository contents

## Documentation

- [x] README.md — project overview, how to run, configuration options
- [x] README-KAGGLE.md — Kaggle deployment guide with troubleshooting
- [x] ARCHITECTURE.md — system design, flowcharts, scoring tables
- [x] CODEBASE_MAP.md — per-module documentation, dependency graph
- [x] SYSTEM_STATE.md — current status, design decisions, assumptions
- [x] CHANGELOG.md — version history (v1.0 through v2.2)
- [x] TODO.md — development roadmap (45 tasks)
- [x] PROJECT_SUMMARY.md — executive overview for new developers
- [x] All documented file paths exist
- [x] No contradictions between documents

## Code Quality

- [x] Every module has a header comment
- [x] Every public function has a docstring
- [x] Every class has a docstring
- [x] No unused imports
- [x] No dead code
- [x] No broken imports
- [x] No temporary debugging code
- [x] `__init__.py` exports the intended public API
- [x] `ch_003_definition.py` print statement removed

## Package Self-Containment

- [x] All 15 modules present and purposeful
- [x] All internal imports resolve correctly
- [x] All external imports guarded (torch, transformers, gptqmodel, auto_gptq, psutil)
- [x] Lazy imports for GPU dependencies (testability)

## Notebook

- [x] Cells execute in logical order
- [x] No duplicated cells
- [x] No obsolete cells
- [x] Section numbering consistent (Cells 1-24)
- [x] Diagnostics appear before model loading
- [x] All 55 imported symbols verified against package source
- [x] Readable without reading source code

## Tests

- [x] `test_model_discovery.py` — 19 unit tests
- [x] Tests pass without GPU (lazy torch/transformers imports)
- [x] Tests cover: tokenizer detection, candidate scoring, GGUF rejection, empty dirs, multiple candidates

## Kaggle Package Ready

- [x] `requirements-kaggle.txt` lists all dependencies with versions
- [x] `README-KAGGLE.md` provides step-by-step deployment guide
- [x] Model attachment instructions documented
- [x] Troubleshooting guide for common failures

## Model Discovery Ready

- [x] `find_kaggle_model()` searches recursively under `/kaggle/input/`
- [x] Keyword scoring matches actual implementation
- [x] Tokenizer file validation
- [x] GGUF rejection
- [x] `debug_kaggle_models()` diagnostics

## GPTQ Loading Ready

- [x] `detect_gptq_backend()` reads `quantize_config.json` and `config.json`
- [x] Cascading backend: gptqmodel > auto_gptq > transformers
- [x] GPTQ models never touch BitsAndBytesConfig

## BNB Fallback Ready

- [x] `_load_bnb_model()` with NF4 + double quant + float16
- [x] Automatic fallback when GPTQ not detected
- [x] `bitsandbytes>=0.45` in requirements

## Research Baseline Complete

- [x] Pilot experiment: ToDo API with FastAPI + Pydantic v2 + pytest
- [x] 3 progressive requirement changes (due date, tags, overdue rule)
- [x] Deterministic repair for missing imports
- [x] Multi-stage validation pipeline
- [x] Metrics collection with JSONL logging

---

## Remaining GPU-Only Validation Steps

These steps require a real Kaggle GPU session and cannot be verified locally:

- [ ] End-to-end notebook execution on Kaggle T4/P100 GPU
- [ ] GPTQ model loading with `gptqmodel` backend
- [ ] GPTQ model loading with `auto_gptq` fallback
- [ ] BNB NF4 fallback loading
- [ ] All 3 changes (CH-001, CH-002, CH-003) complete successfully
- [ ] Model discovery finds the correct path under `/kaggle/input/`
- [ ] Context length validation with real model config
- [ ] Peak GPU memory tracking accuracy
- [ ] All hidden tests pass on generated code
- [ ] Snapshot comparison shows expected file changes
- [ ] Metrics JSONL output contains all expected fields
- [ ] Notebook runs to completion without errors
