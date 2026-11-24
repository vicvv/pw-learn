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


@pytest.fixture(scope="session")
def api_request_context(playwright):
    """An HTTP client with no browser, for API tests (Module 10)."""
    context = playwright.request.new_context(
        extra_http_headers={"Accept": "application/json"}
    )
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def local_server():
    """A tiny HTTP server on localhost, so tests have a real origin.

    Browsers only allow geolocation and similar features on a secure origin,
    which means https:// or http://localhost. A page from set_content has no
    origin at all. Using localhost also avoids depending on any external site.
    """
    import http.server
    import socketserver
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>local test page</h1>")

        def log_message(self, *args):
            pass                              # keep the test output clean

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)   # port 0: any free port
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://localhost:{port}/"
    server.shutdown()
    server.server_close()