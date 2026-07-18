# Selective Regeneration Pipeline

A research framework for evaluating LLM-guided selective code regeneration using dependency-aware impact analysis.

## Project Overview

This project studies how an LLM can apply a requirement change to a Python project by modifying **only the files affected by the change**, rather than regenerating the entire codebase. It combines a dependency graph, a DSL (Domain-Specific Language) diff, and a Qwen2.5-Coder model to produce minimal, targeted code edits.

The pipeline:

1. Defines a requirement change as a structured delta against a YAML-based DSL.
2. Computes a structural diff between the old and new DSL.
3. Resolves affected source files via a dependency rule graph.
4. Sends the diff + affected files to the LLM and receives a JSON payload of file operations.
5. Applies the payload to a staging copy of the project.
6. Validates the result through a multi-stage pipeline: AST parse, compile, ruff lint, unit tests, integration tests, regression tests, and hidden tests.
7. If validation fails, attempts deterministic repair (missing imports via ruff), then falls back to an LLM repair call.
8. If all validation passes, commits the change to the working project.

## Research Objective

Evaluate whether **selective regeneration** (targeted file edits guided by dependency analysis) outperforms full-codebase regeneration in terms of:

- First-pass acceptance rate
- Token efficiency
- Code correctness (measured by hidden test suites)
- Repairability (can local deterministic repair or a single LLM repair call fix failures?)

## Repository Structure

```
project-root/
├── README.md
├── README-KAGGLE.md
├── SYSTEM_STATE.md
├── ARCHITECTURE.md
├── CODEBASE_MAP.md
├── CHANGELOG.md
├── TODO.md
├── PROJECT_SUMMARY.md
├── RELEASE_CHECKLIST.md
├── MANIFEST.json
├── requirements-kaggle.txt
│
├── notebooks/
│   ├── qwen-selective-regeneration-v2.ipynb
│   └── archive/
│       └── v1.0-research-baseline.ipynb
│
├── selective_regeneration/
│   ├── __init__.py
│   ├── change_model.py
│   ├── ch_003_definition.py
│   ├── context_builder.py
│   ├── dependency.py
│   ├── deterministic_repair.py
│   ├── diff.py
│   ├── dsl.py
│   ├── experiment_runner.py
│   ├── llm_runner.py
│   ├── metrics.py
│   ├── output_parser.py
│   ├── patching.py
│   ├── snapshots.py
│   └── validation.py
│
├── config/
│   └── experiment_config.json
│
└── tests/
│   ├── __init__.py
│   └── test_model_discovery.py
```

## How to Run on Kaggle

### Prerequisites

1. Create a new Kaggle notebook with **GPU** accelerator enabled (T4, P100, or better).
2. Go to **Add Data > Add Model** and search for `qwen2.5-coder`.
3. Add the model: `qwen-lm/qwen2.5-coder` with variant `7b-instruct-gptq-int4` (Transformers format).

### Execution

1. Upload the `selective_regeneration/` package directory to the Kaggle notebook working directory.
2. Upload `notebooks/qwen-selective-regeneration-v2.ipynb` as the notebook.
3. Run all cells in order.

The notebook:

- Cell 1: Hardware check (GPU, CUDA, PyTorch)
- Cell 2: Installs dependencies (`gptqmodel`, `bitsandbytes`, `transformers`, etc.)
- Cell 3: Verifies package versions
- Cell 4: Creates working directories and sets up module path
- Cell 5: Defines `ExperimentConfig` (model source, context limits, seeds)
- Cell 6: Imports all modules
- Cell 7: Creates the initial ToDo API project
- Cell 8: Validates the initial project passes all tests
- Cell 9: Saves an initial snapshot
- Cell 10: Runs model discovery diagnostics, discovers and loads the model
- Cell 11: Smoke test (simple JSON generation)
- Cell 12-21: Runs 3 requirement changes, validates each
- Cell 22-23: Summary and metrics export
- Cell 24: Zips output

### Model Loading

The system automatically:

1. Searches `/kaggle/input/` recursively for model directories with `config.json`.
2. Scores candidates by path keywords (Qwen2.5-Coder, GPTQ, INT4).
3. Rejects GGUF directories and candidates without tokenizer files.
4. Detects if the model is GPTQ-quantized via `quantize_config.json` or `config.json`.
5. If GPTQ: loads via `gptqmodel` > `auto-gptq` > `transformers` (cascading fallback).
6. If not GPTQ: falls back to BitsAndBytes NF4 4-bit quantization.
7. No Hugging Face download is attempted. All loading is from local files.

