"""Module 07 - Fixtures, the Page Object Model and device emulation.

The fixtures (todo_page, todo_with_items, mobile_page) live in tests/conftest.py.
The page object (TodoPage) lives in src/pw_learn/pages/todo_page.py.
Run from the repo root with the venv active:
    pytest tests/test_07_fixtures_pom.py -v
"""
import re

from playwright.sync_api import Page, expect

from pw_learn.pages import TodoPage


# ---------- PAGE OBJECT AND FIXTURES ----------

def test_page_object_adds_items(todo_page: TodoPage):
    todo_page.add("buy milk", "walk the dog")
    expect(todo_page.titles).to_have_text(["buy milk", "walk the dog"])


def test_fixture_provides_items(todo_with_items: TodoPage):
    expect(todo_with_items.items).to_have_count(3)
    expect(todo_with_items.counter).to_have_text("3 items left")


def test_complete_an_item(todo_with_items: TodoPage):
    todo_with_items.complete("walk the dog")
    expect(todo_with_items.item("walk the dog")).to_have_class(re.compile("completed"))
    expect(todo_with_items.counter).to_have_text("2 items left")


def test_delete_an_item(todo_with_items: TodoPage):
    todo_with_items.delete("buy milk")
    expect(todo_with_items.titles).to_have_text(["walk the dog", "write tests"])


def test_filter_links(todo_with_items: TodoPage):
    todo_with_items.complete("buy milk")
    todo_with_items.show("Active")
    expect(todo_with_items.titles).to_have_text(["walk the dog", "write tests"])
    todo_with_items.show("Completed")
    expect(todo_with_items.titles).to_have_text(["buy milk"])


def test_chained_actions(todo_with_items: TodoPage):
    todo_with_items.complete("buy milk").complete("write tests").clear_completed()
    expect(todo_with_items.titles).to_have_text(["walk the dog"])


def test_each_test_starts_empty(todo_page: TodoPage):
    expect(todo_page.items).to_have_count(0)


# ---------- CONTEXT SETTINGS AND DEVICES ----------

def test_context_args_set_the_language(page: Page):
    page.set_content("<p>hello</p>")
    assert page.evaluate("navigator.language") == "en-US"


def test_mobile_emulation(mobile_page: Page):
    # Without the viewport meta tag, a phone lays the page out 980 pixels wide,
    # as if it were an old desktop site. Real mobile-friendly pages include it.
    mobile_page.set_content(
        '<meta name="viewport" content="width=device-width, initial-scale=1"><p>hello</p>'
    )
    assert "iPhone" in mobile_page.evaluate("navigator.userAgent")
    assert mobile_page.viewport_size["width"] == 390      # the iPhone 13 screen
    assert mobile_page.evaluate("window.innerWidth") == 390


def test_todo_on_a_phone(mobile_page: Page):
    todo = TodoPage(mobile_page).open()
    todo.add("buy milk")
    expect(todo.titles).to_have_text("buy milk")