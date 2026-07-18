# TODO

Development roadmap for the Selective Regeneration Pipeline.

---

## Immediate Fixes

### 1. Kaggle model discovery rewrite
- **Priority**: Critical
- **Status**: Done
- Rewrite `find_kaggle_model()` to search recursively under all `/kaggle/input` paths
- Support both `/kaggle/input/datasets/` and `/kaggle/input/models/` layouts
- Match keywords against full path string, not just directory name
- Require tokenizer files before accepting a candidate
- Reject GGUF directories
- Score candidates with priority: Qwen2.5-Coder GPTQ INT4 > other Qwen GPTQ > plain Transformers
- File: `selective_regeneration/llm_runner.py`

### 2. Model discovery diagnostics
- **Priority**: High
- **Status**: Done
- Add `debug_kaggle_models()` helper that prints:
  - Top-level contents of `/kaggle/input`
  - All discovered `config.json` files
  - Tokenizer file presence for each candidate
  - Quantization info from `quantize_config.json` and `config.json`
  - Candidate scores and rejection reasons
  - Directory tree under `/kaggle/input/models` and `/kaggle/input/datasets`
- File: `selective_regeneration/llm_runner.py`

### 3. Model loading failure messages
- **Priority**: High
- **Status**: Done
- Include paths searched, candidates found, rejection reasons, and Kaggle attach instructions in `FileNotFoundError`
- Never print "No model found" when a valid `config.json` exists
- File: `selective_regeneration/llm_runner.py`

### 4. Lazy torch/transformers imports
- **Priority**: High
- **Status**: Done
- Move `import torch` and `from transformers import ...` inside functions
- Allows model discovery tests to run without GPU dependencies
- File: `selective_regeneration/llm_runner.py`

### 5. Repository restructuring
- **Priority**: High
- **Status**: Done
- Move Python modules into `selective_regeneration/` package directory
- Move notebooks into `notebooks/` and archived notebooks into `notebooks/archive/`
- Create `tests/` directory with model discovery tests
- Create `config/` directory
- Update all imports and paths
- Files: entire repository

---

## Kaggle Runtime Validation

### 6. End-to-end Kaggle notebook test
- **Priority**: High
- **Status**: Pending
- Run the full notebook on a Kaggle GPU session with the Qwen2.5-Coder 7B GPTQ INT4 model attached
- Verify all 3 changes (CH-001, CH-002, CH-003) complete successfully
- Verify model discovery finds the correct path
- Acceptance criteria: notebook runs to completion without errors on Kaggle with GPU

### 7. Kaggle package import path validation
- **Priority**: High
- **Status**: Pending
- Verify that `sys.path.insert` correctly resolves the `selective_regeneration` package on Kaggle
- Test with package uploaded as a Kaggle Dataset
- Test with package in notebook source directory
- Acceptance criteria: all imports succeed on Kaggle runtime

### 8. GPTQ model loading validation on Kaggle
- **Priority**: High
- **Status**: Pending
- Verify `gptqmodel` backend loads correctly on Kaggle T4/P100 GPU
- Verify `auto_gptq` fallback works if `gptqmodel` unavailable
- Verify `transformers` GPTQ fallback works
- Verify BNB fallback works for non-GPTQ models
- Acceptance criteria: model loads and generates valid output on Kaggle GPU

---

## Model Loading Improvements

### 9. Model path caching
- **Priority**: Medium
- **Status**: Pending
- Cache the discovered model path to avoid redundant filesystem scans
- File: `selective_regeneration/llm_runner.py`
- Acceptance criteria: second call to `find_kaggle_model()` returns instantly

### 10. Multi-model support
- **Priority**: Medium
- **Status**: Pending
- Allow specifying which model variant to load when multiple candidates exist
- Add `model_variant` parameter to `ExperimentConfig`
- File: `selective_regeneration/llm_runner.py`, notebook Cell 5

### 11. Model loading timeout
- **Priority**: Medium
- **Status**: Pending
- Add configurable timeout for model loading to detect stuck loads
- Raise clear error if loading exceeds timeout
- File: `selective_regeneration/llm_runner.py`

---

## Selective Regeneration Research Tasks

