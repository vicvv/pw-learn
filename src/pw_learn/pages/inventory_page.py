"""Page object for the saucedemo.com inventory (products) page.

Note: this site marks elements with data-test, not data-testid, so these
locators use CSS attribute selectors instead of get_by_test_id.
"""
from playwright.sync_api import Locator, Page


class InventoryPage:
    URL = "https://www.saucedemo.com/inventory.html"

    def __init__(self, page: Page):
        self.page = page
        self.title = page.get_by_text("Products", exact=True)
        self.items = page.locator('[data-test="inventory-item"]')
        self.cart_link = page.locator('[data-test="shopping-cart-link"]')
        self.menu_button = page.get_by_role("button", name="Open Menu")
        self.logout_link = page.locator('[data-test="logout-sidebar-link"]')

    def open(self) -> "InventoryPage":
        self.page.goto(self.URL)
        return self

    def item(self, name: str) -> Locator:
        return self.items.filter(has_text=name)

    def add_to_cart(self, name: str) -> "InventoryPage":
        self.item(name).get_by_role("button", name="Add to cart").click()
        return self

    def cart_count(self) -> Locator:
        return self.page.locator('[data-test="shopping-cart-badge"]')

    def logout(self) -> None:
        self.menu_button.click()
        self.logout_link.click()