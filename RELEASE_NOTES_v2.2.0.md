# Release Notes — v2.2.0

**Research Baseline v2.2.0 (RC1)**

Release Date: 2026-07-18

---

## Summary

This release establishes the frozen research baseline for the Selective Regeneration Pipeline. The system is a complete, documented, and tested framework for evaluating LLM-guided selective code regeneration using dependency-aware impact analysis.

---

## Implemented Functionality

### Core Pipeline
- DSL-based requirement change definition (`RequirementChange` dataclass)
- Structural diff engine for YAML DSL dictionaries
- Dependency rule graph for mapping DSL changes to source files
- LLM prompt construction with system prompts and output schema
- JSON output parsing with brace-matching fallback
- Payload schema validation (jsonschema)
- Scope validation (allowlist, path traversal, duplicates)
- Staging directory pattern with copy-on-success
- File read/write/payload application operations
- Snapshot creation and manifest comparison
- Multi-stage validation pipeline (7 stages)

### Model Loading
- Auto-discovery under `/kaggle/input/` with recursive search
- Path-keyword scoring (12 criteria)
- Tokenizer file validation
- GGUF directory rejection
- GPTQ backend auto-detection (gptqmodel > auto-gptq > transformers)
- BNB NF4 fallback with double quant
- Context length validation against model limits
- GPU and RAM reporting

### Repair System
- Deterministic repair for missing imports (ruff F821 detection)
- Safe import lookup table (13 common imports)
- LLM repair fallback with validation-informed prompts

### Metrics and Observability
- JSONL metrics logging per change
- Token usage tracking (prompt/output/total)
- Timing data (per-generation and total)
- Peak GPU memory tracking
- 7-category failure classification
- Stage-level pass/fail tracking

### Testing
- 19 unit tests for model discovery (no GPU required)
- Lazy torch/transformers imports for testability

---

## Architecture

```
RequirementChange → DSL Patch → Structural Diff → Dependency Resolution
    → Prompt Construction → LLM Generation → JSON Parsing → Scope Validation
        → Staging Copy → Apply Payload → Write DSL → Write Hidden Tests
            → Multi-Stage Validation
                → Deterministic Repair (ruff)
                → Optional LLM Repair
            → Snapshot → Commit → Metrics
```

Key design decisions:
- Selective regeneration (only affected files sent to LLM)
- Complete file generation (not line-level diffs)
- Staging directory pattern (validate before commit)
- Deterministic-before-LLM repair (cheap fixes first)
- Kaggle-first loading (local files, no HF Hub download)

---

## Documentation

10 documentation files:

| File | Purpose |
|------|---------|
| README.md | Project overview and getting started |
| README-KAGGLE.md | Kaggle deployment guide |
| ARCHITECTURE.md | System design and flowcharts |
| CODEBASE_MAP.md | Per-module documentation |
| SYSTEM_STATE.md | Current status and design decisions |
| CHANGELOG.md | Version history |
| TODO.md | Development roadmap |
| PROJECT_SUMMARY.md | Executive overview |
| RELEASE_CHECKLIST.md | Pre-release verification |
| FINAL_BASELINE.md | Frozen baseline record |

---

## Testing

- 19 unit tests in `tests/test_model_discovery.py`
- Covers: tokenizer detection, candidate scoring, GGUF rejection, empty directories, multiple candidates
- Tests run without GPU (lazy torch/transformers imports)
- Run with: `python -m pytest tests/test_model_discovery.py -v`

---

## Known Limitations

1. Pilot project is a simple ToDo API; results may not generalize.
2. Dependency rules are manually specified, not auto-extracted from imports.
3. Only Python 3.11+ projects (FastAPI + Pydantic v2 + pytest).
4. Complete file generation (not line-level diffs) for all affected files.
5. Hidden tests are pre-defined per change, not dynamically generated.
6. Deterministic repair handles only missing imports (fixed lookup table).
7. No streaming or incremental generation.
8. Context length hard-capped at 8192 tokens.
9. Single GPU only; no multi-GPU support.

---

## GPU-Only Validation Remaining

These items require a Kaggle GPU session:

- End-to-end notebook execution on Kaggle T4/P100 GPU
- GPTQ model loading with all backends
- BNB NF4 fallback loading
- All 3 changes completing successfully
- Model discovery finding the correct path
- Context length validation with real model config
- Peak GPU memory tracking accuracy
- Hidden tests passing on generated code

---

## Files Changed (32 tracked)

| Category | Count | Files |
|----------|-------|-------|
| Package | 15 | `selective_regeneration/*.py` |
| Notebooks | 2 | `qwen-selective-regeneration-v2.ipynb`, archived `v1.0-research-baseline.ipynb` |
| Tests | 2 | `test_model_discovery.py`, `__init__.py` |
| Config | 1 | `experiment_config.json` |
| Documentation | 10 | 10 markdown files |
| Other | 2 | `MANIFEST.json`, `requirements-kaggle.txt` |
