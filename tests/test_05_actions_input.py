"""Module 05 - Actions and input: typing, keys, clicks, hover, drag, dropdowns.

Practice: Playwright's public TodoMVC demo, plus tiny local pages built
with page.set_content().
Run from the repo root with the venv active:
    pytest tests/test_05_actions_input.py -v
"""
from playwright.sync_api import Page, expect

TODO_URL = "https://demo.playwright.dev/todomvc/"

FORM_PAGE = """
<form>
  <label for="name">Name</label>
  <input id="name" value="old text">

  <label for="size">Size</label>
  <select id="size">
    <option value="s">Small</option>
    <option value="m">Medium</option>
    <option value="l">Large</option>
  </select>

  <label for="toppings">Toppings</label>
  <select id="toppings" multiple>
    <option value="cheese">Cheese</option>
    <option value="ham">Ham</option>
    <option value="olives">Olives</option>
  </select>

  <label><input type="checkbox" id="terms"> I accept the terms</label>
  <label><input type="radio" name="plan" value="free" id="free"> Free</label>
  <label><input type="radio" name="plan" value="pro" id="pro"> Pro</label>
</form>
<div data-testid="typed"></div>
<script>
  document.querySelector("#name").addEventListener("keyup", (event) => {
    document.querySelector("[data-testid=typed]").textContent += event.key + " ";
  });
</script>
"""

CLICK_PAGE = """
<button id="target">Click me</button>
<div data-testid="log"></div>
<script>
  const log = document.querySelector("[data-testid=log]");
  const button = document.querySelector("#target");
  button.onclick = (event) => { log.textContent = event.detail === 2 ? "double" : "single"; };
  button.oncontextmenu = (event) => { event.preventDefault(); log.textContent = "right"; };
  button.onmouseenter = () => { log.textContent = "hovered"; };
</script>
"""

LONG_PAGE = """
<div style="height: 3000px">scroll down</div>
<button id="bottom">Bottom button</button>
<div data-testid="log"></div>
<script>
  document.querySelector("#bottom").onclick = () => {
    document.querySelector("[data-testid=log]").textContent = "bottom clicked";
  };
</script>
"""


def open_todos(page: Page, *items: str):
    """Open the TodoMVC demo and add the given items."""
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    for item in items:
        new_todo.fill(item)
        new_todo.press("Enter")


# ---------- TYPING ----------

def test_fill_replaces_existing_text(page: Page):
    page.set_content(FORM_PAGE)
    name = page.get_by_label("Name")
    expect(name).to_have_value("old text")
    name.fill("new text")
    expect(name).to_have_value("new text")


def test_clear_empties_a_field(page: Page):
    page.set_content(FORM_PAGE)
    name = page.get_by_label("Name")
    name.clear()
    expect(name).to_be_empty()


def test_press_sequentially_fires_key_events(page: Page):
    page.set_content(FORM_PAGE)
    page.get_by_label("Name").clear()
    # clear() presses Delete, which the page also records, so start the log fresh
    page.evaluate("document.querySelector('[data-testid=typed]').textContent = ''")
    page.get_by_label("Name").press_sequentially("abc")
    expect(page.get_by_test_id("typed")).to_have_text("a b c")


# ---------- KEYS ----------

def test_press_enter_submits(page: Page):
    page.goto(TODO_URL)
    new_todo = page.get_by_placeholder("What needs to be done?")
    new_todo.fill("buy milk")
    new_todo.press("Enter")
    expect(page.get_by_test_id("todo-title")).to_have_text("buy milk")


def test_escape_cancels_edit(page: Page):
    open_todos(page, "buy milk")
    page.get_by_test_id("todo-title").dblclick()
    edit_box = page.get_by_role("textbox", name="Edit")
    edit_box.fill("something else")
    edit_box.press("Escape")
    expect(page.get_by_test_id("todo-title")).to_have_text("buy milk")


def test_keyboard_shortcut_selects_all(page: Page):
    page.set_content(FORM_PAGE)
    name = page.get_by_label("Name")
    name.click()
    name.press("ControlOrMeta+a")
    name.press("Backspace")
    expect(name).to_be_empty()


# ---------- CLICKS AND HOVER ----------

def test_double_click(page: Page):
    page.set_content(CLICK_PAGE)
    page.get_by_role("button", name="Click me").dblclick()
    expect(page.get_by_test_id("log")).to_have_text("double")


def test_right_click(page: Page):
    page.set_content(CLICK_PAGE)
    page.get_by_role("button", name="Click me").click(button="right")
    expect(page.get_by_test_id("log")).to_have_text("right")


def test_hover(page: Page):
    page.set_content(CLICK_PAGE)
    page.get_by_role("button", name="Click me").hover()
    expect(page.get_by_test_id("log")).to_have_text("hovered")


def test_click_scrolls_into_view(page: Page):
    page.set_content(LONG_PAGE)
    page.get_by_role("button", name="Bottom button").click()
    expect(page.get_by_test_id("log")).to_have_text("bottom clicked")


# ---------- CHECKBOXES, RADIO BUTTONS AND DROPDOWNS ----------

def test_check_and_uncheck(page: Page):
    page.set_content(FORM_PAGE)
    terms = page.get_by_label("I accept the terms")
    expect(terms).not_to_be_checked()
    terms.check()
    expect(terms).to_be_checked()
    terms.check()                      # already checked: does nothing
    expect(terms).to_be_checked()
    terms.uncheck()
    expect(terms).not_to_be_checked()


def test_radio_buttons(page: Page):
    page.set_content(FORM_PAGE)
    page.get_by_label("Pro").check()
    expect(page.get_by_label("Pro")).to_be_checked()
    expect(page.get_by_label("Free")).not_to_be_checked()


def test_select_option(page: Page):
    page.set_content(FORM_PAGE)
    size = page.get_by_label("Size", exact=True)
    size.select_option("m")                        # by value
    expect(size).to_have_value("m")
    size.select_option(label="Large")              # by visible text
    expect(size).to_have_value("l")


def test_select_multiple_options(page: Page):
    page.set_content(FORM_PAGE)
    toppings = page.get_by_label("Toppings")
    toppings.select_option(["cheese", "olives"])
    expect(toppings).to_have_values(["cheese", "olives"])