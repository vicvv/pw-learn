PLAYWRIGHT WITH PYTHON - MODULE 07: FIXTURES, THE PAGE OBJECT MODEL AND DEVICE EMULATION


GOAL

Stop repeating yourself. By now every test opens a page and adds some items with the same few lines, and the same locators appear in file after file. If the app changes one placeholder text, dozens of tests break and each needs fixing.

This module fixes that with two tools, and adds a third:

- Fixtures: setup code written once and given to any test that asks for it, with clean-up afterwards.
- Page objects: classes that hold one page's locators and actions, so a change in the app is fixed in one place.
- Device emulation: running a test as if on a phone, by changing the browser context's settings.

By the end of this module you can:

- write fixtures, including ones with teardown, and choose their scope
- put shared fixtures in conftest.py
- use and override Playwright's built-in fixtures, including browser_context_args
- write a page object, and decide what belongs in it and what does not
- combine page objects with fixtures
- run tests as a phone, from the command line or from a fixture

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tiny local pages built with page.set_content().


FIXTURES: WHAT THEY ARE

You have used fixtures since Module 01: page is one. A fixture is a function that prepares something a test needs. A test asks for it by naming it as an argument, and pytest runs the fixture first and passes in what it returns.

```python
def test_has_title(page: Page):      # "page" is a fixture
    ...
```

The test never calls page(). pytest sees the name, finds the fixture with that name, runs it, and hands the result to the test. That is called dependency injection: the test declares what it needs, and pytest supplies it.

Why fixtures instead of a helper function called at the top of each test:

- Teardown: a fixture can clean up afterwards, even when the test fails. A helper cannot.
- Sharing: fixtures in conftest.py are available to every test, with no import.
- Scope: a fixture can run once per test, once per file, or once for the whole run.
- Composition: fixtures can ask for other fixtures, so setup is built from small pieces.


WRITING A FIXTURE

```python
import pytest

@pytest.fixture
def todo_page(page: Page) -> TodoPage:
    return TodoPage(page).open()
```

- @pytest.fixture marks the function as a fixture. Without it, it is just a normal function, and naming it in a test does nothing useful.
- The function name is the fixture's name. A test asks for it by that name: def test_x(todo_page):
- This fixture itself asks for page, so pytest gives it a fresh page first.
- Whatever it returns is what the test receives.


SETUP AND TEARDOWN WITH YIELD

When something must be cleaned up afterwards, use yield instead of return:

```python
@pytest.fixture
def mobile_page(playwright, browser, browser_name):
    context = browser.new_context(**device)
    page = context.new_page()
    yield page              # the test runs here
    context.close()         # teardown
```

The order of events:

1. pytest runs the fixture up to yield. That is the setup.
2. The value after yield is passed to the test.
3. The test runs.
4. pytest comes back and runs the rest of the fixture. That is the teardown.

The teardown runs whether the test passed or failed. That is the real advantage over clean-up code at the end of a test: if the test fails halfway through, code after the failure never runs, but a fixture's teardown still does.

If the setup itself fails (before yield), the teardown does not run, because there is nothing to clean up yet.


FIXTURES USING FIXTURES

A fixture can ask for other fixtures, and pytest builds the chain:

```python
@pytest.fixture
def todo_page(page):                    # needs page
    return TodoPage(page).open()

@pytest.fixture
def todo_with_items(todo_page):         # needs todo_page, which needs page
    return todo_page.add("buy milk", "walk the dog", "write tests")
```

A test that asks for todo_with_items gets, in order: a fresh page, then the TodoMVC page opened in it, then three items added. The test itself starts with everything ready.

Within one test, each fixture runs only once, even if several things ask for it. Teardown runs in reverse order: the last fixture set up is the first torn down.


CONFTEST.PY

conftest.py is a file pytest finds by its exact name. Every fixture in it is available to every test in that folder and the folders below it, with no import.

- tests/conftest.py is shared by every test in tests/.
- Do not import from conftest.py in a test. pytest makes the fixtures available on its own.
- Fixtures used by one test file only can stay in that file. Shared ones belong in conftest.py.
- To see every fixture available, including Playwright's: pytest --fixtures


SCOPES

A fixture's scope decides how often it runs:

```python
@pytest.fixture                       # scope="function", the default: once per test
@pytest.fixture(scope="module")       # once per test file
@pytest.fixture(scope="session")      # once for the whole test run
```

