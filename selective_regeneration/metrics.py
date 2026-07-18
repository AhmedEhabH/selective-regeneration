# metrics.py — Experiment metrics collection and JSONL storage.

import json
from datetime import datetime, timezone

from selective_regeneration.validation import stage_passed


def build_change_metrics(
    *,
    change,
    strategy,
    experiment_name,
    project_name,
    model_id,
    seed,
    dsl_diff,
    affected_files,
    file_diff,
    initial_generation,
    repair_generation,
    first_validation,
    validation_after_local_repair,
    final_validation,
    first_pass_acceptance,
    local_repair_used,
    local_repair_actions,
    accepted_after_local_repair,
    start_time,
    end_time,
    quantization: str = "unknown",
) -> dict:
    """Build a complete metrics record for a single change run.

    Combines change metadata, generation results, validation outcomes,
    timing data, and file diffs into a single dict.
    """
    initial_tokens = (
        initial_generation.total_tokens
    )

    llm_repair_tokens = (
        repair_generation.total_tokens
        if repair_generation
        else 0
    )

    total_llm_tokens = (
        initial_tokens + llm_repair_tokens
    )

    actually_modified = sorted(
        set(
            file_diff["added"]
            + file_diff["modified"]
            + file_diff["deleted"]
        )
    )

    return {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "experiment": experiment_name,
        "project": project_name,
        "strategy": strategy,

        "change_id": change.change_id,
        "version": change.version,
        "change_title": change.title,

        "changed_dsl_elements": len(dsl_diff),
        "affected_files_count": len(affected_files),
        "affected_files": affected_files,
        "actually_modified_files": actually_modified,

        "model_id": model_id,
        "quantization": quantization,
        "seed": seed,

        "generation_calls": 1,
        "repair_calls": int(
            repair_generation is not None
        ),

        "local_repair_used": local_repair_used,
        "local_repair_actions": local_repair_actions,

        "initial_prompt_tokens": (
            initial_generation.prompt_tokens
        ),
        "initial_output_tokens": (
            initial_generation.output_tokens
        ),
        "initial_total_tokens": (
            initial_generation.total_tokens
        ),

        "repair_prompt_tokens": (
            repair_generation.prompt_tokens
            if repair_generation
            else 0
        ),
        "repair_output_tokens": (
            repair_generation.output_tokens
            if repair_generation
            else 0
        ),
        "repair_total_tokens": (
            repair_generation.total_tokens
            if repair_generation
            else 0
        ),

        "total_tokens": total_llm_tokens,

        "generation_seconds": (
            initial_generation.duration_seconds
        ),
        "repair_seconds": (
            repair_generation.duration_seconds
            if repair_generation
            else 0
        ),
        "total_duration_seconds": round(
            end_time - start_time, 3
        ),

        "peak_gpu_memory_mb": max(
            initial_generation.peak_gpu_memory_mb,
            (
                repair_generation.peak_gpu_memory_mb
                if repair_generation
                else 0
            ),
        ),

        "first_pass_acceptance": first_pass_acceptance,
        "accepted_after_local_repair": (
            accepted_after_local_repair
        ),
        "accepted_after_llm_repair": bool(
            repair_generation is not None
            and final_validation["all_passed"]
            and not accepted_after_local_repair
        ),

        "compile_pass": stage_passed(
            final_validation, "compile"
        ),
        "ruff_pass": stage_passed(
            final_validation, "ruff"
        ),
        "unit_pass": stage_passed(
            final_validation, "unit"
        ),
        "integration_pass": stage_passed(
            final_validation, "integration"
        ),
        "regression_pass": stage_passed(
            final_validation, "regression"
        ),
        "hidden_tests_pass": stage_passed(
            final_validation, "hidden"
        ),

        "final_acceptance": (
            final_validation["all_passed"]
        ),

        "failure_category": _classify_failure(
            first_pass_acceptance,
            local_repair_used,
            accepted_after_local_repair,
            repair_generation is not None,
            final_validation["all_passed"],
        ),
    }


def _classify_failure(
    first_pass,
    local_repair_used,
    accepted_after_local,
    llm_repair_used,
    final_passed,
) -> str:
    """Classify the failure mode based on which repair steps were used.

    Returns one of: first_pass_acceptance, accepted_after_local_repair,
    accepted_after_llm_repair, deterministic_repair_not_attempted,
    deterministic_repair_insufficient, llm_repair_insufficient, unknown_failure.
    """
    if final_passed:
        if first_pass:
            return "first_pass_acceptance"
        elif accepted_after_local:
            return "accepted_after_local_repair"
        else:
            return "accepted_after_llm_repair"

    if not first_pass and not local_repair_used:
        return "deterministic_repair_not_attempted"

    if (
        not first_pass
        and local_repair_used
        and not llm_repair_used
    ):
        return "deterministic_repair_insufficient"

    if llm_repair_used:
        return "llm_repair_insufficient"

    return "unknown_failure"


def append_metrics_jsonl(
    metrics_path,
    metrics_record,
) -> None:
    """Append a metrics record as a JSON line to the given file."""
    with metrics_path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                metrics_record,
                ensure_ascii=False,
            )
            + "\n"
        )


def load_metrics_jsonl(
    metrics_path,
) -> list[dict]:
    """Read all metrics records from a JSONL file.

    Returns a list of dicts, one per line. Silently skips empty files.
    """
    recorded_runs = []

    if metrics_path.exists():
        with metrics_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                line = line.strip()
                if line:
                    recorded_runs.append(
                        json.loads(line)
                    )

    return recorded_runs
