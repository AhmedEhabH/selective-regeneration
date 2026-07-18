# llm_runner.py — Model loading (GPTQ/BNB), generation, and memory management.

from __future__ import annotations

import gc
import json
import time
from dataclasses import dataclass
from pathlib import Path


_TOKENIZER_FILES = {
    "tokenizer.json",
    "tokenizer_config.json",
    "tokenizer.model",
}


@dataclass
class GenerationResult:
    """Result of a single LLM generation call.

    Attributes:
        text: The generated text.
        prompt_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens generated.
        total_tokens: Sum of prompt and output tokens.
        duration_seconds: Wall-clock generation time.
        peak_gpu_memory_mb: Peak GPU memory used during generation.
        finish_reason: "eos" or "max_new_tokens".
    """
    text: str
    prompt_tokens: int
    output_tokens: int
    total_tokens: int
    duration_seconds: float
    peak_gpu_memory_mb: float
    finish_reason: str


def _bytes_to_gb(n: int) -> float:
    return round(n / 1024**3, 2)


def _print_system_info() -> None:
    import torch

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        vram_total = _bytes_to_gb(props.total_memory)
        vram_free = _bytes_to_gb(
            torch.cuda.mem_get_info(0)[0]
        )
        print(f"GPU:              {gpu_name}")
        print(f"VRAM total:       {vram_total} GB")
        print(f"VRAM free:        {vram_free} GB")
    else:
        print("GPU:              none (CPU only)")

    try:
        import psutil

        ram = psutil.virtual_memory()
        print(f"RAM total:        {_bytes_to_gb(ram.total)} GB")
        print(f"RAM available:    {_bytes_to_gb(ram.available)} GB")
    except ImportError:
        print("RAM:              (psutil not installed)")


def _has_tokenizer_files(model_dir: Path) -> bool:
    return any(
        (model_dir / f).exists() for f in _TOKENIZER_FILES
    )


def _score_candidate(
    model_dir: Path,
) -> tuple[int, list[str]]:
    path_str = str(model_dir).lower()
    dir_name = model_dir.name.lower()
    rejection_reasons: list[str] = []

    if "gguf" in dir_name or ".gguf" in path_str:
        rejection_reasons.append("GGUF directory rejected")
        return -1, rejection_reasons

    if not _has_tokenizer_files(model_dir):
        rejection_reasons.append(
            "No tokenizer files found "
            f"(checked: {', '.join(_TOKENIZER_FILES)})"
        )
        return -1, rejection_reasons

    score = 0

    if "qwen2.5-coder" in path_str:
        score += 50
    elif "qwen2" in path_str:
        score += 30
    elif "qwen" in path_str:
        score += 20

    if "gptq" in path_str:
        score += 40

    if "int4" in path_str or "int-4" in path_str:
        score += 30

    if "awq" in path_str:
        score += 35

    if "7b-instruct" in path_str or "7b_instruct" in path_str:
        score += 15

    if "coder" in path_str:
        score += 10

    if "7b" in path_str:
        score += 5

    parts = model_dir.parts
    for part in parts:
        if part.isdigit():
            score += 3
            break

    if score == 0:
        rejection_reasons.append(
            "No matching model keywords found in path"
        )

    return score, rejection_reasons


def find_kaggle_model(
    search_root: str = "/kaggle/input",
) -> Path | None:
    """Search recursively for the best Qwen model under the given root.

    Scores candidates by path keywords, validates tokenizer files,
    rejects GGUF directories. Returns the highest-scoring valid path.
    """
    search_root_path = Path(search_root)
    if not search_root_path.exists():
        return None

    candidates: list[tuple[int, Path, list[str]]] = []

    for config_path in search_root_path.rglob("config.json"):
        model_dir = config_path.parent
        score, reasons = _score_candidate(model_dir)
        candidates.append((score, model_dir, reasons))

    candidates.sort(key=lambda c: c[0], reverse=True)

    for score, model_dir, reasons in candidates:
        cfg = model_dir / "config.json"
        if cfg.exists() and score > 0:
            return model_dir

    return None


