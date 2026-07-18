# Project Summary

Executive overview of the Selective Regeneration Pipeline.

---

## Research Title

**Selective Regeneration: LLM-Guided Targeted Code Updates via Dependency-Aware Impact Analysis**

## Research Objective

Evaluate whether an LLM can apply requirement changes to a Python codebase by modifying **only the files affected by the change**, rather than regenerating the entire project. This studies the trade-off between token efficiency, code correctness, and repairability compared to full-codebase regeneration.

## Main Contribution

A pipeline that combines:
1. A YAML-based DSL (Domain-Specific Language) to represent project structure.
2. Structural diffing of DSL changes to identify what changed.
3. A dependency rule graph that maps DSL changes to source files.
4. LLM generation scoped to only affected files (selective regeneration).
5. Multi-stage validation with deterministic repair before LLM repair.

This approach sends far fewer tokens to the LLM than full regeneration, while maintaining correctness through comprehensive validation.

---

## Repository Overview

```
selective-regeneration-pipeline/
├── selective_regeneration/    # Python package (15 modules)
├── notebooks/                 # Jupyter notebook (main experiment driver)
│   ├── qwen-selective-regeneration-v2.ipynb
│   └── archive/v1.0-research-baseline.ipynb
├── tests/                     # Unit tests (model discovery)
├── config/                    # Experiment configuration
├── *.md                       # Documentation (9 files)
├── MANIFEST.json              # Repository structure manifest
└── requirements-kaggle.txt    # Kaggle dependencies
```

## Current Implementation Status

### Complete

- Full selective regeneration pipeline (DSL diff → dependency resolution → LLM generation → validation → repair → commit).
- Model loading from Kaggle with GPTQ INT4 (primary) and BNB NF4 (fallback).
- Auto-discovery of Qwen2.5-Coder model under `/kaggle/input/` with recursive search and keyword scoring.
- GPTQ backend auto-detection (gptqmodel > auto-gptq > transformers).
- Context length validation against model limits.
- Deterministic repair for missing imports via ruff F821 detection.
- Multi-stage validation: AST parse, compile, ruff, unit, integration, regression, hidden tests.
- Metrics collection with JSONL logging (tokens, timing, memory, outcomes).
- Pilot experiment: ToDo API with 3 progressive requirement changes.
- 19 unit tests for model discovery (no GPU required).
- Complete documentation suite (8 markdown files).
- Kaggle deployment guide with troubleshooting.

### Pending (requires GPU)

- End-to-end Kaggle notebook validation.
- GPTQ model loading verification on real hardware.
- Multi-model testing (32B, DeepSeek-Coder).

### Future Work

- Automatic dependency extraction from Python imports.
- Comparative experiment arms (monolithic, agent, compiled-AI, delta-MCP, incremental RTL, code-plan).
- Multi-project benchmarks (BFCL, HumanEval).
- Streaming generation, multi-repair strategies, CI/CD integration.

---

## Project Architecture

### Core Pipeline

```
RequirementChange → DSL Patch → Structural Diff → Dependency Resolution
    → Prompt Construction → LLM Generation → JSON Parsing → Scope Validation
        → Staging Copy → Apply Payload → Write DSL → Write Hidden Tests
            → Multi-Stage Validation
                → Deterministic Repair (ruff)
                → Optional LLM Repair
            → Snapshot → Commit → Metrics
```

### Key Design Decisions

1. **Selective regeneration**: Only affected files are sent to the LLM, not the entire codebase.
2. **Complete file generation**: The LLM generates full file contents, not line-level diffs.
3. **Staging directory pattern**: Changes are validated in a copy before committing to the working project.
4. **Deterministic-before-LLM repair**: Cheap ruff-based import fixes are tried before expensive LLM repair calls.
5. **Kaggle-first loading**: Models are loaded from local `/kaggle/input/`, never downloaded from Hugging Face Hub.

---

## Key Modules

