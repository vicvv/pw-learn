PLAYWRIGHT WITH PYTHON - MODULE 11: AUTHENTICATION AND SAVED LOGIN STATE


GOAL

Stop logging in over and over. Most applications need a login before anything useful can be tested, and every test gets a fresh, empty browser context (Module 01). Done naively, that means every single test fills in the login form, which costs a few seconds each and makes the whole suite slower and more fragile.

The answer is to log in once, save the session to a file, and give that file to every test that needs it. This module also covers where credentials belong, and why that saved file is as sensitive as a password.

By the end of this module you can:

- test the login itself: success, wrong password, a locked account, logging out
- save a session with storage_state and reuse it in other tests
- write a logged_in_page fixture that skips the login screen entirely
- keep credentials out of the code, in environment variables
- explain what is in a storage_state file and why it must never be committed
- handle parallel runs, where every worker logs in separately
- log in through the API instead of the UI, when the app allows it

Practice site: saucedemo.com, a public demo shop. Its usernames and password are printed on its own login page, so they are not secrets.


THE PROBLEM

Every test gets a new browser context: no cookies, no storage, nobody logged in. That isolation is what makes tests independent, and it is worth keeping. But it means a hundred tests log in a hundred times.

Logging in through the form costs perhaps three seconds. Across a hundred tests that is five minutes of a suite doing the same thing over and over, and a hundred chances for the login page to be slow, change, or show an unexpected banner. A failure in the login form then breaks every test in the suite, and the reports say nothing about what was actually being tested.

Test the login once, properly. After that, skip it.


WHAT A SESSION IS

When you log in, the server gives the browser something that proves who you are on later requests. Usually that is a cookie, and often also a token kept in the browser's local storage.

Playwright can export all of that from a context:

```python
context.storage_state(path="auth/state.json")
```

The file holds every cookie and every origin's local storage for that context. Giving it to a new context restores the same signed-in state:

```python
context = browser.new_context(storage_state="auth/state.json")
```

The new context starts already logged in. No form, no waiting, no dependency on the login page.


THE STORAGE_STATE FILE IS A CREDENTIAL

This is the part people get wrong. The file does not contain a password, so it looks harmless. It contains something more immediately useful: a live session. Anyone with that file can load it into their own browser and be logged in as that user, with no password needed, until the session expires.

So treat it exactly like a password:

- Keep it out of Git. auth/ is in .gitignore from Module 01.
- Never attach it to a bug report, a chat message or a CI artifact.
- Delete it when the run finishes, which the fixture does in its teardown.
- Prefer a dedicated test account over anyone's real one.
- On CI, let the job create it from secrets each run, rather than storing it anywhere.

A trace (Module 04) has the same problem: it records cookies and network traffic. Both deserve the same care.


LOGGING IN ONCE PER RUN: THE FIXTURE

In tests/conftest.py:

```python
@pytest.fixture(scope="session")
def storage_state_path(browser: Browser, worker_id: str) -> Path:
    AUTH_DIR.mkdir(exist_ok=True)
    path = AUTH_DIR / f"state-{worker_id}.json"

    context = browser.new_context()
    page = context.new_page()
    LoginPage(page).open().login_as(settings.shop_user(), settings.shop_password())
    context.storage_state(path=path)
    context.close()

    yield path
    path.unlink(missing_ok=True)
```

Reading it:

- scope="session" means it runs once, not once per test. That is the whole point.
- It creates its own context, logs in through the page objects, saves the state, and closes the context. The browser used for the login is not reused: only the file matters.
- worker_id is in the file name, for parallel runs (next section).
- yield path hands the file to the tests, and the line after it deletes the file when the run ends (Module 07). A live session is not left lying on disk.
- missing_ok=True means no error if something already removed it.

Then a function-scoped fixture builds a page from that file:

```python
@pytest.fixture
def logged_in_page(browser: Browser, browser_context_args, storage_state_path) -> Page:
    context = browser.new_context(
        **browser_context_args, storage_state=storage_state_path
    )
    page = context.new_page()
    yield page
    context.close()
```

