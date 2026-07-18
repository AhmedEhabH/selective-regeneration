# Kaggle Deployment Guide

Step-by-step guide for running the Selective Regeneration Pipeline on Kaggle.

## Prerequisites

- Kaggle account with GPU access
- GPU accelerator enabled (T4, P100, or better)
- Model: `qwen-lm/qwen2.5-coder` variant `7b-instruct-gptq-int4`

## Setup Steps

### 1. Create Kaggle Notebook

1. Go to Kaggle > Code > New Notebook
2. Under **Settings**, enable **GPU** accelerator
3. Set internet to **Off** (all dependencies are installed from pip cache)

### 2. Attach the Model

1. In the notebook editor, click **Add Data** (right panel)
2. Search for `qwen2.5-coder`
3. Add the model: `qwen-lm/qwen2.5-coder`
4. Select variant: `7b-instruct-gptq-int4` (Transformers format)
5. The model will be mounted at a path like:
   `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/7b-instruct-gptq-int4/1`

### 3. Upload Package Files

Upload these to the notebook's working directory:

- `selective_regeneration/` (entire package directory)
- `notebooks/qwen-selective-regeneration-v2.ipynb` (rename to your notebook name)

### 4. Run the Notebook

Run all cells in order. The notebook will:

1. Check hardware (Cell 1)
2. Install dependencies (Cells 2-3)
3. Set up paths (Cell 4)
4. Configure experiment (Cell 5)
5. Import modules (Cell 6)
6. Create pilot project (Cell 7)
7. Validate initial project (Cell 8)
8. Save snapshot (Cell 9)
9. Run model diagnostics and load model (Cell 10)
10. Smoke test (Cell 11)
11. Run 3 requirement changes (Cells 12-21)
12. Summary and export (Cells 22-24)

## Troubleshooting

### "No valid model found" Error

If Cell 10 fails with a `FileNotFoundError`:

1. Check that the model is attached (Add Data panel)
2. Run `debug_kaggle_models()` to see what was discovered
3. The error message will list:
   - Paths searched
   - Candidates found and why they were rejected
   - Instructions to attach the model

### OOM (Out of Memory)

The Qwen2.5-Coder 7B GPTQ INT4 model requires ~4-5 GB VRAM. If you get OOM:

1. Ensure GPU is enabled (Settings > GPU)
2. Try a T4 (16 GB) or P100 (16 GB) GPU
3. Reduce `max_context_tokens` in `ExperimentConfig`

### Import Errors

If you see `ModuleNotFoundError: No module named 'selective_regeneration'`:

1. Ensure the `selective_regeneration/` directory is in the notebook working directory
2. Check that `selective_regeneration/__init__.py` exists
3. Cell 4 should print the module path that was added

### Package Installation Failures

If pip install fails (Cell 2):

1. Ensure internet is enabled for the first run
2. After first run, you can disable internet (packages are cached)
3. If specific packages fail, check Kaggle's pre-installed packages

## Model Discovery Behavior

The `find_kaggle_model()` function:

1. Recursively searches all paths under `/kaggle/input`
2. Finds all `config.json` files
3. Scores each candidate directory based on path keywords:
   - Qwen2.5-Coder: +50
   - Qwen2: +30
   - Qwen: +10
   - GPTQ: +40
   - INT4 / INT-4: +30
   - AWQ: +35
   - 7b-instruct: +15
   - Coder: +10
   - 7b: +5
   - Numeric version dir: +3
   - No tokenizer files: −50 (hard reject)
   - GGUF directory: rejected
4. Rejects GGUF directories
5. Rejects candidates without tokenizer files
6. Returns the highest-scoring valid candidate

The `debug_kaggle_models()` function prints detailed diagnostics before model loading.
