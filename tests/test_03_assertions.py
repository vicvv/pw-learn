"""Module 03 - Assertions and auto-waiting.

Practice: Playwright's public TodoMVC demo, plus tiny local pages built
with page.set_content(), so the waiting can be shown on purpose.
Run from the repo root with the venv active:
    pytest FILES/test_03_assertions.py -v
"""
import re

from playwright.sync_api import Page, expect

TODO_URL = "https://demo.playwright.dev/todomvc/"

DELAYED_PAGE = """
<button>Start</button>
<div data-testid="result"></div>
<script>
  document.querySelector("button").onclick = () => {
    setTimeout(() => {
      document.querySelector("[data-testid=result]").textContent = "Done";
    }, DELAY);
  };
</script>
"""

DISABLED_BUTTON_PAGE = """
<button disabled>Go</button>
<div data-testid="result"></div>
<script>
  const button = document.querySelector("button");
  setTimeout(() => { button.disabled = false; }, 1000);
  button.onclick = () => {
    document.querySelector("[data-testid=result]").textContent = "Clicked";
  };
</script>
"""


def open_delayed_page(page: Page, delay_ms: int):
    """Load a tiny page where clicking Start shows "Done" after delay_ms."""
    page.set_content(DELAYED_PAGE.replace("DELAY", str(delay_ms)))


def add_todo(page: Page, text: str):
    """Open the TodoMVC demo and add one item."""
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    new_todo.fill(text)
    new_todo.press("Enter")


# ---------- ASSERTIONS ON THE PAGE AND ON ELEMENTS ----------

def test_page_title_and_url(page: Page):
    page.goto(TODO_URL)
    expect(page).to_have_title(re.compile("TodoMVC"))
    expect(page).to_have_url(re.compile("todomvc"))


def test_text_assertions(page: Page):
    add_todo(page, "buy milk")
    title = page.get_by_test_id("todo-title")
    expect(title).to_have_text("buy milk")
    expect(title).to_contain_text("milk")
    expect(page.get_by_test_id("todo-count")).to_have_text("1 item left")


def test_value_and_checked(page: Page):
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    new_todo.fill("draft")
    expect(new_todo).to_have_value("draft")
    new_todo.press("Enter")
    expect(new_todo).to_be_empty()
    checkbox = page.get_by_test_id("todo-item").get_by_role("checkbox")
    expect(checkbox).not_to_be_checked()
    checkbox.check()
    expect(checkbox).to_be_checked()


def test_negative_assertions(page: Page):
    add_todo(page, "buy milk")
    page.get_by_test_id("todo-item").get_by_role("checkbox").check()
    page.get_by_role("button", name="Clear completed").click()
    expect(page.get_by_test_id("todo-item")).to_have_count(0)
    expect(page.get_by_role("button", name="Clear completed")).to_be_hidden()


# ---------- WAITING ----------

def test_expect_waits_for_text(page: Page):
    open_delayed_page(page, 1500)
    page.get_by_role("button", name="Start").click()
    expect(page.get_by_test_id("result")).to_have_text("Done")


def test_reading_does_not_wait(page: Page):
    open_delayed_page(page, 1500)
    page.get_by_role("button", name="Start").click()
    assert page.get_by_test_id("result").inner_text() == ""


def test_click_waits_for_enabled(page: Page):
    page.set_content(DISABLED_BUTTON_PAGE)
    page.get_by_role("button", name="Go").click()
    expect(page.get_by_test_id("result")).to_have_text("Clicked")


def test_custom_timeout(page: Page):
    open_delayed_page(page, 6000)
    page.get_by_role("button", name="Start").click()
    expect(page.get_by_test_id("result")).to_have_text("Done", timeout=10_000)