- Each test still gets its own context and page, so tests stay isolated: separate cart, separate page state, no interference.
- Only the session is shared, and a session is read-only as far as the tests are concerned.
- **browser_context_args keeps the settings from Module 07 (the locale), rather than throwing them away.
- The context is created by hand, so this fixture closes it.

A test then looks like this, with no login in sight:

```python
def test_logged_in_page_skips_the_login(logged_in_page: Page):
    inventory = InventoryPage(logged_in_page).open()
    expect(inventory.title).to_be_visible()
```


SHARED SESSION, SEPARATE EVERYTHING ELSE

It is worth being precise about what is shared.

Shared: the cookies and local storage that prove who you are.

Not shared: the page, the context, anything the test does. test_a_second_test_reuses_the_same_session adds an item to the cart, and test_each_test_gets_a_fresh_cart then finds an empty cart. The two tests use the same login and nothing else.

Why the cart is empty: saucedemo keeps the cart in session storage, which storage_state does not save. Other applications keep the cart on the server, and then it would persist, because it belongs to the account rather than the browser.

That distinction matters. A saved session shares whatever the server associates with the account. If your application stores a draft, a cart or a preference server-side, every test using that session sees it, and a test that changes it affects the others. Either clean up afterwards, or give those tests their own account.


PARALLEL RUNS

A session fixture runs once per session, and with -n 4 there are four sessions, one per worker (Module 09). So four logins happen, each in its own process, with nothing coordinating them.

If they all wrote auth/state.json, they would write the same file at the same moment, and a worker could read a half-written file.

The fixture avoids that by putting worker_id in the name: state-master.json without -n, and state-gw0.json, state-gw1.json and so on with it. Each worker has its own file and never touches another's.

Alternatives, depending on the application:

- A lock, so the first worker logs in and the others wait and reuse the file. Fewer logins, more complexity.
- One account per worker, using worker_id to choose. Necessary if the application allows only one active session per account, where a second login would invalidate the first.

Four logins per run is usually fine. The saving is still a hundred logins down to four.


CREDENTIALS

Real usernames and passwords must never be in the code. Anything committed stays in Git's history for good, and in a public repository anyone can read it. Deleting the line later does not help: the secret has to be changed.

src/pw_learn/settings.py reads them from the environment, with a default:

```python
def shop_user() -> str:
    return os.environ.get("SHOP_USER", DEMO_USER)

def shop_password() -> str:
    return os.environ.get("SHOP_PASSWORD", DEMO_PASSWORD)
```

The defaults here are saucedemo's published demo credentials, which the site prints on its own login page. That is only acceptable because they are already public. For a real application there should be no default at all: a missing credential should stop the run with a clear message, not fall back to something.

Where the values come from:

- A .env file in the repo root, read by conftest.py. In .gitignore, never committed. .env.example is committed instead, listing the names with harmless values.
- An environment variable for one run: SHOP_PASSWORD=... pytest
- CI secrets, which the CI system puts into the environment for the job (Module 12).

Never print a password, never put one in a test name, and never assert on one. They end up in logs, reports and traces.


LOGGING IN THROUGH THE API

The fastest login is no browser at all. If the application has a login endpoint, call it, take the session, and build a context from it:

```python
@pytest.fixture(scope="session")
def api_storage_state(playwright, worker_id):
    request = playwright.request.new_context(base_url="https://api.example.com")
    response = request.post("/login", data={
        "username": settings.shop_user(),
        "password": settings.shop_password(),
    })
    assert response.ok
    path = AUTH_DIR / f"api-state-{worker_id}.json"
    request.storage_state(path=path)
    request.dispose()
    return path
```

A request context has storage_state() just as a browser context does, so the cookies the API set can be handed to a browser.

This is not used in this module's tests, because saucedemo has no login API: it is a front-end demo that keeps its session in the browser. The pattern matters for real applications, where it turns a three-second login into about a hundred milliseconds.

When it does not work: a login that sets a token in local storage rather than a cookie needs that token added to the context separately, and single sign-on flows with redirects are often easier to do through the UI once and save.

Whichever way you log in, keep at least one test that logs in through the form. That is the only thing proving the login page still works for a real user.


TESTING THE LOGIN ITSELF

