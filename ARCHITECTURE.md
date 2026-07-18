# Architecture

This document describes the complete system architecture of the Selective Regeneration Pipeline.

## Repository Structure

```
2026-07-18-1655/
├── notebooks/
│   ├── qwen-selective-regeneration-v2.ipynb
│   └── archive/
│       └── v1.0-research-baseline.ipynb
├── selective_regeneration/                     # Python package
│   ├── __init__.py
│   ├── ch_003_definition.py
│   ├── change_model.py
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
├── config/
│   └── experiment_config.json
├── tests/
│   ├── __init__.py
│   └── test_model_discovery.py
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CODEBASE_MAP.md
├── MANIFEST.json
├── README.md
├── README-KAGGLE.md
├── SYSTEM_STATE.md
├── TODO.md
└── requirements-kaggle.txt
```

## System Overview

```mermaid
graph TB
    subgraph "notebooks/qwen-selective-regeneration-v2.ipynb"
        A[Cell 5: ExperimentConfig] --> B[Cell 7: Create Project]
        B --> C[Cell 8: Validate Initial]
        C --> D[Cell 9: Snapshot Initial]
        D --> E[Cell 10: Load Model]
        E --> F[Cell 11: Smoke Test]
        F --> G[Cell 12: Dependency Rules]
        G --> H[Cell 13-21: Run Changes]
        H --> I[Cell 22-23: Summary + Metrics]
    end

    subgraph "selective_regeneration/ (package)"
        J[experiment_runner.py] --> K[context_builder.py]
        J --> L[output_parser.py]
        J --> M[patching.py]
        J --> N[snapshots.py]
        J --> O[validation.py]
        J --> P[deterministic_repair.py]
        J --> Q[diff.py]
        J --> R[dependency.py]
        J --> S[dsl.py]
        J --> T[llm_runner.py]
        J --> U[metrics.py]
    end

    H --> J
```

## Requirement Change Flow

```mermaid
flowchart TD
    A[Define RequirementChange] --> B[Apply DSL Patch]
    B --> C[Compute Structural Diff]
    C --> D[Resolve Affected Files]
    D --> E[Read Current File Contents]
    E --> F[Build Generation Prompt]
    F --> G[LLM Generate]
    G --> H[Parse JSON Output]
    H --> I[Validate Payload Schema]
    I --> J[Validate Generated Scope]
    J --> K[Copy Project to Staging]
    K --> L[Apply Generated Payload]
    L --> M[Write New DSL]
    M --> N[Write Hidden Tests]
    N --> O[Validate Project]
    O --> P{All Passed?}
    P -->|Yes| Q[Commit to Working Project]
    P -->|No| R[Deterministic Repair]
    R --> S{All Passed?}
    S -->|Yes| Q
    S -->|No| T{Repair Attempts Left?}
    T -->|Yes| U[LLM Repair Generate]
    U --> V[Apply Repair Payload]
    V --> W[Deterministic Repair Again]
    W --> X[Final Validation]
    X --> Y{All Passed?}
    Y -->|Yes| Q
    Y -->|No| Z[Record Failure]
    Q --> AA[Create Snapshot]
    Z --> AA
    AA --> AB[Compare Manifests]
    AB --> AC[Build Metrics]
    AC --> AD[Append to JSONL]
```

## Dependency Extraction

```mermaid
flowchart LR
    A[Structural Diff] --> B["For each changed path:"]
    B --> C{"Prefix matches a rule?"}
    C -->|Yes| D[Add rule's artifacts to affected set]
    C -->|No| E[Skip]
    D --> F[Return sorted affected files]
    E --> F
```

The dependency rules are a manually defined dictionary mapping DSL dotted-paths to lists of source files:

```python
{
    "entities.Task.fields": {
        "artifacts": ["app/models.py", "app/schemas.py", ...]
    },
    "actions.create_task": {
        "artifacts": ["app/schemas.py", "app/service.py", ...]
    },
    ...
}
```

When a DSL diff entry has a path starting with a rule prefix, all files in that rule's `artifacts` list become affected.

## Impact Analysis

```mermaid
flowchart TD
    A[DSL Diff: list of changes] --> B[For each change]
    B --> C[For each dependency rule]
    C --> D{change.path starts with rule.prefix?}
    D -->|Yes| E[Union rule.artifacts into affected set]
    D -->|No| F[Next rule]
    E --> G[All rules checked]
    F --> G
    G --> H[Sort affected set]
    H --> I[Validate: all affected files in allowed_files]
    I --> J[Return affected_files]
```

## Selective Regeneration