### 12. Automatic dependency extraction from Python imports
- **Priority**: High
- **Status**: Pending
- Parse `import` and `from ... import` statements to build dependency graph automatically
- Replace manual `DEPENDENCY_RULES` dict in notebook
- Handle relative imports, `__init__.py` re-exports, and conditional imports
- File: new `selective_regeneration/auto_dependency.py`
- Acceptance criteria: auto-extracted rules match manual rules for the ToDo API pilot

### 13. Comparative experiment arms
- **Priority**: High
- **Status**: Pending
- Implement monolithic regeneration arm (regenerate all files)
- Implement agent-based arm (iterative file-by-file)
- Implement compiled-AI arm
- Implement delta-MCP arm
- Implement incremental RTL arm
- Implement code-plan arm
- File: new `selective_regeneration/arms/` directory
- Acceptance criteria: all 7 arms run on the same 3-change benchmark

### 14. Streaming generation support
- **Priority**: Medium
- **Status**: Pending
- Support partial file output to reduce latency
- Allow early termination when sufficient tokens generated
- File: `selective_regeneration/llm_runner.py`

### 15. Multi-repair attempt strategies
- **Priority**: Medium
- **Status**: Pending
- Experiment with multiple repair rounds (currently capped at 1)
- Add temperature sampling for repair diversity
- Track repair effectiveness per attempt
- File: `selective_regeneration/experiment_runner.py`

### 16. Larger model testing
- **Priority**: Medium
- **Status**: Pending
- Test with Qwen2.5-Coder-32B, DeepSeek-Coder, and other coding models
- Compare quality vs 7B model
- File: notebooks, `selective_regeneration/llm_runner.py`

### 17. Multi-project benchmarks
- **Priority**: Medium
- **Status**: Pending
- Run pipeline on BFCL, HumanEval, or other benchmarks
- Adapt the pilot ToDo API to support multiple project types
- Files: notebooks, new benchmark adapters

---

## Dependency Extraction Improvements

### 18. Handle re-exports in `__init__.py`
- **Priority**: Medium
- **Status**: Pending
- When `__init__.py` re-exports symbols, trace them to their source modules
- File: `selective_regeneration/auto_dependency.py` (when created)
- Acceptance criteria: correctly identifies re-exported dependencies

### 19. Handle conditional imports
- **Priority**: Medium
- **Status**: Pending
- Support `try/except ImportError` blocks and `if TYPE_CHECKING` guards
- File: `selective_regeneration/auto_dependency.py` (when created)

### 20. Support third-party dependency tracking
- **Priority**: Low
- **Status**: Pending
- Track which third-party packages each module uses
- Flag when a change might break a third-party integration
- File: new `selective_regeneration/third_party_deps.py`

---

## Impact Analysis Improvements

### 21. Transitive dependency resolution
- **Priority**: High
- **Status**: Pending
- When file A depends on B and B depends on C, a change to C should affect both A and B
- Currently only direct prefix-matching is supported
- File: `selective_regeneration/dependency.py`

### 22. Test-to-source reverse mapping
- **Priority**: Medium
- **Status**: Pending
- Automatically detect which tests cover which source files
- Use import analysis or coverage data to build reverse mapping
- File: `selective_regeneration/dependency.py`

### 23. Change confidence scoring
- **Priority**: Medium
- **Status**: Pending
- Score each change by estimated risk based on:
  - Number of affected files
  - Complexity of the DSL diff
  - Historical pass/fail rates for similar changes
- File: `selective_regeneration/dependency.py`

---

## Artifact Validation Improvements

### 24. Type-aware validation
- **Priority**: Medium
- **Status**: Pending
- Use mypy or pyright for type checking in addition to AST parse
- File: `selective_regeneration/validation.py`

### 25. Import cycle detection
- **Priority**: Medium
- **Status**: Pending
- Detect when generated code creates import cycles
- File: `selective_regeneration/validation.py`

### 26. Semantic test analysis
- **Priority**: Low
- **Status**: Pending
- Analyze whether tests actually test the expected behavior
- Detect tests that pass vacuously (no assertions)
- File: `selective_regeneration/validation.py`

---

## Evaluation and Baselines

### 27. Baseline metrics collection
- **Priority**: High
- **Status**: Pending
- Record baseline metrics before any changes:
  - Initial project complexity
  - File count, line count
  - Test coverage
- File: `selective_regeneration/metrics.py`

### 28. Functional correctness metrics
- **Priority**: Medium
- **Status**: Pending
- Measure whether the generated code actually does what the requirement specifies
- Beyond test pass/fail, check behavioral correctness
- File: `selective_regeneration/metrics.py`