The saved session skips the login for other tests, so the login page needs its own small set of tests:

- the happy path: correct credentials reach the application
- wrong password: a clear message, and the user stays on the login page
- a locked or disabled account: the right message
- logging out: the session really ends

The failure cases matter more than people expect. An application that shows no message, or the wrong one, or that lets a locked user in, is a real problem, and only these tests would notice.

What to assert on a failed login: the message the user sees, and that the URL did not change. Checking the URL matters: without it, a test could pass on a page that showed an error and let the user through anyway.


THE FILES

- src/pw_learn/pages/login_page.py - the LoginPage page object
- src/pw_learn/pages/inventory_page.py - the InventoryPage page object
- src/pw_learn/pages/__init__.py - exports all three page objects
- src/pw_learn/settings.py - shop_user() and shop_password()
- tests/conftest.py - the storage_state_path and logged_in_page fixtures
- tests/test_11_auth_state.py - 12 tests
- .env.example - now also lists SHOP_USER and SHOP_PASSWORD

A note on the locators: saucedemo marks its elements with data-test, not data-testid. get_by_test_id looks for data-testid, so these page objects use CSS attribute selectors such as page.locator('[data-test="inventory-item"]') instead. Playwright can be told to use a different attribute globally with playwright.selectors.set_test_id_attribute("data-test"), but that would break the TodoMVC tests in Modules 02 to 09, which do use data-testid.

The tests:

Logging in through the UI:
- test_login_succeeds - the happy path, marked smoke
- test_login_fails_with_a_wrong_password - the error message, and the URL unchanged
- test_locked_out_user_sees_a_message - saucedemo's locked_out_user
- test_logout_returns_to_the_login_page - the menu, then Logout

Reusing a saved session:
- test_saved_state_file_exists - the file is written, with cookies and origins in it
- test_logged_in_page_skips_the_login - no login steps, straight to the inventory
- test_a_second_test_reuses_the_same_session - the same session, adding to the cart
- test_without_the_state_the_user_is_not_logged_in - a plain page is sent back to the login page
- test_each_test_gets_a_fresh_cart - the session is shared, the cart is not

Credentials:
- test_credentials_have_defaults - with nothing set, the demo values are used
- test_credentials_from_the_environment - environment variables win

A separate user:
- test_a_different_user_in_its_own_context - problem_user logs in in its own context, unaffected by the saved session


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Committing the storage_state file.
It is a live session: anyone with it is logged in as that user. auth/ is in .gitignore, and the fixture deletes the file at the end of the run.

Trap 2 - Credentials in the code.
A password in a committed file stays in Git's history for good. Deleting the line later is not enough: the password itself must be changed. Read credentials from the environment.

Trap 3 - A default password for a real application.
Harmless for a demo whose credentials are published. For a real system, a missing credential should stop the run, not fall back to something that might be wrong.

Trap 4 - All workers writing the same file.
A session fixture runs once per worker. Without worker_id in the name, four workers write one file at once, and a worker can read a half-written one.

Trap 5 - Assuming a shared session means shared state.
Each test still has its own context and page. What is shared is whatever the server keeps for that account. A draft or a server-side cart does carry over, and one test can then affect another.

Trap 6 - Replacing browser_context_args instead of passing it through.
new_context(storage_state=...) alone throws away the locale and anything else set in Module 07. Pass **browser_context_args as well.

Trap 7 - Skipping the login tests entirely.
If every test uses the saved session and nothing exercises the form, a broken login page passes unnoticed until a user finds it.

Trap 8 - Asserting only on the error message for a failed login.
Check the URL too. Otherwise a test passes on an application that shows an error and logs the user in anyway.

Trap 9 - An expired session.
A long run, or a reused file from yesterday, can hit a session that has expired, and tests fail in confusing ways as if logged out. Create the file during the run, not before it.

Trap 10 - Sharing one account between parallel workers.
If the application allows only one active session per account, each new login invalidates the previous one, and workers log each other out. Use one account per worker.

Trap 11 - A password in the output.
pytest prints local variables in a failure report, and traces record network traffic. Never print, assert on, or pass a password through anything that ends up in a report.