def debug_kaggle_models(
    search_root: str = "/kaggle/input",
) -> None:
    """Print detailed diagnostics of all discovered model candidates.

    Shows paths, scores, tokenizer presence, quantization config,
    and rejection reasons for each candidate found under search_root.
    """
    search_root_path = Path(search_root)

    print("=" * 70)
    print("KAGGLE MODEL DISCOVERY DIAGNOSTICS")
    print("=" * 70)

    if not search_root_path.exists():
        print(f"\nSearch root does not exist: {search_root}")
        return

    print(f"\nTop-level contents of {search_root}:")
    try:
        for entry in sorted(search_root_path.iterdir()):
            prefix = "  [dir] " if entry.is_dir() else "  [file]"
            print(f"{prefix} {entry.name}")
    except PermissionError:
        print("  (permission denied)")

    print(f"\nAll discovered config.json files:")
    config_files = list(search_root_path.rglob("config.json"))
    if not config_files:
        print("  (none found)")
    else:
        for cf in config_files:
            print(f"  {cf}")

    print(f"\nCandidate analysis:")
    candidates: list[tuple[int, Path, list[str]]] = []
    for config_path in config_files:
        model_dir = config_path.parent
        score, reasons = _score_candidate(model_dir)
        candidates.append((score, model_dir, reasons))

    candidates.sort(key=lambda c: c[0], reverse=True)

    for score, model_dir, reasons in candidates:
        print(f"\n  Path: {model_dir}")
        print(f"  Score: {score}")

        has_tok = _has_tokenizer_files(model_dir)
        print(f"  Has tokenizer: {has_tok}")

        quant_cfg = model_dir / "quantize_config.json"
        if quant_cfg.exists():
            try:
                with quant_cfg.open("r", encoding="utf-8") as f:
                    qdata = json.load(f)
                print(
                    f"  quantize_config.json: "
                    f"{json.dumps(qdata, indent=4)}"
                )
            except (json.JSONDecodeError, OSError) as exc:
                print(
                    f"  quantize_config.json: (error reading: {exc})"
                )
        else:
            print("  quantize_config.json: (not found)")

        cfg_path = model_dir / "config.json"
        if cfg_path.exists():
            try:
                with cfg_path.open("r", encoding="utf-8") as f:
                    cdata = json.load(f)
                quant_info = cdata.get(
                    "quantization_config", {}
                )
                if quant_info:
                    print(
                        f"  config.json quantization_config: "
                        f"{json.dumps(quant_info, indent=4)}"
                    )
                else:
                    print(
                        "  config.json quantization_config: (empty)"
                    )
            except (json.JSONDecodeError, OSError):
                print("  config.json: (error reading)")

        if reasons:
            print(f"  Rejection reasons: {'; '.join(reasons)}")

    valid = [
        c for c in candidates if c[0] > 0
    ]
    print(f"\nValid candidates: {len(valid)}")

    if valid:
        best = valid[0]
        print(f"Best candidate: {best[1]} (score={best[0]})")
    else:
        print("No valid candidates found.")

    for model_subdir in ("models", "datasets"):
        base = search_root_path / model_subdir
        if base.exists():
            print(f"\nDirectory tree under {base}:")
            _print_limited_tree(base, max_depth=4)

    print("=" * 70)


def _print_limited_tree(
    root: Path,
    max_depth: int = 4,
    current_depth: int = 0,
) -> None:
    if current_depth >= max_depth:
        return
    try:
        entries = sorted(root.iterdir())
    except PermissionError:
        return
    indent = "  " * (current_depth + 1)
    for entry in entries[:30]:
        if entry.is_dir():
            print(f"{indent}{entry.name}/")
            _print_limited_tree(
                entry, max_depth, current_depth + 1
            )
        else:
            print(f"{indent}{entry.name}")


def detect_gptq_backend(
    model_dir: Path,
) -> str | None:
    """Detect the GPTQ backend for a model directory.

    Reads quantize_config.json and config.json to determine the
    quantization method. Returns the backend name or None if not GPTQ.
    """
    quant_cfg_path = model_dir / "quantize_config.json"

    if quant_cfg_path.exists():
        try:
            with quant_cfg_path.open(
                "r", encoding="utf-8"
            ) as f:
                quant_cfg = json.load(f)
        except (json.JSONDecodeError, OSError):
            quant_cfg = {}

        quant_method = str(
            quant_cfg.get("quant_method", "")
        ).lower()

        if quant_method in ("gptq", "marlin"):
            try:
                import gptqmodel  # noqa: F401

                return "gptqmodel"
            except ImportError:
                pass

            try:
                import auto_gptq  # noqa: F401

                return "auto_gptq"
            except ImportError:
                pass

            if quant_method == "marlin":
                return "transformers_marlin"

            return "transformers_gptq"

    config_path = model_dir / "config.json"
    if config_path.exists():
        try:
            with config_path.open(
                "r", encoding="utf-8"
            ) as f:
                config = json.load(f)
            quant_method = str(
                config.get("quantization_config", {}).get(
                    "quant_method", ""
                )
            ).lower()
            if quant_method in ("gptq", "marlin"):
                try:
                    import gptqmodel  # noqa: F401

                    return "gptqmodel"
                except ImportError:
                    pass
                try:
                    import auto_gptq  # noqa: F401

                    return "auto_gptq"
                except ImportError:
                    pass
                return "transformers_gptq"
        except (json.JSONDecodeError, OSError):
            pass

    return None


