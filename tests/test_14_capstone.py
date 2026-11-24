"""Module 14 - Capstone: a complete suite for one application.

Everything from the course, applied to saucedemo.com as a real project would:
page objects, fixtures, a saved session, data-driven cases, markers, mocking,
and an accessibility check.

Run from the repo root with the venv active:
    pytest tests/test_14_capstone.py -v
    pytest tests/test_14_capstone.py -m smoke
"""
import pytest
from playwright.sync_api import Page, expect

from pw_learn import settings
from pw_learn.pages import CartPage, InventoryPage, LoginPage

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"


@pytest.fixture
def shop(logged_in_page: Page) -> InventoryPage:
    """The product list, already logged in (Module 11)."""
    return InventoryPage(logged_in_page).open()


@pytest.fixture
def cart_with_two_items(shop: InventoryPage) -> CartPage:
    """Two items in the cart, ready for checkout."""
    shop.add_to_cart(BACKPACK)
    shop.add_to_cart(BIKE_LIGHT)
    shop.cart_link.click()
    return CartPage(shop.page)


# ---------- THE MAIN JOURNEY ----------

@pytest.mark.smoke
def test_buy_two_items_end_to_end(cart_with_two_items: CartPage):
    """The journey that matters most: cart, details, overview, confirmation."""
    checkout = cart_with_two_items.checkout()
    checkout.fill_details("Ada", "Lovelace", "12345").continue_to_overview()
    expect(checkout.total).to_be_visible()
    checkout.finish()
    expect(checkout.confirmation).to_be_visible()


@pytest.mark.smoke
def test_add_to_cart_updates_the_badge(shop: InventoryPage):
    shop.add_to_cart(BACKPACK)
    expect(shop.cart_count()).to_have_text("1")
    shop.add_to_cart(BIKE_LIGHT)
    expect(shop.cart_count()).to_have_text("2")


def test_cart_contains_what_was_added(cart_with_two_items: CartPage):
    expect(cart_with_two_items.item_names()).to_have_text([BACKPACK, BIKE_LIGHT])


def test_remove_an_item_from_the_cart(cart_with_two_items: CartPage):
    cart_with_two_items.remove(BACKPACK)
    expect(cart_with_two_items.item_names()).to_have_text([BIKE_LIGHT])


def test_continue_shopping_returns_to_the_products(cart_with_two_items: CartPage):
    cart_with_two_items.continue_shopping.click()
    expect(cart_with_two_items.page).to_have_url(InventoryPage.URL)


# ---------- VALIDATION, DATA-DRIVEN (Module 08) ----------

@pytest.mark.parametrize(
    "first, last, postcode, message",
    [
        pytest.param("", "Lovelace", "12345", "First Name is required", id="no-first-name"),
        pytest.param("Ada", "", "12345", "Last Name is required", id="no-last-name"),
        pytest.param("Ada", "Lovelace", "", "Postal Code is required", id="no-postcode"),
    ],
)
def test_checkout_validation(cart_with_two_items: CartPage, first, last, postcode, message):
    checkout = cart_with_two_items.checkout()
    checkout.fill_details(first, last, postcode).continue_to_overview()
    expect(checkout.error).to_contain_text(message)


# ---------- A DIFFERENT USER (Module 11) ----------

def test_a_blocked_account_cannot_log_in(page: Page):
    login = LoginPage(page).open()
    login.login("locked_out_user", settings.shop_password())
    expect(login.error).to_contain_text("locked out")
    expect(page).to_have_url(LoginPage.URL)


# ---------- RESILIENCE: WHAT IF THE BACKEND FAILS (Module 10) ----------

def test_the_page_survives_a_failed_image_request(shop: InventoryPage):
    """Blocking the product images must not break the page itself."""
    shop.page.route("**/*.jpg", lambda route: route.abort())
    shop.page.reload()
    expect(shop.title).to_be_visible()
    expect(shop.items).to_have_count(6)


# ---------- ACCESSIBILITY (Module 13) ----------

def test_the_product_page_has_no_new_accessibility_problems(shop: InventoryPage):
    axe_module = pytest.importorskip(
        "axe_playwright_python.sync_playwright",
        reason="axe-playwright-python is not installed",
    )
    results = axe_module.Axe().run(shop.page)
    # saucedemo has known problems; this guards against new kinds appearing.
    known = {"color-contrast", "landmark-one-main", "region", "page-has-heading-one"}
    unexpected = [
        violation["id"]
        for violation in results.response["violations"]
        if violation["id"] not in known
    ]
    assert unexpected == [], f"new accessibility problems: {unexpected}"


# ---------- KEYBOARD NAVIGATION (Module 13) ----------

def test_the_login_form_is_reachable_by_keyboard(page: Page):
    LoginPage(page).open()
    page.keyboard.press("Tab")
    expect(page.get_by_placeholder("Username")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_placeholder("Password")).to_be_focused()