Trap 12 - get_by_test_id on an application that uses a different attribute.
saucedemo uses data-test, so get_by_test_id("error") finds nothing. Worse, a test asserting to_have_count(0) passes anyway, because a locator matching nothing satisfies it. Check the actual attribute before assuming.


HANDS-ON PRACTICE

1. Run the Module 11 tests:

```
pytest tests/test_11_auth_state.py -v
```

   Expect 12 passed. The first test that needs it triggers the login fixture, which is why one test takes noticeably longer than the rest. A plain "pytest" now runs 126 tests: 124 passed, 1 xfailed and 1 rerun.

2. Watch the saved session skip the login:

```
pytest tests/test_11_auth_state.py --headed --slowmo 400 -k skips_the_login
```

   The browser opens straight on the inventory page. No login form appears, because the session came from the file.

3. Look at what is in the file. The fixture deletes it at the end of the run, so write a copy first:

```
python -c "
from playwright.sync_api import sync_playwright
from pw_learn.pages import LoginPage
from pw_learn import settings
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    LoginPage(context.new_page()).open().login_as(settings.shop_user(), settings.shop_password())
    context.storage_state(path='auth/look.json')
    browser.close()
"
python -m json.tool auth/look.json | head -40
```

   You will see cookies, each with a name, value, domain and expiry, and an origins section with local storage. That is the whole session. Then delete it:

```
rm auth/look.json
```

4. Check Git ignores it:

```
mkdir -p auth && touch auth/test.json
git status
rm auth/test.json
```

   git status must not mention auth/. If it does, add auth/ to .gitignore before going any further.

5. Override the credentials from the environment:

```
SHOP_USER=problem_user pytest tests/test_11_auth_state.py -k credentials -v
```

   The environment variable wins over the default, which is what test_credentials_from_the_environment demonstrates.

If a test fails because saucedemo changed:

The locators live in src/pw_learn/pages/login_page.py and inventory_page.py, so a change is fixed in one place. To find the current locator, run playwright codegen https://www.saucedemo.com/, log in with the demo credentials, and use the Pick locator button on the element.

If the login itself fails, open the site in a browser and check the credentials printed on its login page.

Break it on purpose (this step is MEANT to fail):

1. In tests/conftest.py, in the logged_in_page fixture, remove the storage_state argument so the context is created without it:
   context = browser.new_context(**browser_context_args)
2. Run:

```
pytest tests/test_11_auth_state.py -v -k "skips_the_login or second_test"
```

3. Both tests fail. The context is no longer logged in, so saucedemo sends it back to the login page, and the inventory title and the Add to cart button are never found. That is what every test in a real suite would look like if the session file were missing or expired.
4. Put storage_state=storage_state_path back and run again. Both pass.


MENTAL MODEL

- Each test starts logged out. That isolation is worth keeping.
- Log in once per run, save the session with storage_state, give the file to every test.
- The file is a live session: treat it as a password, keep it out of Git, delete it afterwards.
- Credentials come from the environment, never from the code.
- Parallel runs mean one login and one file per worker.
- Keep a few tests that do log in through the form, including the failure cases.


FOR YOUR OWN APP LATER

- Ask whether the application has a login endpoint. An API login is usually ten to thirty times faster than the form, and it does not break when the login page is redesigned.
- Use a dedicated test account, not anyone's real one, and make sure it can be reset if it gets into a strange state.
- If different tests need different roles (an administrator, a read-only user), make one fixture and one state file per role.
- For single sign-on, logging in once through the UI and saving the state is often the only practical approach, and this module's pattern is exactly that.
- On CI, put the credentials in the CI system's secrets, let the job create the state file during the run, and never upload it as an artifact (Module 12).
- If the application keeps a cart, a draft or preferences on the server, decide deliberately whether tests should share them. If not, give those tests their own account, or clean up in a fixture's teardown.


QUIZ (answers below - try before peeking)

1. Why not simply log in at the start of every test?

2. What exactly is in a storage_state file, and why is it as sensitive as a password?

3. Why is storage_state_path session-scoped but logged_in_page function-scoped?

