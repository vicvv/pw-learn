PLAYWRIGHT WITH PYTHON - APPENDIX A: QUICK REFERENCE

Everything in one place, to look up rather than read through. Each section names the module that explains it.


SETUP (01)

```
python3 -m venv .venv
source .venv/bin/activate                  # Mac and Linux
.venv\Scripts\activate                     # Windows
pip install -r requirements.txt
playwright install chromium                # or: firefox webkit
playwright install --with-deps chromium    # Linux and CI: system libraries too
pip install -e .                           # this repository's own package
deactivate
```

Check the setup:

```
which python                               # should be inside .venv
pip list
playwright --version
```


RUNNING TESTS

```
pytest                                     # everything
pytest -v                                  # one line per test
pytest -q                                  # quiet
pytest tests/test_05_actions_input.py      # one file
pytest tests/test_05_actions_input.py::test_fill_replaces_existing_text
pytest -k "todo and not flow"              # by name
pytest -m smoke                            # by marker (08)
pytest -m "not slow"
pytest -x                                  # stop at the first failure
pytest --lf                                # only what failed last time
pytest -s                                  # show print() output
pytest --durations=10                      # the ten slowest tests
pytest --fixtures                          # every available fixture
pytest --markers                           # every registered marker
pytest --collect-only                      # list tests without running them
```


PLAYWRIGHT OPTIONS (04)

```
pytest --headed                            # show the browser
pytest --slowmo 500                        # pause 500ms before each action
pytest --browser firefox                   # chromium (default), firefox, webkit
pytest --browser chromium --browser webkit # both, every test twice
pytest --browser-channel chrome            # real Chrome instead of Chromium
pytest --device "iPhone 13"                # emulate a device (07)
pytest --base-url https://staging.example.com   # (08)
pytest --tracing retain-on-failure
pytest --screenshot only-on-failure
pytest --video retain-on-failure
pytest --full-page-screenshot
pytest --output evidence                   # instead of test-results/
```

Debugging:

```
PWDEBUG=1 pytest -s -k name_of_test        # Inspector, paused, no timeouts
playwright show-trace test-results/<folder>/trace.zip
playwright codegen https://example.com
playwright codegen --target python-pytest -o recorded.py https://example.com
```

In code:

```python
page.pause()          # stop here, open the Inspector (needs --headed)
breakpoint()          # stop here, open Python's debugger (needs -s)
```


PARALLEL AND RETRIES (09)

```
pytest -n auto                             # one worker per CPU core
pytest -n 4
pytest -n 4 --dist loadfile                # keep each file on one worker
pytest --reruns 2                          # retry failures
pytest --reruns 2 --reruns-delay 1
```


REPORTS (12)

```
pytest --junit-xml=results.xml             # for tools
pytest --html=report.html --self-contained-html   # for people
```


LOCATORS (02)

In order of preference:

```python
page.get_by_role("button", name="Submit")          # how assistive tech sees it
page.get_by_role("button", name="Submit", exact=True)
page.get_by_label("Email address")                 # form fields
page.get_by_placeholder("What needs to be done?")
page.get_by_text("Welcome back")
page.get_by_test_id("todo-item")                   # data-testid by default
page.get_by_title("Close")
page.get_by_alt_text("Company logo")
page.locator("#id")                                # CSS, when nothing else fits
page.locator('[data-test="checkout"]')             # a different test attribute (11)
page.locator("xpath=//div[@id='x']")               # last resort
```

Common roles: button, link, textbox, checkbox, radio, heading, list, listitem, table, row, cell, dialog, alert, navigation, main, combobox, option, menuitem, img, tab.

Narrowing:

```python
locator.filter(has_text="buy milk")
locator.filter(has_not_text="done")
locator.filter(has=page.get_by_role("button"))
locator.first
locator.last
locator.nth(2)                                     # counting from 0
page.get_by_role("list").get_by_role("listitem")   # chaining
page.frame_locator("iframe[name='inner']")         # inside an iframe (06)
```

Strictness: a locator used for an action must match exactly one element, or it fails. That is deliberate.


ACTIONS (05)