def load_model(
    model_path: str | None = None,
    model_source: str = "kaggle",
    quantization_backend: str = "auto",
    seed: int = 42,
) -> tuple:
    """Load a tokenizer and model from a Kaggle model directory.

    Resolves the model path, detects quantization, loads with the
    appropriate backend (GPTQ primary, BNB fallback), and returns
    (tokenizer, model). Attaches metadata attributes to the model.
    """
    import torch
    from transformers import set_seed

    set_seed(seed)

    _print_system_info()

    if torch.cuda.is_available():
        gpu_props = torch.cuda.get_device_properties(0)
        vram_total = gpu_props.total_memory
    else:
        vram_total = 0

    resolved_path: Path | None = None
    search_root = "/kaggle/input"

    if model_path is not None:
        candidate = Path(model_path)
        if candidate.exists() and (
            candidate / "config.json"
        ).exists():
            resolved_path = candidate
    if resolved_path is None and model_source == "kaggle":
        resolved_path = find_kaggle_model(search_root)

    if resolved_path is None:
        _raise_model_not_found(
            model_path=model_path,
            search_root=search_root,
        )

    model_dir = resolved_path
    print(f"\nSelected model path: {model_dir}")

    gptq_backend = None
    used_quantization = "none"

    if quantization_backend in ("auto", "gptq"):
        gptq_backend = detect_gptq_backend(model_dir)

    if gptq_backend is not None:
        print(f"Quantization type:  GPTQ ({gptq_backend})")
        tokenizer, model = _load_gptq_model(
            model_dir,
            gptq_backend,
            seed,
        )
        used_quantization = f"gptq_{gptq_backend}"
    elif quantization_backend in ("auto", "bnb"):
        print(
            "Quantization type:  BNB 4-bit (fallback)"
        )
        tokenizer, model = _load_bnb_model(
            model_dir,
            seed,
        )
        used_quantization = "bnb_nf4_4bit"
    else:
        raise ValueError(
            f"Unsupported quantization_backend: "
            f"{quantization_backend!r}. "
            f"Use 'auto', 'gptq', or 'bnb'."
        )

    model.eval()

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    print(f"\nQuantization used: {used_quantization}")
    print("Model loaded successfully.")
    _print_memory_stats()

    model._used_quantization = used_quantization  # type: ignore[attr-defined]
    model._model_source = model_source  # type: ignore[attr-defined]
    model._resolved_path = str(model_dir)  # type: ignore[attr-defined]

    return tokenizer, model


def _raise_model_not_found(
    model_path: str | None,
    search_root: str,
) -> None:
    search_root_path = Path(search_root)
    searched = [str(search_root_path)]

    candidates_found: list[str] = []
    rejection_reasons: list[str] = []

    if search_root_path.exists():
        for config_path in search_root_path.rglob(
            "config.json"
        ):
            model_dir = config_path.parent
            score, reasons = _score_candidate(model_dir)
            candidates_found.append(str(model_dir))
            if reasons:
                rejection_reasons.append(
                    f"  {model_dir}: {'; '.join(reasons)}"
                )

    msg_parts = [
        "No valid model found.",
        "",
        "Search paths:",
    ]
    for s in searched:
        msg_parts.append(f"  - {s}")

    if candidates_found:
        msg_parts.append("")
        msg_parts.append("Candidate config.json directories found:")
        for c in candidates_found:
            msg_parts.append(f"  - {c}")

    if rejection_reasons:
        msg_parts.append("")
        msg_parts.append("Rejection reasons:")
        for r in rejection_reasons:
            msg_parts.append(r)

    msg_parts.extend([
        "",
        "To attach the Kaggle model:",
        "  1. In the Kaggle notebook, click 'Add Data'.",
        "  2. Search for 'qwen2.5-coder'.",
        "  3. Add the model 'qwen-lm/qwen2.5-coder'",
        "     with variant '7b-instruct-gptq-int4'.",
        "  4. Ensure tokenizer files (tokenizer.json or",
        "     tokenizer_config.json) are present in the",
        "     model directory.",
        "",
        "To use a local model, set model_path to the",
        "directory containing config.json.",
    ])

    if model_path:
        msg_parts.extend([
            "",
            f"User-specified model_path was: {model_path}",
            f"Exists: {Path(model_path).exists()}",
        ])

    raise FileNotFoundError("\n".join(msg_parts))


