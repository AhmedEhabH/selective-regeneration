# Contributing

Guidelines for contributing to the Selective Regeneration Pipeline.

---

## Repository Layout

```
selective-regeneration-pipeline/
├── selective_regeneration/    # Python package — all pipeline logic
├── notebooks/                 # Jupyter notebooks — experiment drivers
├── tests/                     # Unit tests
├── config/                    # Experiment configuration
└── *.md                       # Documentation
```

- **Package code** goes in `selective_regeneration/`.
- **Experiment notebooks** go in `notebooks/`.
- **Tests** go in `tests/`.
- **Configuration** goes in `config/`.
- **Documentation** goes at the repository root.

## Coding Style

- Python 3.11+ required.
- Follow PEP 8 for naming: `lowercase_with_underscores` for modules/functions, `CamelCase` for classes, `UPPER_CASE` for constants.
- Every public function and class must have a docstring.
- Every module must have a header comment on line 1.
- Prefer `pathlib.Path` over string paths.
- Use type annotations for all function signatures.
- Keep functions focused — one responsibility per function.
- No side effects on module import (except dataclass instantiation for constants).

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix or correction |
| `docs` | Documentation only |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or updating tests |
| `chore` | Build, CI, or tooling changes |
| `perf` | Performance improvement |

### Scopes

| Scope | Area |
|-------|------|
| `pipeline` | Core experiment pipeline |
| `llm` | Model loading and generation |
| `validation` | Multi-stage validation |
| `repair` | Deterministic and LLM repair |
| `metrics` | Metrics collection |
| `notebook` | Jupyter notebooks |
| `docs` | Documentation |
| `manifest` | Repository manifest |

### Examples

```
feat(llm): add Qwen2.5-Coder 32B support
fix(validation): handle empty test directory gracefully
docs: update ARCHITECTURE.md scoring table
test(llm): add unit tests for GPTQ backend detection
refactor(pipeline): extract repair logic into separate module
```

## Branching Strategy

- `main` — Stable, tagged releases only. Never push directly.
- `develop` — Integration branch for active work.
- `feature/<name>` — Feature branches off `develop`.
- `fix/<name>` — Bug fix branches off `main` or `develop`.
- `release/<version>` — Release preparation branches.

### Workflow

1. Create a feature branch from `develop`.
2. Make changes, commit with conventional messages.
3. Open a pull request to `develop`.
4. After review, merge into `develop`.
5. When ready for release, create `release/<version>` from `develop`.
6. Tag the release and merge into `main`.

## Documentation Rules

- All documentation files are at the repository root.
- `README.md` is the entry point for new developers.
- `ARCHITECTURE.md` describes system design.
- `CODEBASE_MAP.md` documents every module.
- `CHANGELOG.md` records all version changes.
- `TODO.md` tracks the development roadmap.
- Update `MANIFEST.json` when adding or removing files.
- Update `CHANGELOG.md` for every version bump.

## Testing Expectations

- Run `python -m pytest tests/ -v` before committing.
- Tests must pass without GPU (lazy imports for torch/transformers).
- Add tests for new public functions.
- Test edge cases, not just happy paths.
- Aim for >80% line coverage on `selective_regeneration/`.

## For AI Contributors

If you are an AI coding agent:

1. Read `PROJECT_SUMMARY.md` first.
2. Read `SYSTEM_STATE.md` for current status.
3. Read `CODEBASE_MAP.md` for module details.
4. Check `TODO.md` for pending tasks.
5. Never modify the research algorithm without explicit approval.
6. Never push to `main` directly.
7. Always run tests before committing.
8. Update documentation when changing public APIs.