- function: every test gets its own fresh copy. Safest, and the right default.
- module: shared by every test in one file.
- session: shared by every test in the run. Good for expensive things that do not change, such as reading a settings file or starting a server.

The rule: a fixture can only use fixtures with the same or a wider scope. A session fixture cannot ask for page, because page is function-scoped: the session fixture would outlive it.

Playwright's own fixtures use scope deliberately:

- playwright, browser, browser_name, browser_context_args - session: one browser for the whole run, because starting a browser is slow.
- context, page - function: a fresh, isolated context and page for every test, which is what keeps tests independent.

That combination gives speed and isolation at the same time.


THE BUILT-IN PLAYWRIGHT FIXTURES

pytest-playwright provides these. Any test or fixture can ask for them by name.

- page - a new page in a new context, for each test
- context - the browser context that page belongs to
- browser - the running browser, shared by all tests
- browser_name - "chromium", "firefox" or "webkit", from --browser
- playwright - the Playwright object, with playwright.devices and playwright.request
- browser_context_args - the settings used to create every context
- browser_type_launch_args - the settings used to start the browser (for example headless, slow_mo)
- base_url - the value of --base-url, if given (Module 08)


OVERRIDING BROWSER_CONTEXT_ARGS

Every context pytest-playwright creates is built from the dictionary that browser_context_args returns. Override it in conftest.py to change settings for every test:

```python
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "locale": "en-US"}
```

- The fixture has the same name as Playwright's, so pytest uses yours instead.
- It asks for browser_context_args itself. That gets Playwright's original, which already includes anything from the command line such as --device. Your version adds to it rather than replacing it.
- {**original, "locale": "en-US"} makes a new dictionary with everything from the original, plus or overriding locale.
- It must be session-scoped, like the original. Without scope="session" pytest stops with a ScopeMismatch error.

Useful settings:

```python
{
    "locale": "en-US",                          # browser language, for translated apps (Module 02)
    "timezone_id": "Europe/Berlin",             # time zone, for apps that show times
    "viewport": {"width": 1280, "height": 720}, # window size
    "color_scheme": "dark",                     # dark mode
    "ignore_https_errors": True,                # only for test servers with self-signed certificates
}
```

These apply to every test in the folder. For one test, create a context yourself, as mobile_page does.


AUTOUSE FIXTURES

A fixture with autouse=True runs for every test without being asked for:

```python
@pytest.fixture(autouse=True)
def dismiss_cookie_banner(page):
    ...
```

Useful for something every test genuinely needs, such as closing a cookie banner. Use it sparingly: a test that does not show its setup in its arguments is harder to understand.


THE PAGE OBJECT MODEL

A page object is a class that represents one page (or one part of a page) of the app. It holds:

- the locators for that page
- methods for the things a user does there

Tests then read like a description of what the user does, and the details of how live in one place:

```python
# without a page object
page.get_by_placeholder("What needs to be done?").fill("buy milk")
page.get_by_placeholder("What needs to be done?").press("Enter")
page.get_by_test_id("todo-item").filter(has_text="buy milk").get_by_role("checkbox").check()

# with a page object
todo.add("buy milk")
todo.complete("buy milk")
```

The real benefit is maintenance. When the app changes the placeholder text, you change one line in the page object, and every test that adds an item works again. Without it, you hunt through every file.


WRITING A PAGE OBJECT

TodoPage, in src/pw_learn/pages/todo_page.py:

```python
class TodoPage:
    URL = "https://demo.playwright.dev/todomvc/"

    def __init__(self, page: Page):
        self.page = page
        self.new_todo = page.get_by_placeholder("What needs to be done?")
        self.items = page.get_by_test_id("todo-item")
        ...

    def add(self, *texts: str) -> "TodoPage":
        for text in texts:
            self.new_todo.fill(text)
            self.new_todo.press("Enter")
        return self

    def item(self, text: str) -> Locator:
        return self.items.filter(has_text=text)
```

- __init__ receives the Playwright page and creates the locators. Because locators are lazy (Module 02), nothing is searched yet, so creating them up front is cheap and safe.
- Locators are stored as attributes (self.items, self.counter), so tests can assert on them: expect(todo.counter).to_have_text(...)
- Methods are the actions: add, complete, delete, show, clear_completed.
- item(text) returns a locator, not an action, so a test can do anything with it: check it, assert on it, chain from it.
- URL is a class attribute: one place to change the address.

