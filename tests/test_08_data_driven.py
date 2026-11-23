"""Module 08 - Data-driven tests and organisation.

parametrize, test data from CSV and JSON files, markers, skip and xfail,
and settings that change between environments.
Run from the repo root with the venv active:
    pytest tests/test_08_data_driven.py -v
"""
import csv
import json
import re
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from pw_learn import settings
from pw_learn.pages import TodoPage

DATA = Path(__file__).parent / "data"


def load_csv(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(name: str):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def split_items(text: str) -> list[str]:
    """'milk|eggs' -> ['milk', 'eggs'], and '' -> []."""
    return [item for item in text.split("|") if item]


# ---------- PARAMETRIZE ----------

@pytest.mark.smoke
@pytest.mark.parametrize(
    "text",
    [
        pytest.param("buy milk", id="plain"),
        pytest.param("café crème", id="accents"),
        pytest.param("x" * 100, id="long"),
        pytest.param("<b>not bold</b>", id="html-shown-as-text"),
    ],
)
def test_add_any_text(todo_page: TodoPage, text: str):
    todo_page.add(text)
    expect(todo_page.titles).to_have_text(text)


@pytest.mark.smoke
@pytest.mark.parametrize(
    "count, label",
    [
        (1, "1 item left"),
        (2, "2 items left"),
        (3, "3 items left"),
    ],
)
def test_counter_label(todo_page: TodoPage, count: int, label: str):
    todo_page.add(*[f"item {number}" for number in range(count)])
    expect(todo_page.counter).to_have_text(label)


@pytest.mark.parametrize("first", ["milk", "eggs"])
@pytest.mark.parametrize("second", ["bread", "jam"])
def test_every_combination(todo_page: TodoPage, first: str, second: str):
    todo_page.add(first, second)
    expect(todo_page.titles).to_have_text([first, second])


# ---------- TEST DATA FROM FILES ----------

@pytest.mark.parametrize(
    "items, complete, expected_left",
    [
        pytest.param(
            split_items(row["items"]),
            split_items(row["complete"]),
            row["expected_left"],
            id=row["case"],
        )
        for row in load_csv("todos.csv")
    ],
)
def test_counter_from_csv(todo_page: TodoPage, items, complete, expected_left):
    todo_page.add(*items)
    for text in complete:
        todo_page.complete(text)
    expect(todo_page.counter).to_have_text(expected_left)


@pytest.mark.slow
@pytest.mark.parametrize(
    "case",
    [pytest.param(entry, id=entry["id"]) for entry in load_json("filters.json")],
)
def test_filters_from_json(todo_page: TodoPage, case: dict):
    todo_page.add(*case["items"])
    for text in case["complete"]:
        todo_page.complete(text)
    todo_page.show(case["filter"])
    expect(todo_page.titles).to_have_text(case["expected"])


# ---------- SKIP AND XFAIL ----------

@pytest.mark.skipif(sys.platform == "win32", reason="checks a Unix-style path")
def test_skip_on_some_systems(tmp_path):
    assert str(tmp_path).startswith("/")


def test_skip_at_runtime(page: Page, browser_name: str):
    if browser_name == "webkit":
        pytest.skip("example of a runtime skip: not checked in WebKit")
    page.set_content("<p>hello</p>")
    expect(page.get_by_text("hello")).to_be_visible()


@pytest.mark.xfail(
    strict=True,
    reason="known gap: the app ignores empty items, but a requirement says they should be added",
)
def test_empty_item_is_added(todo_page: TodoPage):
    todo_page.new_todo.press("Enter")
    expect(todo_page.items).to_have_count(1, timeout=1000)


# ---------- SETTINGS PER ENVIRONMENT ----------

def test_relative_url_uses_base_url(page: Page, base_url: str):
    assert base_url == "https://demo.playwright.dev"
    page.goto("/todomvc/")
    expect(page).to_have_url(re.compile(r"demo\.playwright\.dev/todomvc"))


def test_setting_has_a_default(monkeypatch):
    monkeypatch.delenv("TODO_URL", raising=False)
    assert settings.todo_url() == settings.DEFAULT_TODO_URL


def test_setting_from_environment(monkeypatch):
    monkeypatch.setenv("TODO_URL", "https://staging.example.com/todomvc/")
    assert settings.todo_url() == "https://staging.example.com/todomvc/"


def test_read_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('# a comment\n\nTODO_URL="https://local.example/"\nOTHER=1\n')
    assert settings.read_env_file(env_file) == {
        "TODO_URL": "https://local.example/",
        "OTHER": "1",
    }