4. test_a_second_test_reuses_the_same_session adds an item to the cart, and test_each_test_gets_a_fresh_cart then finds the cart empty. Why is that not a contradiction?

5. Why does the state file name include worker_id?

6. logged_in_page passes **browser_context_args to new_context as well as storage_state. What breaks if you leave it out?

7. Every test in a suite uses the saved session, and the login page quietly breaks. When does anyone find out?

8. A failed-login test asserts only that an error message appears. What bug could it miss?

9. In test_11_auth_state.py the locators use page.locator('[data-test="..."]') instead of get_by_test_id("..."). Why?

10. DevOps stretch question: how should credentials and the state file be handled on CI? (Just guess.)


ANSWERS


1. Because it is slow and it makes every test depend on the login page. A three-second login across a hundred tests is five minutes per run, and a change or a hiccup on the login page then fails the whole suite at once, with reports that say nothing about what was being tested.

Why it is worth fixing properly: the login is one feature. It deserves its own small set of tests, run once. Every other test is about something else, and should start from the state it needs, not work its way there through the user interface. The same argument applies to creating test data through an API (Module 10).

What you keep: each test still gets its own context and page, so isolation is unchanged. Only the login is shared.

Common mistakes:
- Logging in once and sharing a single page between tests. That is the order-dependence problem from Module 09. Share the session, not the page.

See: THE PROBLEM.


2. Cookies and local storage for every origin the context visited, which together are whatever proves to the server that you are signed in. It is as sensitive as a password because anyone holding it can load it into a browser and be that user, without knowing the password at all.

Why that is easy to overlook: the file contains no password, so it looks like harmless configuration. What it contains is more immediately useful than a password: a session that is already authenticated, needing no login, no second factor, nothing.

Handle it accordingly: auth/ in .gitignore, deleted in the fixture's teardown, never attached to a bug report or uploaded as a CI artifact. Traces deserve the same care, since they record cookies and network traffic.

Common mistakes:
- Committing it because it is "just a JSON file".
- Keeping yesterday's file to save a login. Besides the security problem, the session may have expired (Trap 9).

See: THE STORAGE_STATE FILE IS A CREDENTIAL.


3. The login should happen once per run, so the fixture that performs it is session-scoped. Each test still needs its own isolated context and page, so the fixture that creates those is function-scoped.

Why both: if logged_in_page were session-scoped, every test would share one page, and whatever one test did would be visible to the next. That is exactly the shared-state problem that makes tests order-dependent. If storage_state_path were function-scoped, the suite would log in once per test and nothing would have been gained.

Splitting them gives the benefit of each: one login, and full isolation. A function-scoped fixture may depend on a session-scoped one, which is why this works (Module 07).

Common mistakes:
- Making both session-scoped for speed, and getting tests that pass only in a particular order.

See: LOGGING IN ONCE PER RUN: THE FIXTURE, and Module 07 on scopes.


4. Because the session is shared and the browser state is not. Each test gets a brand-new context, so the second test's browser knows who the user is, but has no memory of anything the first test did in its own browser.

Why the cart specifically: saucedemo keeps it in session storage, which belongs to the browser tab and is not part of storage_state. A new context starts with none of it.

The important qualification: this is true of saucedemo, not of every application. If the cart were stored on the server against the account, it would carry over, because the session identifies that account. So "a shared session shares whatever the server keeps for that account" is the rule, and the cart happens to fall outside it here.

Common mistakes:
- Assuming a saved session always means a completely clean slate. Check where the application stores the state you care about.

See: SHARED SESSION, SEPARATE EVERYTHING ELSE, and Trap 5.


5. Because with -n a session fixture runs once per worker, not once per run. Without worker_id, four workers would write the same file at the same moment, and one could read a half-written file.

Why this is easy to miss: "session scope" sounds like once per run, and without -n it is. xdist starts a separate pytest session in each worker process, so everything session-scoped happens once per worker (Module 09).

The result is state-master.json without -n, and state-gw0.json, state-gw1.json and so on with it. Each worker owns its file.

Alternatives: a lock so only one worker logs in, or one account per worker if the application allows only one active session per account (Trap 10).

Common mistakes:
- Testing only without -n and assuming it will hold in parallel.

