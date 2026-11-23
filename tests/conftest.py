"""Shared pytest fixtures for all tests.

pytest finds this file by its name and makes every fixture in it available
to every test in this folder, with no import needed.
"""
from pathlib import Path

import pytest
from playwright.sync_api import Page

from pw_learn import settings
from pw_learn.pages import TodoPage

# Read the repo's .env file, if there is one, before any test runs.
settings.load_env_file(Path(__file__).parent.parent / ".env")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Settings for every browser context. Must be session-scoped, like the original."""
    return {**browser_context_args, "locale": "en-US"}


@pytest.fixture
def todo_page(page: Page) -> TodoPage:
    """The TodoMVC demo, already open."""
    return TodoPage(page).open()


@pytest.fixture
def todo_with_items(todo_page: TodoPage) -> TodoPage:
    """The TodoMVC demo with three items added."""
    return todo_page.add("buy milk", "walk the dog", "write tests")


@pytest.fixture
def mobile_page(playwright, browser, browser_name):
    """A page in its own context that behaves like an iPhone 13."""
    if browser_name == "firefox":
        pytest.skip("Firefox does not support mobile emulation")
    device = dict(playwright.devices["iPhone 13"])
    device.pop("default_browser_type", None)   # describes the device, not a context setting
    context = browser.new_context(**device)
    page = context.new_page()
    yield page                                 # the test runs here
    context.close()                            # teardown: runs even if the test failed