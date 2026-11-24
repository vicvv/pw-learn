"""Module 12 - CI/CD and reporting.

These tests check the repository's own CI setup: that the workflow file is
valid, that it does what the notes describe, and that no secret is hard-coded
in it. They need no browser and no internet.
Run from the repo root with the venv active:
    pytest tests/test_12_ci_reporting.py -v
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "playwright.yml"


@pytest.fixture(scope="module")
def workflow_text() -> str:
    if not WORKFLOW.exists():
        pytest.skip("no workflow file in this repository")
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_file_exists():
    assert WORKFLOW.exists(), f"expected a workflow at {WORKFLOW}"


def test_workflow_is_valid_yaml(workflow_text: str):
    yaml = pytest.importorskip("yaml", reason="PyYAML is not installed")
    data = yaml.safe_load(workflow_text)
    assert isinstance(data, dict)
    assert "jobs" in data
    assert set(data["jobs"]) == {"smoke", "full"}


def test_browsers_are_installed_with_dependencies(workflow_text: str):
    """A Linux runner has none of the libraries a browser needs (Module 01)."""
    assert "playwright install --with-deps" in workflow_text


def test_traces_are_kept_on_failure(workflow_text: str):
    assert "--tracing retain-on-failure" in workflow_text


def test_reports_are_produced(workflow_text: str):
    assert "--junit-xml=" in workflow_text
    assert "--html=" in workflow_text


def test_credentials_come_from_secrets(workflow_text: str):
    assert "secrets.SHOP_PASSWORD" in workflow_text


def test_no_password_is_hard_coded(workflow_text: str):
    """A real password in a workflow file would be public in the repository."""
    for line in workflow_text.splitlines():
        if "${{" in line:
            continue                      # a reference to a secret, not a value
        assert not re.search(r"(?i)(password|token|secret)\s*:\s*\S", line), line


def test_jobs_have_a_timeout(workflow_text: str):
    """Without one, a hung job can run for hours."""
    assert workflow_text.count("timeout-minutes:") >= 2


def test_reports_are_not_committed():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("test-results/", "auth/", "report*.html", "results*.xml"):
        assert pattern in gitignore, f"{pattern} should be in .gitignore"