Why it lives in src/pw_learn/pages/ and not in tests/: it is reusable code, not a test. Putting it in the package means any test file can import it the same way, and pytest never tries to collect it as a test.

Importing it:

```python
from pw_learn.pages import TodoPage
```

That short form works because src/pw_learn/pages/__init__.py imports TodoPage and lists it in __all__. from pw_learn.pages.todo_page import TodoPage also works.


WHAT GOES IN A PAGE OBJECT, AND WHAT DOES NOT

In the page object:

- locators
- actions a user can take: add, complete, delete, log in, search
- small helpers that return locators: item(text)

In the test:

- assertions: what should be true afterwards
- the test's own data: which items, which user

The page object says how to do things. The test says what should happen. Keeping assertions out of page objects matters because different tests check different outcomes of the same action. If complete() asserted that the counter drops by one, a test about something else that also completes an item would fail for the wrong reason.

A common exception: a page object may wait for its own page to be ready after navigating, because that is part of "opening the page", not a test result.


METHODS THAT RETURN SELF

Most TodoPage methods end with return self. That lets actions be chained:

```python
todo.complete("buy milk").complete("write tests").clear_completed()
```

Each method returns the same TodoPage, so the next method can be called straight on it. It is optional, but it keeps short sequences readable.

When an action takes the user to a different page (for example a login that opens a dashboard), the method returns a page object for that new page instead: return DashboardPage(self.page). The test then holds an object for the page the user is actually on. Module 14 does this.


PAGE OBJECTS AND FIXTURES TOGETHER

The two work best combined. The fixture builds the page object and gets the page into the right state, and the test starts with it ready:

```python
@pytest.fixture
def todo_with_items(todo_page):
    return todo_page.add("buy milk", "walk the dog", "write tests")

def test_complete_an_item(todo_with_items):
    todo_with_items.complete("walk the dog")
    expect(todo_with_items.counter).to_have_text("2 items left")
```

The test is two lines, and both are about what it is actually testing.


DEVICE EMULATION

Playwright can make a browser context behave like a phone or tablet. It changes:

- the viewport size (the window width and height)
- the device scale factor (how sharp the screen is)
- the user agent (how the browser describes itself to websites)
- is_mobile (mobile layout behaviour, such as the meta viewport tag)
- has_touch (touch events, so locator.tap() works)

What it does not change: it is still a desktop browser engine on your computer. It is not a real phone, so performance, the real Safari on iOS, and the phone's own keyboard are not tested.


From the command line, for every test:

```
pytest --device "iPhone 13"
pytest --device "Pixel 7"
```

pytest-playwright adds the device's settings to browser_context_args, so every context in the run is that device.


In code, for one test, with its own context (the mobile_page fixture):

```python
@pytest.fixture
def mobile_page(playwright, browser, browser_name):
    if browser_name == "firefox":
        pytest.skip("Firefox does not support mobile emulation")
    device = dict(playwright.devices["iPhone 13"])
    device.pop("default_browser_type", None)
    context = browser.new_context(**device)
    page = context.new_page()
    yield page
    context.close()
```

- playwright.devices is a dictionary of device descriptions, keyed by name. Print the names with: python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(sorted(p.devices)); p.stop()"
- Each description is a dictionary of context settings. ** passes them to new_context as separate arguments.
- default_browser_type says which browser the real device uses (iPhones use WebKit). It describes the device rather than the context, so it is removed before creating the context.
- Firefox does not support is_mobile, so the fixture skips there instead of failing.
- The context is created by hand, so the fixture closes it in its teardown. The page fixture closes its own context for you, but this one is not managed by pytest-playwright.


Which to use:

- --device: run the whole suite as a phone, for example in a separate CI job.
- A fixture like mobile_page: specific tests that are about the mobile layout, running alongside desktop tests.


THE FILES

- src/pw_learn/pages/todo_page.py - the TodoPage page object
- src/pw_learn/pages/__init__.py - exports TodoPage, so tests can import it from pw_learn.pages
- tests/conftest.py - the browser_context_args override and three fixtures
- tests/test_07_fixtures_pom.py - 10 tests

The fixtures in conftest.py:

browser_context_args
  Adds locale "en-US" to every context, so every test runs with the browser set to US English.

todo_page
  Opens the TodoMVC demo and returns a TodoPage.

todo_with_items
  Uses todo_page, then adds three items.

mobile_page
  A page in its own context that behaves like an iPhone 13. Skips on Firefox. Closes the context afterwards.