The core innovation is that only affected files are sent to the LLM, not the entire codebase.

```mermaid
sequenceDiagram
    participant Note as Notebook
    participant ER as experiment_runner
    participant CB as context_builder
    participant LLM as llm_runner
    participant OP as output_parser
    participant P as patching
    participant V as validation
    participant DR as deterministic_repair

    Note->>ER: run_selective_change(change)
    ER->>ER: Apply DSL patch, compute diff
    ER->>ER: Resolve affected files
    ER->>CB: build_generation_prompt(...)
    CB-->>ER: Prompt string
    ER->>LLM: generate_with_qwen(prompt)
    LLM-->>ER: GenerationResult
    ER->>OP: extract_json_object(text)
    OP-->>ER: payload dict
    ER->>OP: validate_payload_schema(payload)
    ER->>OP: validate_generated_scope(payload)
    ER->>P: apply_generated_payload(staging, payload)
    ER->>V: validate_project(staging)
    V-->>ER: validation result
    alt Validation failed
        ER->>DR: run_deterministic_local_repair(staging)
        DR-->>ER: repair report
        ER->>V: validate_project(staging)
        V-->>ER: validation result
    end
    ER->>ER: Create snapshot, compare manifests
    ER->>ER: Build metrics
    ER-->>Note: Result dict
```

## Artifact Validation

```mermaid
flowchart TD
    A[Generated Payload] --> B[Schema Validation]
    B --> C{Valid JSON schema?}
    C -->|No| D[Raise ValueError]
    C -->|Yes| E[Scope Validation]
    E --> F{All paths in allowlist?}
    F -->|No| G[Raise ValueError]
    F -->|Yes| H{No path traversal?}
    H -->|No| I[Raise ValueError]
    H -->|Yes| J{No absolute paths?}
    J -->|No| K[Raise ValueError]
    J -->|Yes| L{No duplicate paths?}
    L -->|No| M[Raise ValueError]
    L -->|Yes| N{Correct change_id?}
    N -->|No| O[Raise ValueError]
    N -->|Yes| P[Payload valid]
```

## LLM Generation

```mermaid
flowchart TD
    A[system_prompt + user_prompt] --> B[Apply chat template]
    B --> C[Tokenize]
    C --> D{prompt_tokens > max_context_tokens?}
    D -->|Yes| E[Raise ValueError]
    D -->|No| F{prompt + new > model context length?}
    F -->|Yes| G[Raise ValueError]
    F -->|No| H[Move to GPU]
    H --> I[Reset peak memory stats]
    I --> J[model.generate]
    J --> K[Decode output tokens]
    K --> L[Record peak GPU memory]
    L --> M[Clean up: del, gc.collect, empty_cache]
    M --> N[Return GenerationResult]
```

## Metrics Collection

```mermaid
flowchart TD
    A[Change metadata] --> B[Generation results]
    B --> C[Validation results]
    C --> D[File diffs]
    D --> E[Timing data]
    E --> F[build_change_metrics]
    F --> G[Classify failure category]
    G --> H[Metrics dict]
    H --> I[Append to JSONL file]
```

Each metrics record contains:

| Category | Fields |
|----------|--------|
| Identity | `change_id`, `version`, `change_title`, `experiment`, `project`, `strategy` |
| Input | `model_id`, `quantization`, `seed`, `changed_dsl_elements`, `affected_files_count` |
| Token usage | `initial_prompt_tokens`, `initial_output_tokens`, `initial_total_tokens`, `repair_prompt_tokens`, `repair_output_tokens`, `repair_total_tokens`, `total_tokens` |
| Timing | `generation_seconds`, `repair_seconds`, `total_duration_seconds` |
| Memory | `peak_gpu_memory_mb` |
| Outcomes | `first_pass_acceptance`, `accepted_after_local_repair`, `accepted_after_llm_repair`, `final_acceptance` |
| Stage results | `compile_pass`, `ruff_pass`, `unit_pass`, `integration_pass`, `regression_pass`, `hidden_tests_pass` |
| Classification | `failure_category` |

## Model Loading Architecture

### Discovery Phase

The model discovery process uses `debug_kaggle_models()` to locate candidate models on the host system. It searches well-known paths (e.g., `/kaggle/input/`) and applies a multi-stage validation pipeline before accepting a candidate:

