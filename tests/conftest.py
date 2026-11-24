"""Shared pytest fixtures for all tests.

pytest finds this file by its name and makes every fixture in it available
to every test in this folder, with no import needed.
"""
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page

from pw_learn import settings
from pw_learn.pages import LoginPage, TodoPage

# Read the repo's .env file, if there is one, before any test runs.
settings.load_env_file(Path(__file__).parent.parent / ".env")

AUTH_DIR = Path(__file__).parent.parent / "auth"


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


# ---------- AUTHENTICATION (Module 11) ----------

@pytest.fixture(scope="session")
def storage_state_path(browser: Browser, worker_id: str) -> Path:
    """Log in once per worker and save the session to a file.

    The file holds live cookies and tokens, so auth/ is in .gitignore.
    One file per worker, because with -n every worker runs its own session
    and they would otherwise write the same file at the same moment.
    """
    AUTH_DIR.mkdir(exist_ok=True)
    path = AUTH_DIR / f"state-{worker_id}.json"

    context = browser.new_context()
    page = context.new_page()
    LoginPage(page).open().login_as(settings.shop_user(), settings.shop_password())
    context.storage_state(path=path)
    context.close()

    yield path
    path.unlink(missing_ok=True)              # teardown: do not leave a session behind


@pytest.fixture
def logged_in_page(browser: Browser, browser_context_args, storage_state_path) -> Page:
    """A page that is already logged in, with no login steps in the test."""
    context = browser.new_context(
        **browser_context_args, storage_state=storage_state_path
    )
    page = context.new_page()
    yield page
    context.close()

# ---------- REPORTING (Module 12) ----------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record the page's URL and title on a failed test, so reports show
    where the browser was when it failed."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
    if page is None:
        return
    try:
        report.sections.append(("Browser state", f"url: {page.url}\ntitle: {page.title()}"))
    except Exception:
        pass            # the page may already be closed; never fail the report