See: PARALLEL RUNS, and Trap 4.


6. The context loses the settings from Module 07, starting with locale="en-US". Anything else configured there, such as a time zone or a viewport, would be lost too, and any --device given on the command line.

Why: browser_context_args is the dictionary every context is normally built from. Creating a context by hand bypasses it unless you pass it through. The result is a context subtly different from the one every other test uses, and the difference may only show up in one odd failure much later, for example a date formatted for the wrong locale.

```python
context = browser.new_context(**browser_context_args, storage_state=storage_state_path)
```

The ** spreads the dictionary into separate arguments, and storage_state is added alongside them.

Common mistakes:
- Hard-coding the locale in this fixture instead. It then has to be kept in step with conftest.py by hand.

See: LOGGING IN ONCE PER RUN: THE FIXTURE, Trap 6, and Module 07.


7. Nobody finds out from the tests. Every test skips the form, so the suite stays green while real users cannot log in at all.

Why: the saved session is created once, and if that still works, nothing else touches the login page. In the worst case the state file is reused from an earlier run, and even the fixture stops exercising the login.

That is the trade-off of this pattern, and it is why the module keeps four tests that go through the form: success, wrong password, locked account, and logout. They are cheap, they run once, and they are the only thing standing between a broken login page and production.

Common mistakes:
- Removing the login tests as redundant once the fixture exists. They are the opposite of redundant.

See: TESTING THE LOGIN ITSELF, and Trap 7.


8. An application that shows the error and logs the user in anyway, or redirects despite the failure. The message would be there, the assertion would pass, and a serious authentication bug would go unnoticed.

Why checking the URL matters: the message proves the application noticed something was wrong. The URL proves it acted on it. Those are different claims, and only the second one is about security.

```python
expect(login.error).to_contain_text("do not match")
expect(page).to_have_url("https://www.saucedemo.com/")
```

For a real application, consider asserting more: that no session cookie was set, and that a protected page still redirects to the login.

Common mistakes:
- Asserting the exact wording of the message. Wording changes often. Use to_contain_text with a stable part (Module 03).

See: TESTING THE LOGIN ITSELF, and Trap 8.


9. Because saucedemo marks its elements with data-test, while get_by_test_id looks for data-testid. The names matched; only the attribute differed.

Why it was worth noticing: the first version of these tests used get_by_test_id and failed with "element(s) not found", even though the aria snapshot in the error clearly showed the element on the page. The snapshot in a Playwright failure is often the quickest way to see that an element exists but the locator is wrong.

The global alternative, playwright.selectors.set_test_id_attribute("data-test"), would make get_by_test_id use the other attribute, but it applies to the whole run and would break every TodoMVC test in Modules 02 to 09, which genuinely use data-testid. A CSS attribute selector affects only the page object that needs it.

One further point worth remembering: a broken locator does not always fail loudly. to_have_count(0) passes when the locator matches nothing, so a test can go green for entirely the wrong reason (Trap 12).

Common mistakes:
- Assuming every application uses data-testid.

See: THE FILES, and Trap 12.


10. Keep the credentials in the CI system's secrets, let the job create the state file during the run, and never upload that file as an artifact.

Why each part:
- Secrets are stored encrypted by the CI system and put into the job's environment as variables, which is exactly what settings.shop_user() and shop_password() already read. No code changes.
- Creating the state file during the run means it is always fresh, so it cannot expire, and nothing is stored between runs.
- Artifacts can be downloaded by anyone with access to the repository, and on a public repository that means anyone at all. A state file in an artifact is a handed-over session. Traces have the same problem, which is why a trace from a logged-in run should never be public either.

In GitHub Actions that looks like:

```yaml
env:
  SHOP_USER: ${{ secrets.SHOP_USER }}
  SHOP_PASSWORD: ${{ secrets.SHOP_PASSWORD }}
```

CI systems also mask secret values in the logs, so an accidental print shows as ***. That is a safety net, not a licence to print them.

Module 12 sets this up.

Common mistakes:
- Committing a .env file with the real credentials so CI can read it.
- Uploading test-results without checking what is in it.

See: CREDENTIALS, Trap 11, and Module 12.
