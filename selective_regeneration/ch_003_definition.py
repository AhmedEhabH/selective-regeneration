# CH-003: Change the overdue rule so that tasks due on the current date are also overdue.
#
# Add this cell after the CH-002 section in the notebook.

from selective_regeneration.change_model import RequirementChange

CHANGE_3 = RequirementChange(
    change_id="CH-003",
    version="1.3",
    title="Overdue includes current date",
    requirement_delta="""
Change the overdue rule so that tasks due on the current
date are also considered overdue.

Previously a task was overdue only when due_date was strictly
earlier than current_date. Now a task is overdue when
due_date is earlier than or equal to current_date.

All other behavior (completed tasks, tags, filtering) must
remain unchanged.
""".strip(),

    dsl_patch={
        "project.version": "1.3",
        "business_rules.overdue_rule": {
            "text": (
                "A task is overdue when it has a due date, "
                "is incomplete, and due_date is earlier than "
                "or equal to current_date."
            )
        },
    },

    expected_change_types=[
        "modify_business_rule",
    ],

    allowed_files=[
        "app/service.py",
        "app/main.py",
        "app/models.py",
        "app/schemas.py",
        "tests/unit/test_service.py",
        "tests/integration/test_api.py",
        "dsl.yaml",
    ],

    hidden_test_files={
        # Overwrite CH-001 hidden test to remove the
        # now-failing "due today is NOT overdue" test.
        "hidden_tests/test_change_001.py": """
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_completed_task_is_not_overdue() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Completed task",
            "due_date": "2026-01-01",
        },
    ).json()

    client.post(f"/tasks/{created['id']}/complete")

    response = client.get(
        "/tasks/overdue",
        params={"current_date": "2026-06-01"},
    )

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert created["id"] not in returned_ids
""",

        # New hidden tests for the updated overdue rule.
        "hidden_tests/test_change_003.py": """
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_task_due_today_is_now_overdue() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Due today",
            "due_date": "2026-06-01",
        },
    ).json()

    response = client.get(
        "/tasks/overdue",
        params={"current_date": "2026-06-01"},
    )

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert created["id"] in returned_ids


def test_task_due_yesterday_is_overdue() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Due yesterday",
            "due_date": "2026-05-31",
        },
    ).json()

    response = client.get(
        "/tasks/overdue",
        params={"current_date": "2026-06-01"},
    )

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert created["id"] in returned_ids


def test_task_due_tomorrow_is_not_overdue() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Due tomorrow",
            "due_date": "2026-06-02",
        },
    ).json()

    response = client.get(
        "/tasks/overdue",
        params={"current_date": "2026-06-01"},
    )

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert created["id"] not in returned_ids


def test_completed_task_due_today_not_overdue() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Completed due today",
            "due_date": "2026-06-01",
        },
    ).json()

    client.post(f"/tasks/{created['id']}/complete")

    response = client.get(
        "/tasks/overdue",
        params={"current_date": "2026-06-01"},
    )

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert created["id"] not in returned_ids
""",
    },
)
