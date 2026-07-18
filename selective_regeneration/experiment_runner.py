# experiment_runner.py — Full pipeline orchestration for a single change.

import shutil
import time
from pathlib import Path

from selective_regeneration.change_model import RequirementChange
from selective_regeneration.context_builder import (
    SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    build_generation_prompt,
    build_repair_prompt,
)
from selective_regeneration.dependency import (
    resolve_affected_files,
)
from selective_regeneration.deterministic_repair import (
    run_deterministic_local_repair,
)
from selective_regeneration.diff import structural_diff
from selective_regeneration.dsl import (
    apply_dsl_patch,
    read_yaml,
    write_yaml,
)
from selective_regeneration.llm_runner import (
    generate_with_qwen,
)
from selective_regeneration.metrics import (
    build_change_metrics,
    append_metrics_jsonl,
)
from selective_regeneration.output_parser import (
    extract_json_object,
    validate_generated_scope,
    validate_payload_schema,
)
from selective_regeneration.patching import (
    apply_generated_payload,
    read_selected_files,
    write_files,
)
from selective_regeneration.snapshots import (
    compare_manifests,
    create_snapshot,
)
from selective_regeneration.validation import (
    validate_project,
)


def run_selective_change(
    *,
    project_dir: Path,
    change: RequirementChange,
    dependency_rules: dict,
    tokenizer,
    model,
    config,
    results_path: Path | None = None,
    snapshots_dir: Path | None = None,
) -> dict:
    """Run the complete selective regeneration pipeline for one change.

    Steps: DSL patch -> diff -> affected files -> LLM generate -> parse ->
    validate -> deterministic repair -> optional LLM repair -> snapshot ->
    commit -> metrics. Returns a result dict with all outcomes.
    """
    start_time = time.perf_counter()

    old_dsl = read_yaml(project_dir / "dsl.yaml")

    new_dsl = apply_dsl_patch(
        old_dsl,
        change.dsl_patch,
    )

    dsl_diff = structural_diff(old_dsl, new_dsl)

    affected_files = resolve_affected_files(
        dsl_diff,
        dependency_rules,
    )

    if not affected_files:
        raise RuntimeError(
            f"No affected files resolved for {change.change_id}"
        )

    disallowed = (
        set(affected_files) - set(change.allowed_files)
    )

    if disallowed:
        raise RuntimeError(
            f"Disallowed impacted files: {disallowed}"
        )

    current_files = read_selected_files(
        project_dir,
        affected_files,
    )

    prompt = build_generation_prompt(
        change=change,
        old_dsl=old_dsl,
        new_dsl=new_dsl,
        dsl_diff=dsl_diff,
        affected_files=affected_files,
        file_contents=current_files,
    )

    initial_generation = generate_with_qwen(
        tokenizer=tokenizer,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        max_new_tokens=config.max_new_tokens,
        max_context_tokens=config.max_context_tokens,
    )

    payload = extract_json_object(
        initial_generation.text
    )

    validate_payload_schema(payload)

    validate_generated_scope(
        payload,
        change,
        affected_files,
    )

    staging_dir = (
        project_dir.parent
        / "runtime"
        / f"staging_{change.change_id.lower()}"
    )

    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    shutil.copytree(
        project_dir,
        staging_dir,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "*.pyc",
        ),
    )

    apply_generated_payload(staging_dir, payload)

    write_yaml(staging_dir / "dsl.yaml", new_dsl)

    write_files(
        staging_dir,
        change.hidden_test_files,
    )

    first_validation = validate_project(
        staging_dir,
        test_timeout=config.test_timeout_seconds,
    )

    first_pass_acceptance = (
        first_validation["all_passed"]
    )

    repair_generation = None
    local_repair_used = False
    local_repair_report = {"actions": []}

    if not first_validation["all_passed"]:
        local_repair_used = True

        local_repair_report = (
            run_deterministic_local_repair(
                staging_dir,
                test_timeout=config.test_timeout_seconds,
            )
        )

        validation_after_local_repair = (
            validate_project(
                staging_dir,
                test_timeout=config.test_timeout_seconds,
            )
        )
    else:
        validation_after_local_repair = (
            first_validation
        )

    accepted_after_local_repair = (
        validation_after_local_repair["all_passed"]
    )

    post_repair_local_report = None

    if (
        not validation_after_local_repair["all_passed"]
        and config.max_repair_attempts > 0
    ):
        repair_prompt = build_repair_prompt(
            change=change,
            staging_dir=staging_dir,
            affected_files=affected_files,
            validation=validation_after_local_repair,
        )

        repair_generation = generate_with_qwen(
            tokenizer=tokenizer,
            model=model,
            system_prompt=REPAIR_SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            max_new_tokens=config.max_new_tokens,
            max_context_tokens=config.max_context_tokens,
        )

        repair_payload = extract_json_object(
            repair_generation.text
        )

        validate_payload_schema(repair_payload)

        validate_generated_scope(
            repair_payload,
            change,
            affected_files,
        )

        apply_generated_payload(
            staging_dir,
            repair_payload,
        )

        post_repair_local_report = (
            run_deterministic_local_repair(
                staging_dir,
                test_timeout=config.test_timeout_seconds,
            )
        )

        final_validation = validate_project(
            staging_dir,
            test_timeout=config.test_timeout_seconds,
        )

    else:
        final_validation = (
            validation_after_local_repair
        )

    passed = final_validation["all_passed"]

    snapshot_name = (
        f"{change.version}_{change.change_id}"
        if passed
        else (
            f"failed_{change.version}_"
            f"{change.change_id}"
        )
    )

    snapshot = create_snapshot(
        staging_dir,
        snapshot_name,
        snapshots_dir=snapshots_dir,
    )

    file_diff = compare_manifests(
        project_dir,
        staging_dir,
    )

    if passed:
        if project_dir.exists():
            shutil.rmtree(project_dir)

        shutil.copytree(
            staging_dir,
            project_dir,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                ".pytest_cache",
                ".ruff_cache",
                "*.pyc",
            ),
        )

    end_time = time.perf_counter()

    local_repair_actions = local_repair_report.get(
        "actions", []
    )

    metrics = build_change_metrics(
        change=change,
        strategy="selective_bundle",
        experiment_name=config.experiment_name,
        project_name="todo_api",
        model_id=config.model_id,
        seed=config.seed,
        dsl_diff=dsl_diff,
        affected_files=affected_files,
        file_diff=file_diff,
        initial_generation=initial_generation,
        repair_generation=repair_generation,
        first_validation=first_validation,
        validation_after_local_repair=validation_after_local_repair,
        final_validation=final_validation,
        first_pass_acceptance=first_pass_acceptance,
        local_repair_used=local_repair_used,
        local_repair_actions=local_repair_actions,
        accepted_after_local_repair=accepted_after_local_repair,
        start_time=start_time,
        end_time=end_time,
        quantization=getattr(
            model, "_used_quantization", "unknown"
        ),
    )

    if results_path is not None:
        append_metrics_jsonl(results_path, metrics)

    return {
        "change_id": change.change_id,
        "version": change.version,
        "passed": passed,
        "first_pass_acceptance": first_pass_acceptance,
        "local_repair_used": local_repair_used,
        "accepted_after_local_repair": accepted_after_local_repair,
        "llm_repair_used": (
            repair_generation is not None
        ),
        "affected_files": affected_files,
        "dsl_diff": dsl_diff,
        "metrics": metrics,
        "first_validation": first_validation,
        "final_validation": final_validation,
        "snapshot": str(snapshot),
    }
