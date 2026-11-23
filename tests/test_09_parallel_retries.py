"""Module 09 - Parallel runs, retries and flaky tests.

Needs pytest-xdist (parallel runs) and pytest-rerunfailures (retries).
Run from the repo root with the venv active:
    pytest tests/test_09_parallel_retries.py -v
    pytest tests/test_09_parallel_retries.py -v -n 4
"""
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from pw_learn.pages import TodoPage


# ---------- INDEPENDENT TESTS RUN SAFELY IN PARALLEL ----------

@pytest.mark.parametrize("number", [1, 2, 3, 4])
def test_independent_tests(todo_page: TodoPage, number: int):
    text = f"task {number}"
    todo_page.add(text)
    expect(todo_page.titles).to_have_text(text)
    expect(todo_page.counter).to_have_text("1 item left")


def test_worker_id(worker_id: str):
    # "master" when run without -n, "gw0", "gw1" and so on inside parallel workers
    assert worker_id == "master" or worker_id.startswith("gw")


def test_unique_data_per_test(todo_page: TodoPage):
    text = f"item-{uuid4().hex[:8]}"
    todo_page.add(text)
    expect(todo_page.item(text)).to_have_count(1)


# ---------- RETRIES ----------

_attempts = {"count": 0}


@pytest.mark.flaky(reruns=2)
def test_flaky_passes_on_retry():
    """Fails on its first attempt on purpose, to show what a rerun looks like."""
    _attempts["count"] += 1
    assert _attempts["count"] >= 2, "fails on the first attempt on purpose"