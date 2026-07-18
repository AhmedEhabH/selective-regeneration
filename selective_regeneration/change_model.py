# change_model.py — Data structures for requirement change definitions.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequirementChange:
    """A structured definition of a single requirement change.

    Attributes:
        change_id: Unique identifier (e.g. "CH-001").
        version: Semantic version after this change (e.g. "1.1").
        title: Short human-readable title.
        requirement_delta: Natural-language description of what changed.
        dsl_patch: Dict of dotted-path -> new value for DSL updates.
        expected_change_types: Expected categories of code changes.
        allowed_files: Files the LLM is permitted to modify.
        hidden_test_files: Mapping of filename -> file content for
            hidden tests that should be written before validation.
    """
    change_id: str
    version: str
    title: str
    requirement_delta: str
    dsl_patch: dict
    expected_change_types: list[str]
    allowed_files: list[str]
    hidden_test_files: dict[str, str] = field(
        default_factory=dict
    )
