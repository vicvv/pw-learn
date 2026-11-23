"""Page object for the TodoMVC demo. Filled in during Module 06."""
"""Page object for Playwright's TodoMVC demo.

A page object holds the locators and actions for one page, so tests can
say what they do ("add an item", "complete it") instead of how.
"""
from playwright.sync_api import Locator, Page


class TodoPage:
    URL = "https://demo.playwright.dev/todomvc/"

    def __init__(self, page: Page):
        self.page = page
        # Locators are lazy (Module 02), so creating them here searches nothing yet.
        self.new_todo = page.get_by_placeholder("What needs to be done?")
        self.items = page.get_by_test_id("todo-item")
        self.titles = page.get_by_test_id("todo-title")
        self.counter = page.get_by_test_id("todo-count")
        self.toggle_all = page.get_by_label("Mark all as complete")
        self.clear_completed_button = page.get_by_role("button", name="Clear completed")

    def open(self) -> "TodoPage":
        self.page.goto(self.URL)
        return self

    def add(self, *texts: str) -> "TodoPage":
        for text in texts:
            self.new_todo.fill(text)
            self.new_todo.press("Enter")
        return self

    def item(self, text: str) -> Locator:
        """The list item whose text contains the given text."""
        return self.items.filter(has_text=text)

    def complete(self, text: str) -> "TodoPage":
        self.item(text).get_by_role("checkbox").check()
        return self

    def delete(self, text: str) -> "TodoPage":
        item = self.item(text)
        item.hover()                              # the delete button only appears on hover
        item.get_by_role("button").click()        # the only button inside an item
        return self

    def show(self, filter_name: str) -> "TodoPage":
        """Click one of the filter links: All, Active or Completed."""
        self.page.get_by_role("link", name=filter_name).click()
        return self

    def clear_completed(self) -> "TodoPage":
        self.clear_completed_button.click()
        return self
