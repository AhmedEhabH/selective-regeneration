# Versioning

Versioning policy for the Selective Regeneration Pipeline.

---

## Format

This project follows [Semantic Versioning](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH
```

- **MAJOR** — Breaking changes to the API, data format, or pipeline behavior.
- **MINOR** — New features, new experiment arms, new modules. Backward-compatible.
- **PATCH** — Bug fixes, documentation updates, internal refactoring. No behavior change.

## Research Baseline Versions

The project uses a modified versioning scheme for research milestones:

```
v2.2.0 RC1  →  Research Baseline (frozen)
v2.2.0      →  Validated Baseline (GPU-verified)
v2.3.0      →  New capability or experiment arm
v3.0.0      →  New research phase or breaking change
```

### Version Progression

| Version | Milestone | Status |
|---------|-----------|--------|
| v1.0.0 | Initial implementation (HF Hub loading) | Superseded |
| v2.0.0 | Kaggle model loading, GPTQ/BNB | Superseded |
| v2.1.0 | Repository restructuring, model discovery | Superseded |
| **v2.2.0** | **Research Baseline — RC1** | **Current** |
| v2.2.0 | Research Baseline — GPU-validated | Pending |
| v2.3.0 | Automatic dependency extraction | Future |
| v3.0.0 | Comparative experiment arms | Future |

## When to Bump Versions

### MINOR bump (e.g., v2.2.0 → v2.3.0)

- Adding a new module to the package.
- Adding a new experiment arm.
- Adding a new validation stage.
- Adding new metrics fields.
- Changing the notebook structure significantly.

### PATCH bump (e.g., v2.2.0 → v2.2.1)

- Fixing a bug in existing code.
- Updating documentation.
- Adding tests.
- Refactoring without behavior change.
- Updating dependencies.

### MAJOR bump (e.g., v2.x → v3.0.0)

- Changing the `RequirementChange` dataclass structure.
- Changing the `GENERATION_SCHEMA`.
- Changing the `run_selective_change()` return dict keys.
- Changing the package name.
- Dropping Python version support.

## Release Candidates

For significant releases, use release candidates:

```
v2.2.0-rc1  →  First release candidate
v2.2.0-rc2  →  Second release candidate (if needed)
v2.2.0      →  Final release
```

RC tags indicate the release is functionally complete but needs validation (e.g., GPU testing).

## Tagging

Use annotated tags for releases:

```bash
git tag -a v2.2.0 -m "Research Baseline v2.2.0"
```

## Research Milestone Mapping

| Research Phase | Expected Version |
|----------------|------------------|
| Baseline implementation | v2.2.0 |
| Automatic dependency extraction | v2.3.0 |
| Comparative experiment arms | v2.4.0 – v3.0.0 |
| Multi-project benchmarks | v3.x |
| Thesis writing / final | v3.x + docs |
