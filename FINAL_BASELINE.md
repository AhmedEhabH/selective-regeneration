# FINAL_BASELINE.md

**Research Baseline v2.2.0 (RC1)**

---

## Version

**v2.2.0** — Release Candidate 1

## Date

2026-07-18

## Freeze Status

**FROZEN** — This document marks the frozen research baseline. No further refactoring, feature additions, or algorithm changes should be made to this commit. All future research work builds upon this snapshot.

---

## Repository Statistics

| Metric | Value |
|--------|-------|
| Python modules | 17 (15 package + 2 test) |
| Total Python lines | ~2,800 |
| Notebooks | 2 (1 active + 1 archived) |
| Documentation files | 10 (9 markdown + FINAL_BASELINE.md) |
| Unit tests | 19 (model discovery) |
| Test coverage | Model discovery logic only |
| Config files | 1 (experiment_config.json) |
| Package name | `selective_regeneration` |
| Required GPU | Yes (T4, P100, or better) |
| Target model | Qwen2.5-Coder 7B GPTQ INT4 |

---

## Project Status

**Research Baseline — Ready for Experimentation**

The selective regeneration pipeline is fully implemented and documented. The codebase has passed:
- Repository quality audit (no duplicates, dead code, broken imports)
- Package audit (all modules purposeful, all public APIs documented)
- Notebook audit (logical cell order, consistent numbering)
- Documentation audit (all 10 documents cross-checked and consistent)
- Static audit (no syntax errors, no circular imports, no naming violations)
- MANIFEST audit (all 31 tracked files verified)

---

## Implemented Features

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

## Remaining GPU-Only Validation

These items CANNOT be verified without a Kaggle GPU session:

- [ ] End-to-end notebook execution on Kaggle T4/P100 GPU
- [ ] GPTQ model loading with `gptqmodel` backend
- [ ] GPTQ model loading with `auto_gptq` fallback
- [ ] BNB NF4 fallback loading and generation
- [ ] All 3 changes (CH-001, CH-002, CH-003) complete successfully
- [ ] Model discovery finds the correct path under `/kaggle/input/`
- [ ] Context length validation with real model config (32768)
- [ ] Peak GPU memory tracking accuracy
- [ ] All hidden tests pass on generated code
- [ ] Metrics JSONL output contains all expected fields
- [ ] Notebook runs to completion without errors

---

## Known Limitations

1. **Pilot scope**: ToDo API only; results may not generalize to larger codebases.
2. **Manual dependency rules**: Not auto-extracted from Python imports.
3. **Python 3.11+ only**: FastAPI + Pydantic v2 + pytest required.
4. **Complete file generation**: LLM generates full files, not line-level diffs.
5. **Pre-defined hidden tests**: Not dynamically generated per change.
6. **Limited deterministic repair**: Only missing imports (fixed lookup table).
7. **No streaming**: Each repair is a full re-generation.
8. **8192 token cap**: Longer prompts are rejected.
9. **Single GPU only**: No multi-GPU or multi-node support.

---

## Research Scope

This baseline evaluates **selective regeneration** — the approach of sending only dependency-affected files to an LLM for code modification, rather than regenerating the entire codebase.

### Measured Metrics
- First-pass acceptance rate
- Token efficiency (prompt + output tokens per change)
- Code correctness (hidden test pass rate)
- Repairability (deterministic repair success rate, LLM repair success rate)
- Wall-clock time per change
- Peak GPU memory usage

### Experiment Design
- 3 progressive requirement changes on a ToDo API
- Each change tested independently
- Metrics recorded per change in JSONL format
- Snapshots taken before and after each change

---

## What Should Be Implemented Next

| Priority | Task | Rationale |
|----------|------|-----------|
| 1 | End-to-end Kaggle validation | Verify pipeline works on real hardware |
| 2 | Automatic dependency extraction | Replace manual rules with import analysis |
| 3 | Comparative experiment arms | Monolithic, agent, compiled-AI, delta-MCP, incremental RTL, code-plan |
| 4 | Multi-project benchmarks | BFCL, HumanEval adaptation |
| 5 | Streaming generation | Reduce latency for large files |
| 6 | Multi-repair strategies | Multiple rounds, temperature sampling |
| 7 | Larger model testing | 32B, DeepSeek-Coder comparison |

---

## Freeze Notice

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   RESEARCH BASELINE v2.2.0 (RC1) — FROZEN              │
│                                                         │
│   Date: 2026-07-18                                     │
│   Status: Ready for experiment execution                │
│                                                         │
│   This is the baseline that future research work        │
│   will build upon. Do not modify this commit without    │
│   explicit approval.                                    │
│                                                         │
│   To run the experiment:                                │
│   1. Upload to Kaggle with GPU                          │
│   2. Attach Qwen2.5-Coder 7B GPTQ INT4                 │
│   3. Run all cells in the notebook                      │
│   4. See README-KAGGLE.md for details                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
