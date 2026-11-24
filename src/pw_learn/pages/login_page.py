"""Page object for the saucedemo.com login page.

saucedemo.com is a public demo shop. Its usernames and password are printed
on the login page itself, so they are not secrets. Real credentials belong in
environment variables, never in code (see docs/11-auth-state.md).

Note: this site marks elements with data-test, not data-testid, so these
locators use CSS attribute selectors instead of get_by_test_id.
"""
from playwright.sync_api import Page

from pw_learn.pages.inventory_page import InventoryPage


class LoginPage:
    URL = "https://www.saucedemo.com/"

    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_placeholder("Username")
        self.password = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error = page.get_by_role("alert")

    def open(self) -> "LoginPage":
        self.page.goto(self.URL)
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        """Fill in the form and submit. Use this when the login should fail."""
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()
        return self

    def login_as(self, username: str, password: str) -> InventoryPage:
        """Log in and return the page the user lands on."""
        self.login(username, password)
        self.page.wait_for_url("**/inventory.html")
        return InventoryPage(self.page)