```mermaid
flowchart TD
    A[debug_kaggle_models] --> B[Scan candidate directories]
    B --> C{config.json present?}
    C -->|No| D[Skip — not a model dir]
    C -->|Yes| E[Read quantize_config.json]
    E --> F{quant_method present?}
    F -->|No| G[Skip — unquantized]
    F -->|Yes| H{quant_method in allowed set?}
    H -->|No| I[Skip — unknown quant]
    H -->|Yes| J[Tokenizer Validation]
    J --> K{tokenizer.json or tokenizer.model?}
    K -->|No| L[Skip — no tokenizer]
    K -->|Yes| M{GGUF file present?}
    M -->|Yes| N[Reject — GGUF not supported by transformers]
    M -->|No| O[Compute discovery score]
    O --> P[Sort candidates by score descending]
    P --> Q[Return top candidate path]
```

### Scoring

Each valid candidate is scored by path-keyword matching to select the best model when multiple are available:

| Criterion | Points | Rationale |
|-----------|--------|-----------|
| Path contains `qwen2.5-coder` | +50 | Primary target model |
| Path contains `qwen2` | +30 | Secondary Qwen match |
| Path contains `qwen` | +10 | Tertiary Qwen match |
| Path contains `gptq` | +40 | GPTQ quantized (preferred) |
| Path contains `int4` or `int-4` | +30 | INT4 variant |
| Path contains `awq` | +35 | AWQ quantized |
| Path contains `7b-instruct` | +15 | Instruct variant |
| Path contains `coder` | +10 | Coder variant |
| Path contains `7b` | +5 | 7B parameter size |
| Numeric version directory in path | +3 | Versioned model |
| No tokenizer files found | −50 | Hard disqualifier |
| GGUF directory | −∞ | Hard reject |

### Loading Phase

```mermaid
flowchart TD
    A[load_model] --> B[Print system info]
    B -->     C[find_kaggle_model — discover candidate]
    C --> D{candidate found?}
    D -->|No| E[debug_kaggle_models — diagnostic output]
    E --> F[Raise FileNotFoundError]
    D -->|Yes| G[Use discovered path]
    G --> H[detect_gptq_backend]
    H --> I{quant_method in quantize_config.json?}
    I -->|gptq/marlin| J{gptqmodel installed?}
    J -->|Yes| K[Load with GPTQModel.load]
    J -->|No| L{auto_gptq installed?}
    L -->|Yes| M[Load with AutoGPTQForCausalLM]
    L -->|No| N[Load with AutoModelForCausalLM]
    I -->|not found| O{quant_method in config.json?}
    O -->|gptq/marlin| J
    O -->|not found| P[No GPTQ detected]
    P --> Q[Load with BitsAndBytesConfig NF4]
    K --> R[model.eval]
    M --> R
    N --> R
    Q --> R
    R --> S[Print memory stats]
    S --> T[Return tokenizer, model]
```

### Key Notes

- `debug_kaggle_models()` prints a diagnostic table of all scanned directories, their quant methods, tokenizer availability, and computed scores — useful for debugging model-not-found issues on Kaggle/Colab.
- GGUF files (e.g., `.gguf` quantized models) are explicitly rejected because the HuggingFace `transformers` library does not load them directly; they require `llama.cpp` or `gguf`-specific tooling.
- Tokenizer validation ensures `tokenizer.json` (fast tokenizer) or `tokenizer.model` (SentencePiece) exists. Without either, the model is skipped even if weights are present.
- When `gptqmodel` is installed, it is preferred over `auto-gptq` because it supports a wider range of GPTQ kernels and has better error messages.

## Validation Pipeline

```mermaid
flowchart TD
    A[validate_project] --> B[ast_parse]
    B --> C{passed?}
    C -->|No| Z[all_passed = false]
    C -->|Yes| D[compile]
    D --> E{passed?}
    E -->|No| Z
    E -->|Yes| F[ruff]
    F --> G[unit tests]
    G --> H{passed?}
    H -->|No| Z
    H -->|Yes| I[integration tests]
    I --> J{passed?}
    J -->|No| Z
    J -->|Yes| K[regression tests]
    K --> L[hidden tests]
    L --> M[all_passed = all stages passed]
```

Note: `ast_parse`, `compile`, `unit`, and `integration` cause early termination on failure. `ruff`, `regression`, and `hidden` always run.

## Deterministic Repair Flow

```mermaid
flowchart TD
    A[run_deterministic_local_repair] --> B[ruff check --fix]
    B --> C[ruff check]
    C --> D[Extract F821 undefined names]
    D --> E{Undefined name in SAFE_MISSING_IMPORTS?}
    E -->|Yes| F[Insert import at top of file]
    E -->|No| G[Skip]
    F --> H[More names?]
    G --> H
    H -->|Yes| E
    H -->|No| I[ruff check --fix]
    I --> J[Return repair report]
```