The tests:

- test_page_object_adds_items - add() puts items in the list
- test_fixture_provides_items - the fixture's three items are there, with the right counter
- test_complete_an_item - complete() ticks one item and the counter drops
- test_delete_an_item - delete() hovers to reveal the button, then clicks it
- test_filter_links - show("Active") and show("Completed") filter the list
- test_chained_actions - methods returning self, chained in one line
- test_each_test_starts_empty - a fresh context has no items, proving the tests are isolated
- test_context_args_set_the_language - the browser reports en-US, from the override
- test_mobile_emulation - the browser reports an iPhone and a narrow window
- test_todo_on_a_phone - the same page object works on the emulated phone


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Forgetting @pytest.fixture.
Without the decorator, naming the function in a test does not call it. pytest stops with "fixture 'todo_page' not found".

Trap 2 - Calling a fixture yourself.
todo_page() in a test fails with an error saying fixtures are not meant to be called directly. Ask for it as an argument instead.

Trap 3 - Importing from conftest.py.
pytest makes its fixtures available automatically. Importing them can create a second copy and confusing errors.

Trap 4 - The wrong scope.
A session or module fixture that asks for page (function scope) stops with a ScopeMismatch error. And a browser_context_args override without scope="session" does the same.

Trap 5 - Sharing state through a wide scope.
A module or session fixture that returns something tests change (a list, a page) leaks those changes from one test into the next. Keep anything a test changes function-scoped.

Trap 6 - Clean-up code at the end of the test.
If the test fails halfway, that code never runs. Put clean-up after yield in a fixture.

Trap 7 - Assertions inside page objects.
The page object then decides what counts as success for every test that uses it. Return locators and values, and assert in the test.

Trap 8 - Page objects in tests/ named test_something.py.
pytest tries to collect them as tests. Keep them in src/pw_learn/pages/.

Trap 9 - Replacing browser_context_args instead of extending it.
return {"locale": "en-US"} throws away Playwright's own settings, including --device from the command line. Start from the original: {**browser_context_args, ...}

Trap 10 - Treating emulation as a real phone.
It changes size, touch and user agent in a desktop engine. Layout and touch bugs show up, but not performance or real device quirks.

Trap 11 - A context you created and did not close.
browser.new_context() is not managed by pytest-playwright. Close it in the fixture's teardown, or it stays open until the browser shuts down.

Trap 12 - A test page without a viewport meta tag.
On an emulated phone, a page without <meta name="viewport" content="width=device-width, initial-scale=1"> is laid out 980 pixels wide and shrunk to fit, exactly as a real phone treats an old desktop site. window.innerWidth then reports 980, not the phone's width. Real mobile-friendly pages include the tag. If your own app's pages are 980 wide on a phone emulation, the tag is missing, and that is a real bug to report.

HANDS-ON PRACTICE

1. Run the Module 07 tests:

```
pytest tests/test_07_fixtures_pom.py -v
```

   Expect 10 passed. A plain "pytest" now runs 63 tests: 2 from Module 01, 7 from Module 02, 8 from Module 03, 6 from Module 04, 14 from Module 05, 16 from Module 06 and 10 from Module 07.

2. See every fixture available, including the three new ones:

```
pytest --fixtures tests/test_07_fixtures_pom.py
```

   Your fixtures appear at the end, with their docstrings, under "fixtures defined from conftest".

3. Run the whole file as a phone:

```
pytest tests/test_07_fixtures_pom.py --device "iPhone 13" -v
```

   Expect 10 passed. Every test now runs with the iPhone's settings, from the command line.

4. Watch the phone layout:

```
pytest tests/test_07_fixtures_pom.py --headed --slowmo 500 -k phone
```

   The browser window is the size of a phone.

5. See the setup and teardown order. Add print("setup") before yield and print("teardown") after it in mobile_page, then run:

```
pytest tests/test_07_fixtures_pom.py -s -k mobile_emulation
```

   -s shows the prints: setup, then the test, then teardown. Remove the prints afterwards.

If a test fails because the demo site changed:

The TodoMVC tests rely on the demo site's current placeholder, test ids, labels and button names, which now all live in one place: src/pw_learn/pages/todo_page.py. If they time out on a locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Fix the locator in todo_page.py. Every test that uses it is fixed at once.
- delete() is the most likely to need a change: the delete button only appears when the mouse is over an item. If it fails, hover over an item in codegen and see what it suggests for the button.

