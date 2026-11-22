"""Module 04 - Debugging: screenshots, traces, console messages and page errors.

Practice: Playwright's public TodoMVC demo, plus tiny local pages built
with page.set_content().
Run from the repo root with the venv active:
    pytest FILES/test_04_debugging.py -v
"""
from playwright.sync_api import Browser, Page, expect

TODO_URL = "https://demo.playwright.dev/todomvc/"


def add_todos(page: Page, *items: str):
    """Open the TodoMVC demo and add the given items."""
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    for item in items:
        new_todo.fill(item)
        new_todo.press("Enter")


def test_page_screenshot(page: Page, tmp_path):
    add_todos(page, "buy milk")
    shot = tmp_path / "page.png"
    page.screenshot(path=shot, full_page=True)
    assert shot.exists()
    assert shot.stat().st_size > 0


def test_element_screenshot(page: Page, tmp_path):
    add_todos(page, "buy milk")
    shot = tmp_path / "item.png"
    page.get_by_test_id("todo-item").screenshot(path=shot)
    assert shot.exists()
    assert shot.stat().st_size > 0


def test_manual_trace(browser: Browser, tmp_path):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    add_todos(page, "buy milk", "walk the dog")
    expect(page.get_by_test_id("todo-item")).to_have_count(2)
    trace_file = tmp_path / "trace.zip"
    context.tracing.stop(path=trace_file)
    context.close()
    assert trace_file.exists()


def test_console_message(page: Page):
    with page.expect_console_message() as message_info:
        page.set_content("<script>console.log('hello from the page')</script>")
    assert message_info.value.text == "hello from the page"


def test_page_error(page: Page):
    with page.expect_event("pageerror") as error_info:
        page.set_content("<script>throw new Error('boom')</script>")
    assert "boom" in error_info.value.message


def test_todo_flow(page: Page):
    add_todos(page, "buy milk", "walk the dog")
    page.get_by_test_id("todo-item").filter(has_text="buy milk").get_by_role("checkbox").check()
    expect(page.get_by_test_id("todo-count")).to_have_text("1 item left")
    expect(page.get_by_test_id("todo-item")).to_have_count(2)