| Module | Purpose | Lines |
|--------|---------|-------|
| `experiment_runner.py` | Full pipeline orchestration for a single change | 337 |
| `llm_runner.py` | Model loading (GPTQ/BNB), generation, memory management | 726 |
| `context_builder.py` | LLM prompt construction, system prompts, output schema | 222 |
| `validation.py` | Multi-stage project validation (7 stages) | 162 |
| `metrics.py` | Metrics collection and JSONL storage | 240 |
| `deterministic_repair.py` | Ruff-based repair for missing imports | 150 |
| `ch_003_definition.py` | CH-003 requirement change definition | 184 |
| `output_parser.py` | JSON extraction and validation from LLM output | 89 |
| `snapshots.py` | Snapshot creation and manifest comparison | 85 |
| `patching.py` | File read/write/payload application | 71 |
| `diff.py` | Structural diff engine for YAML DSL | 57 |
| `dsl.py` | YAML DSL read/write/patch | 46 |
| `change_model.py` | RequirementChange dataclass definition | 23 |
| `dependency.py` | Dependency rule resolution via prefix matching | 14 |

---

## Current Capabilities

- Applies 3 progressive requirement changes to a ToDo API project.
- Generates code changes guided by DSL structural diffs and dependency analysis.
- Validates generated code through 7 validation stages.
- Automatically repairs missing imports via ruff.
- Falls back to LLM repair when deterministic repair is insufficient.
- Tracks token usage, timing, memory, and pass/fail outcomes per change.
- Produces project snapshots for before/after comparison.

## Current Limitations

- Pilot project is a simple ToDo API; results may not generalize.
- Dependency rules are manually specified, not auto-extracted from imports.
- Only Python 3.11+ projects (FastAPI + Pydantic v2 + pytest).
- Complete file generation (not line-level diffs) for all affected files.
- Hidden tests are pre-defined per change, not dynamically generated.
- Deterministic repair handles only missing imports (fixed lookup table).
- No streaming or incremental generation.
- Context length hard-capped at 8192 tokens.
- Single GPU only; no multi-GPU support.

---

## Future Roadmap

| Phase | Task | Priority |
|-------|------|----------|
| **Immediate** | End-to-end Kaggle GPU validation | Critical |
| **Near-term** | Automatic dependency extraction from imports | High |
| **Near-term** | Comparative experiment arms (7 arms) | High |
| **Near-term** | Multi-project benchmarks | Medium |
| **Medium-term** | Streaming generation support | Medium |
| **Medium-term** | Multi-repair attempt strategies | Medium |
| **Medium-term** | Larger model testing (32B, DeepSeek) | Medium |
| **Long-term** | CI/CD integration | Medium |
| **Long-term** | Dashboard and visualization | Low |

---

## How to Continue Development

### Quick Start

1. Read `ARCHITECTURE.md` for system design.
2. Read `CODEBASE_MAP.md` for per-module details.
3. Read `SYSTEM_STATE.md` for current status and design decisions.
4. See `TODO.md` for the full task list.

### Making Changes

| What you want to do | Where to modify |
|---------------------|-----------------|
| Add a new experiment arm | Create new notebook, reuse `experiment_runner.run_selective_change()` |
| Change model loading | `llm_runner.py` (load functions) |
| Change model discovery | `llm_runner.py` (`find_kaggle_model`, `_score_candidate`) |
| Add new validation stages | `validation.py:validate_project()` |
| Add new repair strategies | `deterministic_repair.py` or new module |
| Change prompt engineering | `context_builder.py` |
| Modify output parsing | `output_parser.py` |
| Add new metrics | `metrics.py:build_change_metrics()` |
| Change DSL schema | `dsl.py` and `context_builder.py:GENERATION_SCHEMA` |
| Add new requirement changes | Notebook cells (define `RequirementChange` instances) |
| Change dependency rules | Notebook cell 12 (dict definition) |

### Testing

```bash
# Run model discovery tests (no GPU required):
python -m pytest tests/test_model_discovery.py -v
```

### Running the Experiment

```bash
# Upload to Kaggle, attach Qwen2.5-Coder 7B GPTQ INT4, run all cells.
# See README-KAGGLE.md for step-by-step instructions.
```