```python
locator.click()
locator.dblclick()
locator.click(button="right")
locator.click(modifiers=["ControlOrMeta"])
locator.click(position={"x": 10, "y": 10})
locator.click(force=True)                   # skips the safety checks: rarely right
locator.hover()
locator.fill("text")                        # replaces; the normal choice
locator.clear()
locator.press_sequentially("text")          # key by key; only when the page reacts
locator.press("Enter")
locator.press("ControlOrMeta+a")            # works on Mac and Windows
locator.check()                             # ends checked, whatever it was
locator.uncheck()
locator.select_option("value")
locator.select_option(label="Large")
locator.select_option(["a", "b"])
locator.set_input_files("file.pdf")         # never click a file input (06)
locator.set_input_files([])
locator.drag_to(target)
locator.focus()
locator.scroll_into_view_if_needed()        # clicks scroll automatically
```

Page:

```python
page.goto("https://example.com")
page.goto("/path")                          # with --base-url
page.reload()
page.go_back()
page.set_content("<p>hello</p>")
page.screenshot(path="x.png", full_page=True)
page.screenshot(mask=[locator])             # hide what changes (13)
page.keyboard.press("Tab")
page.mouse.wheel(0, 500)
page.evaluate("window.innerWidth")
page.add_style_tag(content="* { animation: none !important; }")
```


ASSERTIONS (03)

These retry until they pass or time out. Use them for anything on the page:

```python
expect(locator).to_be_visible()
expect(locator).to_be_hidden()
expect(locator).to_be_enabled()
expect(locator).to_be_disabled()
expect(locator).to_be_checked()
expect(locator).to_be_focused()
expect(locator).to_be_empty()
expect(locator).to_have_text("exact")
expect(locator).to_have_text(["first", "second"])    # a list, in order
expect(locator).to_contain_text("part")
expect(locator).to_have_value("typed")
expect(locator).to_have_values(["a", "b"])
expect(locator).to_have_count(3)
expect(locator).to_have_attribute("href", "/home")
expect(locator).to_have_class(re.compile("completed"))
expect(locator).to_match_aria_snapshot("- button \"Submit\"")     # (13)
expect(page).to_have_title("Shop")
expect(page).to_have_url(re.compile(r"/inventory"))
expect(api_response).to_be_ok()
```

Every one has a not_ form: expect(locator).not_to_be_visible()

Timeouts: expect(locator).to_be_visible(timeout=10_000)

A plain assert is correct for anything that cannot change after you read it: a file, a returned value, a calculated number.

Never use is_visible(), inner_text(), count() or text_content() as a check. They read once and do not wait, which is the main cause of flaky tests.

Never use page.wait_for_timeout(). Every action and assertion already waits.


WAITING FOR EVENTS (06, 10)

Start listening, then act, inside the block:

```python
with page.expect_popup() as info:
    page.get_by_role("link", name="Open").click()
popup = info.value

with page.expect_download() as info: ...
with page.expect_response("**/items") as info: ...
with page.expect_request("**/items") as info: ...
with page.expect_file_chooser() as info: ...
```


DIALOGS (06)

Dismissed automatically unless you register a handler. A handler must answer:

```python
page.once("dialog", lambda dialog: dialog.accept())
page.once("dialog", lambda dialog: dialog.dismiss())
page.once("dialog", lambda dialog: dialog.accept("typed text"))
```


FIXTURES (07)

Built in: page, context, browser, browser_name, playwright, browser_context_args, base_url, worker_id (09), tmp_path, monkeypatch (08).

```python
@pytest.fixture
def thing():
    return make_thing()

@pytest.fixture
def thing_with_teardown():
    resource = open_resource()
    yield resource                 # the test runs here
    resource.close()               # always runs, even on failure

@pytest.fixture(scope="session")   # once per run, or per worker with -n
@pytest.fixture(autouse=True)      # every test, without being asked
```

Overriding context settings, in conftest.py:

```python
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "locale": "en-US"}
```

Useful settings: locale, timezone_id, viewport, color_scheme, ignore_https_errors, storage_state.


PAGE OBJECTS (07)