test_context_args_set_the_language and test_mobile_emulation use local pages, so they do not depend on any site.

Break it on purpose (this step is MEANT to fail):

1. In src/pw_learn/pages/todo_page.py, change the placeholder text
   page.get_by_placeholder("What needs to be done?")
   to
   page.get_by_placeholder("What needs doing?")
   To find the line: grep -n "What needs to be done" src/pw_learn/pages/todo_page.py
2. Run, stopping at the first failure:

```
pytest tests/test_07_fixtures_pom.py -v -x
```

3. The first test that adds an item fails after 30 seconds, because fill() waits up to the 30-second action timeout for a field that never appears. -x stops there. Without it, seven tests would each wait 30 seconds, which is three and a half minutes.
4. Notice the scale: one wrong line breaks every test that adds an item. Without a page object, those locators would be spread across many files.
5. Change the line back and run again. 10 passed, from one fix in one place.


MENTAL MODEL

- Fixture: setup written once, asked for by name, with teardown after yield.
- conftest.py: fixtures shared by every test in the folder, no import needed.
- Scope: function for anything a test changes, session for expensive things that do not.
- Page object: one page's locators and actions in one class. Tests say what, page objects say how.
- Assertions stay in tests.
- Devices: --device for the whole run, a fixture with its own context for specific tests.


FOR YOUR OWN APP LATER

- Start with a page object for the login page and the main screen. Most tests go through them.
- One class per page, or per large component such as a navigation bar or a data grid that appears on many pages.
- Put a cookie banner or welcome dialog that blocks every page into an autouse fixture, so no test has to deal with it.
- Use browser_context_args to fix the language and time zone, so tests behave the same on every machine and on CI.
- If the app has a mobile layout, a few tests with a device fixture catch the bugs that only appear on narrow screens, such as a menu that collapses into a button.
- Keep page object methods at the level a user thinks: log_in(user), search(term), add_to_cart(item), not click_button_3().


QUIZ (answers below - try before peeking)

1. Why use a fixture instead of a helper function called at the start of each test?

2. In mobile_page, when does context.close() run, and does it run if the test fails?

3. todo_with_items asks for todo_page, which asks for page. What happens, in order, when a test asks for todo_with_items?

4. Why must the browser_context_args override in conftest.py have scope="session"?

5. A teammate adds expect(self.counter).to_have_text("2 items left") at the end of TodoPage.complete(). Why is that a bad idea?

6. The app changes its placeholder from "What needs to be done?" to "Add a task". How many places must you change, and where?

7. Why do TodoPage's methods return self?

8. What is the difference between pytest --device "iPhone 13" and the mobile_page fixture?

9. Why does mobile_page close its context, when tests using page never close anything?

10. DevOps stretch question: you want every test to run on desktop and on a phone in CI, without changing any test. How? (Just guess.)


ANSWERS


1. Because a fixture can clean up afterwards, even when the test fails, and a helper cannot. Fixtures are also shared through conftest.py without imports, can run once per test or once per run (scope), and can be built from other fixtures.

Why: clean-up written at the end of a test only runs if the test gets that far. If an assertion fails halfway, everything after it is skipped, and whatever you opened stays open. A fixture's code after yield always runs. The other advantages add up too: the test lists what it needs in its arguments, so its setup is visible at a glance.

Common mistakes:
- Thinking fixtures are only for Playwright. They are a general pytest feature, used for anything: test data, temporary files, settings.

See: FIXTURES: WHAT THEY ARE, and Trap 6.


2. After the test finishes, and yes, it runs even if the test fails.

Why: pytest runs the fixture up to yield (setup), gives the page to the test, runs the test, and then always comes back to finish the fixture (teardown). Whether the test passed or failed does not matter. That is the point of putting clean-up after yield rather than at the end of the test.

The only case where it does not run is when the setup itself fails before reaching yield, because then there is nothing to clean up.

Common mistakes:
- Thinking teardown is skipped on failure, which is what happens to clean-up code inside a test.

See: SETUP AND TEARDOWN WITH YIELD.


3. pytest works backwards through the chain and runs the fixtures in dependency order: first page (a fresh page in a new context), then todo_page (opens TodoMVC in that page), then todo_with_items (adds three items). The test then receives the TodoPage with three items.

Why: the test only names todo_with_items, but that fixture needs todo_page, which needs page. pytest builds whatever is needed, once each, from the bottom up. Teardown runs in the reverse order after the test.

