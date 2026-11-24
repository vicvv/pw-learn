"""Module 11 - Authentication and saved login state.

Logging in through the UI, saving the session to a file, reusing it so tests
skip the login screen, and keeping credentials out of the code.

Practice site: saucedemo.com, a public demo shop whose usernames and password
are printed on its own login page.
Run from the repo root with the venv active:
    pytest tests/test_11_auth_state.py -v
"""
import json

import pytest
from playwright.sync_api import Browser, Page, expect

from pw_learn import settings
from pw_learn.pages import InventoryPage, LoginPage


# ---------- LOGGING IN THROUGH THE UI ----------

@pytest.mark.smoke
def test_login_succeeds(page: Page):
    inventory = LoginPage(page).open().login_as(
        settings.shop_user(), settings.shop_password()
    )
    expect(inventory.title).to_be_visible()
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")


def test_login_fails_with_a_wrong_password(page: Page):
    login = LoginPage(page).open()
    login.login(settings.shop_user(), "not-the-password")
    expect(login.error).to_contain_text("Username and password do not match")
    expect(page).to_have_url("https://www.saucedemo.com/")


def test_locked_out_user_sees_a_message(page: Page):
    login = LoginPage(page).open()
    login.login("locked_out_user", settings.shop_password())
    expect(login.error).to_contain_text("locked out")


def test_logout_returns_to_the_login_page(page: Page):
    inventory = LoginPage(page).open().login_as(
        settings.shop_user(), settings.shop_password()
    )
    inventory.logout()
    expect(page.get_by_role("button", name="Login")).to_be_visible()


# ---------- REUSING A SAVED SESSION ----------

def test_saved_state_file_exists(storage_state_path):
    assert storage_state_path.exists()
    state = json.loads(storage_state_path.read_text())
    assert "cookies" in state
    assert "origins" in state


@pytest.mark.smoke
def test_logged_in_page_skips_the_login(logged_in_page: Page):
    inventory = InventoryPage(logged_in_page).open()
    expect(inventory.title).to_be_visible()
    expect(logged_in_page).to_have_url("https://www.saucedemo.com/inventory.html")


def test_a_second_test_reuses_the_same_session(logged_in_page: Page):
    inventory = InventoryPage(logged_in_page).open()
    inventory.add_to_cart("Sauce Labs Backpack")
    expect(inventory.cart_count()).to_have_text("1")


def test_without_the_state_the_user_is_not_logged_in(page: Page):
    page.goto(InventoryPage.URL)
    # saucedemo sends a logged-out visitor back to the login page.
    expect(page).to_have_url("https://www.saucedemo.com/")


def test_each_test_gets_a_fresh_cart(logged_in_page: Page):
    """The session is shared, but the cart from the previous test is not."""
    inventory = InventoryPage(logged_in_page).open()
    expect(inventory.cart_count()).to_have_count(0)


# ---------- CREDENTIALS COME FROM SETTINGS ----------

def test_credentials_have_defaults(monkeypatch):
    monkeypatch.delenv("SHOP_USER", raising=False)
    monkeypatch.delenv("SHOP_PASSWORD", raising=False)
    assert settings.shop_user() == settings.DEMO_USER
    assert settings.shop_password() == settings.DEMO_PASSWORD


def test_credentials_from_the_environment(monkeypatch):
    monkeypatch.setenv("SHOP_USER", "someone_else")
    monkeypatch.setenv("SHOP_PASSWORD", "another-password")
    assert settings.shop_user() == "someone_else"
    assert settings.shop_password() == "another-password"


# ---------- A SEPARATE SESSION FOR A DIFFERENT USER ----------

def test_a_different_user_in_its_own_context(browser: Browser):
    context = browser.new_context()
    page = context.new_page()
    login = LoginPage(page).open()
    login.login("problem_user", settings.shop_password())
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    context.close()
