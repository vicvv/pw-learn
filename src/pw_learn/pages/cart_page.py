"""Page object for the saucedemo.com cart page.

Note: this site marks elements with data-test, not data-testid, so these
locators use CSS attribute selectors instead of get_by_test_id.
"""
from playwright.sync_api import Locator, Page


class CartPage:
    URL = "https://www.saucedemo.com/cart.html"

    def __init__(self, page: Page):
        self.page = page
        self.title = page.get_by_text("Your Cart", exact=True)
        self.items = page.locator('[data-test="inventory-item"]')
        self.checkout_button = page.locator('[data-test="checkout"]')
        self.continue_shopping = page.locator('[data-test="continue-shopping"]')

    def open(self) -> "CartPage":
        self.page.goto(self.URL)
        return self

    def item(self, name: str) -> Locator:
        return self.items.filter(has_text=name)

    def item_names(self) -> Locator:
        return self.page.locator('[data-test="inventory-item-name"]')

    def remove(self, name: str) -> "CartPage":
        self.item(name).get_by_role("button", name="Remove").click()
        return self

    def checkout(self) -> "CheckoutPage":
        self.checkout_button.click()
        return CheckoutPage(self.page)


class CheckoutPage:
    """The three checkout steps: your details, overview, and confirmation."""

    def __init__(self, page: Page):
        self.page = page
        self.first_name = page.locator('[data-test="firstName"]')
        self.last_name = page.locator('[data-test="lastName"]')
        self.postal_code = page.locator('[data-test="postalCode"]')
        self.continue_button = page.locator('[data-test="continue"]')
        self.finish_button = page.locator('[data-test="finish"]')
        self.error = page.get_by_role("alert")
        self.total = page.locator('[data-test="total-label"]')
        self.confirmation = page.get_by_role("heading", name="Thank you for your order!")

    def fill_details(self, first: str, last: str, postcode: str) -> "CheckoutPage":
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postcode)
        return self

    def continue_to_overview(self) -> "CheckoutPage":
        self.continue_button.click()
        return self

    def finish(self) -> "CheckoutPage":
        self.finish_button.click()
        return self
