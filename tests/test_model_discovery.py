# test_model_discovery.py — Unit tests for model discovery logic in llm_runner.py.

import json
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from selective_regeneration.llm_runner import (
    _has_tokenizer_files,
    _score_candidate,
    find_kaggle_model,
)


def _make_model_dir(
    base: Path,
    rel: str,
    *,
    has_config: bool = True,
    has_tokenizer: bool = True,
    quantize_config: dict | None = None,
    config_quant: dict | None = None,
    extra_files: list[str] | None = None,
) -> Path:
    model_dir = base / rel
    model_dir.mkdir(parents=True, exist_ok=True)

    if has_config:
        cfg: dict = {}
        if config_quant:
            cfg["quantization_config"] = config_quant
        (model_dir / "config.json").write_text(
            json.dumps(cfg), encoding="utf-8"
        )

    if has_tokenizer:
        (model_dir / "tokenizer.json").write_text(
            "{}", encoding="utf-8"
        )

    if quantize_config is not None:
        (model_dir / "quantize_config.json").write_text(
            json.dumps(quantize_config), encoding="utf-8"
        )

    for fname in extra_files or []:
        (model_dir / fname).write_text(
            "", encoding="utf-8"
        )

    return model_dir


class TestHasTokenizerFiles:
    def test_returns_true_when_tokenizer_json_exists(
        self, tmp_path: Path
    ) -> None:
        d = tmp_path / "model"
        d.mkdir()
        (d / "tokenizer.json").write_text("{}")
        assert _has_tokenizer_files(d) is True

    def test_returns_true_when_tokenizer_config_exists(
        self, tmp_path: Path
    ) -> None:
        d = tmp_path / "model"
        d.mkdir()
        (d / "tokenizer_config.json").write_text("{}")
        assert _has_tokenizer_files(d) is True

    def test_returns_true_when_tokenizer_model_exists(
        self, tmp_path: Path
    ) -> None:
        d = tmp_path / "model"
        d.mkdir()
        (d / "tokenizer.model").write_text("")
        assert _has_tokenizer_files(d) is True

    def test_returns_false_when_no_tokenizer(
        self, tmp_path: Path
    ) -> None:
        d = tmp_path / "model"
        d.mkdir()
        assert _has_tokenizer_files(d) is False


class TestScoreCandidate:
    def test_qwen25_coder_gptq_int4_in_numeric_dir(
        self, tmp_path: Path
    ) -> None:
        model_dir = (
            tmp_path
            / "models"
            / "qwen-lm"
            / "qwen2.5-coder"
            / "transformers"
            / "7b-instruct-gptq-int4"
            / "1"
        )
        model_dir.mkdir(parents=True)
        (model_dir / "tokenizer.json").write_text("{}")

        score, reasons = _score_candidate(model_dir)
        assert score >= 100
        assert reasons == []

    def test_regular_transformers_model(
        self, tmp_path: Path
    ) -> None:
        model_dir = (
            tmp_path
            / "models"
            / "qwen-lm"
            / "qwen2.5-coder"
            / "transformers"
            / "7b-instruct"
        )
        model_dir.mkdir(parents=True)
        (model_dir / "tokenizer.json").write_text("{}")

        score, reasons = _score_candidate(model_dir)
        assert score > 0
        assert "gptq" not in " ".join(reasons).lower()

    def test_gguf_rejected(
        self, tmp_path: Path
    ) -> None:
        model_dir = (
            tmp_path / "models" / "something-gguf"
        )
        model_dir.mkdir(parents=True)
        (model_dir / "tokenizer.json").write_text("{}")

        score, reasons = _score_candidate(model_dir)
        assert score == -1
        assert any("GGUF" in r for r in reasons)

    def test_missing_tokenizer_rejected(
        self, tmp_path: Path
    ) -> None:
        model_dir = (
            tmp_path
            / "models"
            / "qwen-lm"
            / "qwen2.5-coder"
            / "transformers"
            / "7b-instruct-gptq-int4"
        )
        model_dir.mkdir(parents=True)

        score, reasons = _score_candidate(model_dir)
        assert score == -1
        assert any("tokenizer" in r.lower() for r in reasons)

    def test_no_matching_keywords_zero_score(
        self, tmp_path: Path
    ) -> None:
        model_dir = tmp_path / "models" / "unrelated"
        model_dir.mkdir(parents=True)
        (model_dir / "tokenizer.json").write_text("{}")

        score, reasons = _score_candidate(model_dir)
        assert score == 0
        assert any(
            "keywords" in r.lower() for r in reasons
        )


class TestFindKaggleModel:
    def test_discovers_gptq_in_numeric_version_dir(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct-gptq-int4/1",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert result.name == "1"
        assert (result / "config.json").exists()

    def test_discovers_regular_transformers_model(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert result.name == "7b-instruct"

    def test_returns_none_for_empty_directory(
        self, tmp_path: Path
    ) -> None:
        result = find_kaggle_model(str(tmp_path))
        assert result is None

    def test_returns_none_for_nonexistent_path(
        self, tmp_path: Path
    ) -> None:
        result = find_kaggle_model(
            str(tmp_path / "nonexistent")
        )
        assert result is None

    def test_rejects_gguf_candidate(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/some-model-gguf",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is None

    def test_rejects_missing_tokenizer(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct-gptq-int4",
            has_tokenizer=False,
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is None

    def test_multiple_candidates_picks_best(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/some-model",
        )
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct-gptq-int4/1",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert "7b-instruct-gptq-int4" in str(result)
        assert result.name == "1"

    def test_datasets_path_also_searched(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "datasets/user/qwen2.5-coder/transformers/7b-instruct",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert result.name == "7b-instruct"

    def test_prefers_gptq_over_plain_transformers(
        self, tmp_path: Path
    ) -> None:
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct",
        )
        _make_model_dir(
            tmp_path,
            "models/qwen-lm/qwen2.5-coder/transformers/7b-instruct-gptq-int4",
        )

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert "gptq" in str(result).lower()

    def test_exact_target_path_discovered(
        self, tmp_path: Path
    ) -> None:
        target = (
            "models/qwen-lm/qwen2.5-coder"
            "/transformers/7b-instruct-gptq-int4/1"
        )
        _make_model_dir(tmp_path, target)

        result = find_kaggle_model(str(tmp_path))
        assert result is not None
        assert result.name == "1"
        assert "7b-instruct-gptq-int4" in str(result)
        assert "qwen2.5-coder" in str(result)