### 29. Code complexity metrics
- **Priority**: Medium
- **Status**: Pending
- Track cyclomatic complexity before/after each change
- Flag changes that significantly increase complexity
- File: `selective_regeneration/metrics.py`

### 30. Mutation testing
- **Priority**: Low
- **Status**: Pending
- Use mutation testing to assess test suite quality
- Compare mutation scores before/after changes
- File: new `selective_regeneration/mutation_testing.py`

---

## Reproducibility

### 31. Experiment configuration versioning
- **Priority**: Medium
- **Status**: Pending
- Version the `ExperimentConfig` and include it in metrics output
- Track config changes across runs
- File: `selective_regeneration/experiment_runner.py`

### 32. Deterministic model output verification
- **Priority**: Medium
- **Status**: Pending
- Verify that `seed=42` with `do_sample=False` produces identical outputs across runs
- Document any non-determinism from GPU operations
- Files: tests, notebooks

### 33. Snapshot diffing improvements
- **Priority**: Low
- **Status**: Pending
- Show semantic diffs (not just file-level) when comparing snapshots
- Highlight exactly which lines changed in each file
- File: `selective_regeneration/snapshots.py`

---

## Documentation

### 34. API reference generation
- **Priority**: Medium
- **Status**: Pending
- Auto-generate API docs from docstrings using sphinx or pdoc
- Include in CI pipeline
- Acceptance criteria: docs auto-update on every commit

### 35. Kaggle deployment guide
- **Priority**: High
- **Status**: Done
- Step-by-step guide for deploying on Kaggle
- Include model attachment instructions
- Include troubleshooting for common failures
- File: `README-KAGGLE.md`

### 36. Architecture decision records
- **Priority**: Low
- **Status**: Pending
- Document key design decisions and their rationale
- Cover: staging directory pattern, complete file generation, deterministic-before-LLM repair
- File: new `docs/adr/` directory

---

## Technical Debt

### 37. Remove dead code from v1.0 notebook
- **Priority**: Low
- **Status**: Done
- Archive the deprecated v1.0 notebook properly
- Remove any stale references to HF Hub loading
- File: `notebooks/archive/v1.0-research-baseline.ipynb`

### 38. Type annotations consistency
- **Priority**: Medium
- **Status**: Pending
- Ensure all functions have complete type annotations
- Add `py.typed` marker to package
- Run mypy in strict mode
- File: all `selective_regeneration/*.py`

### 39. Error handling consistency
- **Priority**: Medium
- **Status**: Pending
- Ensure all error paths raise typed exceptions (not generic `Exception`)
- Add error codes for common failures
- Files: all `selective_regeneration/*.py`

### 40. Test coverage for non-discovery modules
- **Priority**: High
- **Status**: Pending
- Add unit tests for `dsl.py`, `diff.py`, `dependency.py`, `patching.py`, `snapshots.py`
- Add unit tests for `output_parser.py`, `context_builder.py`
- Add integration tests for `experiment_runner.py` (mock LLM)
- Acceptance criteria: >80% line coverage for package

---

## Future Research Extensions

### 41. Multi-language support
- **Priority**: Low
- **Status**: Pending
- Extend pipeline to support JavaScript/TypeScript projects
- Adapt validation pipeline for non-Python languages
- File: new language adapters

### 42. Collaborative regeneration
- **Priority**: Low
- **Status**: Pending
- Support concurrent changes by multiple developers
- Detect and resolve conflicts between parallel regenerations
- File: new `selective_regeneration/collaborative.py`

### 43. Feedback loop integration
- **Priority**: Low
- **Status**: Pending
- Learn from past failures to improve future generations
- Build a failure pattern database
- Use patterns to guide repair strategies
- File: new `selective_regeneration/feedback.py`

### 44. CI/CD integration
- **Priority**: Medium
- **Status**: Pending
- Run pipeline in GitHub Actions or similar
- Trigger on pull requests with requirement changes
- Post results as PR comments
- File: new `.github/workflows/` directory

### 45. Dashboard and visualization
- **Priority**: Low
- **Status**: Pending
- Build a web dashboard to visualize experiment results
- Show pass/fail rates, token usage, timing trends
- Compare arms side-by-side
- File: new `dashboard/` directory