See `debug_kaggle_models()` for diagnostic output of the discovery process.

## Required Kaggle Models

| Model | Variant | Purpose |
|-------|---------|---------|
| `qwen-lm/qwen2.5-coder` | `7b-instruct-gptq-int4` (Transformers) | Primary model (GPTQ INT4) |
| `qwen-lm/qwen2.5-coder` | `7b-instruct` (Transformers) | Fallback (BNB NF4 quantized at load time) |

## Required Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `transformers` | >= 4.48 | Model loading and tokenization |
| `accelerate` | >= 1.2 | Device map and distributed loading |
| `gptqmodel` | >= 2.0 | GPTQ quantized model loading (primary) |
| `bitsandbytes` | >= 0.45 | BNB NF4 fallback quantization |
| `sentencepiece` | >= 0.2 | Tokenizer dependency |
| `safetensors` | >= 0.4 | Safe tensor loading |
| `pydantic` | >= 2.8, <= 2.12.3 | Validation schemas |
| `pyyaml` | >= 6.0 | DSL YAML parsing |
| `jsonschema` | >= 4.23 | JSON output validation |
| `pandas` | >= 2.2 | Metrics tabulation |
| `ruff` | >= 0.11 | Linting and deterministic repair |
| `psutil` | >= 5.9 | RAM reporting |
| `fastapi` | latest | ToDo API project |
| `pytest` | latest | Test execution |
| `httpx` | latest | Test client |
| `pytest-cov` | latest | Coverage reporting |

## Configuration Options

The `ExperimentConfig` dataclass in the notebook controls the experiment:

| Field | Default | Description |
|-------|---------|-------------|
| `experiment_name` | `"todo_selective_regeneration_v1"` | Experiment identifier for metrics |
| `model_source` | `"kaggle"` | Where to find the model (`"kaggle"` or `"hf"`) |
| `model_id` | `"qwen-lm/qwen2.5-coder"` | Model identifier for metrics logging |
| `model_path` | `""` | Explicit path to model directory (auto-discovered if empty) |
| `quantization_backend` | `"gptq"` | Preferred backend: `"gptq"`, `"bnb"`, or `"auto"` |
| `max_context_tokens` | `8192` | Maximum allowed prompt token count |
| `max_new_tokens` | `4000` | Maximum tokens the LLM may generate per call |
| `do_sample` | `False` | Greedy decoding |
| `seed` | `42` | Global seed for reproducibility |
| `max_repair_attempts` | `1` | Number of LLM repair calls after local repair fails |
| `generation_timeout_seconds` | `600` | Timeout for LLM generation |
| `test_timeout_seconds` | `180` | Timeout per validation stage |
| `run_ruff` | `True` | Enable ruff linting in validation |
| `run_unit_tests` | `True` | Enable unit test validation |
| `run_integration_tests` | `True` | Enable integration test validation |
| `run_hidden_tests` | `True` | Enable hidden test validation |

## Metrics

Each change run produces a metrics record written to `results/selective_runs.jsonl`. Fields include:

- **Token counts**: prompt/output/total for both initial and repair generations
- **Timing**: per-generation seconds and total wall-clock time
- **Memory**: peak GPU memory in MB
- **Outcome flags**: `first_pass_acceptance`, `accepted_after_local_repair`, `accepted_after_llm_repair`
- **Stage results**: `compile_pass`, `ruff_pass`, `unit_pass`, `integration_pass`, `regression_pass`, `hidden_tests_pass`
- **Failure classification**: one of 7 failure category strings
- **File-level data**: affected files, actually modified files, DSL diff element count

## Testing

Run model discovery tests locally (no GPU required):

```bash
python -m pytest tests/test_model_discovery.py -v
```

## Current Limitations

- The pilot project is a simple ToDo API; results may not generalize to larger codebases.
- Dependency rules are manually specified, not automatically extracted from imports.
- Only Python 3.11+ projects are supported (FastAPI + Pydantic v2 + pytest).
- The model generates complete file contents for each affected file (not line-level diffs).
- Hidden tests are pre-defined per change, not dynamically generated.
- The deterministic repair only handles missing imports via a fixed lookup table.
- No streaming or incremental generation; each repair is a full re-generation.
- Context length is hard-capped at `max_context_tokens` (8192); longer prompts are rejected.
- Single GPU only; no multi-GPU or multi-node support.