All three fixtures share the same page: todo_page receives the page pytest created, and todo_with_items receives that same TodoPage. Nothing is created twice.

Common mistakes:
- Thinking the test must also ask for page and todo_page. It does not: pytest resolves the chain itself.

See: FIXTURES USING FIXTURES.


4. Because Playwright's own browser_context_args is session-scoped, and a fixture that overrides it must have the same scope. Without scope="session", pytest stops with a ScopeMismatch error.

Why: the original runs once for the whole run, and Playwright's other session fixtures rely on it. Your version replaces it, so it has to fit in the same place. A function-scoped version would also mean rebuilding the settings for every test, which is pointless because they do not change.

The general rule behind the error: a fixture can only use fixtures of the same or a wider scope.

Common mistakes:
- Thinking the scope only affects speed. Here it is required, not optional.

See: SCOPES, and OVERRIDING BROWSER_CONTEXT_ARGS.


5. Because the page object would then decide what counts as success for every test that completes an item. The check belongs in the test that cares about it.

Why: "2 items left" is only right if there were three items to begin with. A test that starts with five items and completes one would now fail inside complete(), with an error that looks like a bug in completing items. Different tests check different outcomes of the same action, so the action itself must not check any of them.

The rule: page objects say how to do things, tests say what should happen. complete() ticks the box. The test asserts on the counter.

Common mistakes:
- Thinking more checks are always safer. A check in the wrong place makes failures misleading.

See: WHAT GOES IN A PAGE OBJECT, AND WHAT DOES NOT, and Trap 7.


6. One place: the new_todo line in src/pw_learn/pages/todo_page.py.

Why: every test that adds an item goes through TodoPage.add(), which uses self.new_todo, which is defined once in __init__. Change that one locator and every test works again. That is the main reason page objects exist.

The break-it-on-purpose step shows the reverse: one wrong placeholder breaks every test that adds an item.

Common mistakes:
- Searching every test file. With a page object, locators should not appear in tests at all.

See: THE PAGE OBJECT MODEL, and the break-it-on-purpose step.


7. So actions can be chained in one line: todo.complete("buy milk").complete("write tests").clear_completed()

Why: each method returns the same TodoPage object, so the next method can be called on the result straight away. It is a readability choice, not a requirement.

When an action takes the user to a different page, the method returns a page object for that page instead, so the test always holds an object for the page the user is really on.

Common mistakes:
- Thinking return self is needed for the method to work. Without it, the method still works, it just cannot be chained.

See: METHODS THAT RETURN SELF.


8. --device changes every context in the whole run. The mobile_page fixture creates one phone context for the tests that ask for it, while every other test stays on desktop.

Why: --device adds the device's settings to browser_context_args, which every context is built from. mobile_page builds its own context with browser.new_context(), so it does not affect anything else.

Use --device to run the whole suite as a phone, for example as a separate CI job. Use a fixture for specific tests about the mobile layout, mixed in with desktop tests.

Common mistakes:
- Thinking emulation is a real phone. It is a desktop engine with phone settings: size, touch and user agent.

See: DEVICE EMULATION.


9. Because mobile_page created that context itself with browser.new_context(). pytest-playwright only closes the contexts it created for the page and context fixtures.

Why: whatever you open, you close. The page fixture's context is managed by pytest-playwright, which closes it after each test. A context made by hand is your responsibility. Without the close, it stays open until the whole browser shuts down at the end of the run, using memory and possibly carrying state.

The close is after yield, so it runs even if the test fails.

Common mistakes:
- Closing it at the end of the test instead, where a failure would skip it.

See: DEVICE EMULATION, and Trap 11.


10. Run the suite twice in CI: once normally, and once with --device "iPhone 13". The tests do not change at all.

Why: --device applies to every context in the run, so the same tests become phone tests just by changing the command. In GitHub Actions, a matrix runs the same job several times with different settings, for example one job for desktop and one for each device.

```yaml
strategy:
  matrix:
    device: ["", "iPhone 13", "Pixel 7"]
```

Each job then runs pytest with or without --device. Module 12 covers matrices.

Common mistakes:
- Copying every test into a mobile version. Device emulation exists so you do not have to.

See: DEVICE EMULATION, and Module 12 for CI.


End of Module 07. Next up: Module 08, data-driven tests and organisation (parametrize, test data files, markers, skip and xfail, and settings per environment).