def _load_gptq_model(
    model_dir: Path,
    backend: str,
    seed: int,
) -> tuple:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_dir),
        use_fast=True,
        trust_remote_code=True,
    )

    if backend == "gptqmodel":
        from gptqmodel import GPTQModel

        model = GPTQModel.load(
            str(model_dir),
            device_map="auto",
            trust_remote_code=True,
        )
        return tokenizer, model

    if backend == "auto_gptq":
        from auto_gptq import AutoGPTQForCausalLM

        model = AutoGPTQForCausalLM.from_quantized(
            str(model_dir),
            device_map="auto",
            use_safetensors=True,
            trust_remote_code=True,
        )
        return tokenizer, model

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    return tokenizer, model


def _load_bnb_model(
    model_dir: Path,
    seed: int,
) -> tuple:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_dir),
        use_fast=True,
        trust_remote_code=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        quantization_config=quantization_config,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    return tokenizer, model


def _print_memory_stats() -> None:
    import torch

    if torch.cuda.is_available():
        print(
            "Allocated GPU GB:",
            round(
                torch.cuda.memory_allocated() / 1024**3, 2
            ),
        )
        print(
            "Reserved GPU GB:",
            round(
                torch.cuda.memory_reserved() / 1024**3, 2
            ),
        )


def check_context_fit(
    prompt_tokens: int,
    max_new_tokens: int,
    max_context_tokens: int,
    model_context_length: int = 32768,
) -> None:
    """Validate that prompt + new tokens fit within context limits.

    Raises ValueError if the requested tokens exceed the model's
    max_position_embeddings or the configured max_context_tokens.
    """
    requested = prompt_tokens + max_new_tokens

    if requested > model_context_length:
        raise ValueError(
            f"Requested {requested} tokens "
            f"(prompt {prompt_tokens} + new {max_new_tokens}) "
            f"exceeds model context length "
            f"{model_context_length}."
        )

    if prompt_tokens > max_context_tokens:
        raise ValueError(
            f"Prompt contains {prompt_tokens} tokens, "
            f"above the configured limit "
            f"{max_context_tokens}."
        )


def generate_with_qwen(
    tokenizer,
    model,
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int = 4000,
    max_context_tokens: int = 8192,
) -> GenerationResult:
    """Run a single generation call with the Qwen model.

    Applies chat template, validates context, generates with greedy
    decoding, tracks peak GPU memory, and returns a GenerationResult.
    """
    import torch

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    rendered = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    model_inputs = tokenizer(
        rendered,
        return_tensors="pt",
        add_special_tokens=False,
    )

    prompt_tokens = int(
        model_inputs["input_ids"].shape[-1]
    )

    model_ctx = getattr(
        model.config,
        "max_position_embeddings",
        32768,
    )
    check_context_fit(
        prompt_tokens,
        max_new_tokens,
        max_context_tokens,
        model_context_length=model_ctx,
    )

    model_inputs = {
        key: value.to(model.device)
        for key, value in model_inputs.items()
    }

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()

    with torch.inference_mode():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    duration = time.perf_counter() - started

    new_tokens = generated_ids[
        :,
        model_inputs["input_ids"].shape[-1] :,
    ]

    output_tokens = int(new_tokens.shape[-1])

    text = tokenizer.decode(
        new_tokens[0],
        skip_special_tokens=True,
    )

    peak_mb = (
        torch.cuda.max_memory_allocated() / 1024**2
        if torch.cuda.is_available()
        else 0.0
    )

    finish_reason = (
        "max_new_tokens"
        if output_tokens >= max_new_tokens
        else "eos"
    )

    del generated_ids, new_tokens, model_inputs
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return GenerationResult(
        text=text,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        total_tokens=prompt_tokens + output_tokens,
        duration_seconds=duration,
        peak_gpu_memory_mb=peak_mb,
        finish_reason=finish_reason,
    )