```python
class LoginPage:
    URL = "https://www.saucedemo.com/"

    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_placeholder("Username")

    def open(self) -> "LoginPage":
        self.page.goto(self.URL)
        return self                 # so calls can be chained

    def login_as(self, user, password) -> "InventoryPage":
        ...
        return InventoryPage(self.page)      # the page the user lands on
```

Locators and actions in the page object. Assertions and test data in the test.


DATA-DRIVEN (08)

```python
@pytest.mark.parametrize("text", ["a", "b"])
@pytest.mark.parametrize("count, label", [(1, "1 item"), (2, "2 items")])
@pytest.mark.parametrize("value", [pytest.param("x" * 100, id="long")])
```

Stacking two decorators runs every combination.

Markers, registered in pytest.ini:

```python
@pytest.mark.smoke
@pytest.mark.skip(reason="...")
@pytest.mark.skipif(sys.platform == "win32", reason="...")
@pytest.mark.xfail(strict=True, reason="known bug ABC-123")
pytest.skip("decided while running")
```

skip: does not apply here. xfail: a known bug, still run, tells you when it is fixed.

Data files:

```python
DATA = Path(__file__).parent / "data"      # never a path relative to the terminal
```

Everything from a CSV is text. Convert with int().


API AND MOCKING (10)

```python
response = api_request_context.get(url, params={"q": "x"})
response = api_request_context.post(url, data={"name": "x"})
response.ok            # a property, not a method
response.status
response.json()
```

Routes must be registered before the request is made, and every handler must finish:

```python
page.route("**/users", lambda route: route.fulfill(
    status=200, content_type="application/json", body=json.dumps(data)))
page.route("**/users", lambda route: route.abort())
page.route("**/users", lambda route: route.continue_())     # note the underscore
page.route("**/users", handler, times=1)
page.unroute("**/users")
```

Inspecting a request: route.request.method, .url, .post_data_json, .headers (lower-case names).

Environment:

```python
page.clock.set_fixed_time("2030-01-15T10:00:00Z")
page.clock.install(time="...")
page.clock.run_for("00:10")            # fires timers along the way
page.clock.fast_forward("01:00")       # jumps, skipping timers
page.context.set_offline(True)
page.context.grant_permissions(["geolocation"])
page.context.set_geolocation({"latitude": 48.8584, "longitude": 2.2945})
```


AUTHENTICATION (11)

```python
context.storage_state(path="auth/state.json")
context = browser.new_context(storage_state="auth/state.json")
```

The file is a live session. Keep it out of Git, delete it afterwards, never upload it.

Credentials come from the environment, never from the code.


VISUAL AND ACCESSIBILITY (13)

```
pytest --update-snapshots       # write or replace the reference images
```

```python
assert_snapshot(page.screenshot())
assert_snapshot(locator.screenshot())              # far more stable
assert_snapshot(page.screenshot(), threshold=0.2)

from axe_playwright_python.sync_playwright import Axe
results = Axe().run(page)
assert results.violations_count == 0, results.generate_report()
```

Reference images are platform-specific and are committed.


CI (12)

```yaml
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: pip}
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps chromium
      - run: pytest -m smoke -n 2 --tracing retain-on-failure
        env:
          SHOP_PASSWORD: ${{ secrets.SHOP_PASSWORD }}
      - if: failure()
        uses: actions/upload-artifact@v4
        with: {name: traces, path: test-results/}
```


GIT

```
git status
git add -A
git commit -m "message"
git push
git log --oneline -5
git diff
git restore path/to/file          # discard changes to a file
```

Never commit: .env, auth/, test-results/, report*.html, results*.xml
Do commit: __snapshots__/, .env.example, everything in src/, tests/ and docs/


THE TEN RULES

1. Locators are lazy and strict (02).
2. expect retries; reading calls do not (03).
3. Never write a fixed pause (03, 05).
4. Record a trace instead of guessing (04).
5. Every test independent: alone, any order, in parallel (09).
6. Setup in fixtures, locators in page objects, assertions in tests (07).
7. Test data and credentials come from outside the code (08, 11).
8. Mock what you do not own; keep some tests against the real thing (10).
9. A rerun hides a failure (09).
10. Automated accessibility checks are a floor, not a certificate (13).
