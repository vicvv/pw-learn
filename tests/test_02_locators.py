"""Module 02 - Locators: finding elements the way users see them.

Practice site: Playwright's public TodoMVC demo.
Run from the repo root with the venv active:
    pytest tests/test_02_locators.py -v
"""
import re

from playwright.sync_api import Page, expect

TODO_URL = "https://demo.playwright.dev/todomvc/"
ITEMS = ["buy milk", "walk the dog", "write tests"]


def open_with_items(page: Page):
    """Open the demo app and add the three ITEMS."""
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    for item in ITEMS:
        new_todo.fill(item)
        new_todo.press("Enter")


def test_heading_by_role(page: Page):
    page.goto(TODO_URL)
    expect(page.get_by_role("heading", name="todos")).to_be_visible()


def test_items_by_test_id(page: Page):
    open_with_items(page)
    expect(page.get_by_test_id("todo-title")).to_have_text(ITEMS)


def test_item_by_text(page: Page):
    open_with_items(page)
    expect(page.get_by_text("walk the dog")).to_be_visible()


def test_filter_and_chain(page: Page):
    open_with_items(page)
    item = page.get_by_test_id("todo-item").filter(has_text="walk the dog")
    item.get_by_role("checkbox").check()
    expect(item).to_have_class(re.compile("completed"))
    expect(page.get_by_test_id("todo-count")).to_have_text("2 items left")


def test_first_nth_last(page: Page):
    open_with_items(page)
    titles = page.get_by_test_id("todo-title")
    expect(titles).to_have_count(3)
    expect(titles.first).to_have_text("buy milk")
    expect(titles.nth(1)).to_have_text("walk the dog")
    expect(titles.last).to_have_text("write tests")


def test_filter_links_by_role(page: Page):
    open_with_items(page)
    page.get_by_test_id("todo-item").first.get_by_role("checkbox").check()
    page.get_by_role("link", name="Active").click()
    expect(page.get_by_test_id("todo-title")).to_have_text(["walk the dog", "write tests"])
    page.get_by_role("link", name="Completed").click()
    expect(page.get_by_test_id("todo-title")).to_have_text(["buy milk"])


def test_mark_all_by_label(page: Page):
    open_with_items(page)
    page.get_by_label("Mark all as complete").check()
    expect(page.get_by_role("button", name="Clear completed")).to_be_visible()