PLAYWRIGHT WITH PYTHON - APPENDIX B: TROUBLESHOOTING

Errors you are likely to meet, what they mean, and what to do. Grouped by where they come from.


BEFORE ANYTHING ELSE

When a test fails and the reason is not obvious, do this rather than guessing:

```
pytest -k name_of_test --tracing retain-on-failure
playwright show-trace test-results/<folder>/trace.zip
```

Click the red step and look at the Before snapshot. Most failures explain themselves there: the element is missing, something covers it, the page is still loading, the text differs.

Find the folder name with ls test-results, or type test-results/ and press Tab.


SETUP AND INSTALLATION

"command not found: pytest" or "command not found: playwright"
The virtual environment is not active, or the package is not installed in it.

```
source .venv/bin/activate
which python                  # should be inside .venv
pip list
```

"ModuleNotFoundError: No module named 'pw_learn'"
The repository's own package is not installed.

```
pip install -e .
python -c "import pw_learn; print('ok')"
```

"ImportError: cannot import name 'X' from 'pw_learn.pages'"
The name is not exported. Check src/pw_learn/pages/__init__.py imports it and lists it in __all__. Also check the file name has two underscores on each side of init.

"Executable doesn't exist at ... playwright install"
The browser is not downloaded. Each browser is separate:

```
playwright install chromium firefox webkit
```

On Linux or CI, also install the system libraries:

```
playwright install --with-deps chromium
```

Browser downloads fail behind a corporate proxy or TLS inspection
The network substitutes its own certificate, which the installer does not trust. Point Node at the company certificate:

```
export NODE_EXTRA_CA_CERTS=/path/to/company-ca.pem
```

"IndentationError" or a syntax error on a line that looks fine
Usually a file that was pasted twice, so it contains two copies. Check the length:

```
wc -l path/to/file.py
grep -c "^import\|^from" path/to/file.py
```


LOCATORS AND TIMEOUTS

"Timeout 30000ms exceeded ... waiting for get_by_role(...)"
The element was never found. In order of likelihood:

1. The element is inside an iframe. page.get_by_...() cannot see into one. Inspect the element and look upwards for an iframe tag, then use page.frame_locator(...) (06).
2. The locator is wrong. Open playwright codegen <url>, hover over the element, and compare.
3. The application uses a different test attribute. get_by_test_id looks for data-testid; saucedemo uses data-test. Use page.locator('[data-test="x"]') (11).
4. The page never got into the state the test assumed: an earlier step silently did nothing.

Raising the timeout almost never helps. If the element does not exist, more waiting changes nothing.

"strict mode violation: locator resolved to 3 elements"
The locator matches several elements and the action needs one. That is Playwright protecting you from clicking an arbitrary one.

```python
locator.filter(has_text="the one I mean")
locator.first                      # only when any of them genuinely will do
page.get_by_role("button", name="Save", exact=True)
```

"element is not visible" or "element is not enabled"
The element exists but is not ready. The test is probably running ahead of the page. Assert the precondition first:

```python
expect(page.get_by_role("button", name="Save")).to_be_enabled()
```

"<element> intercepts pointer events"
Something is on top of the element: a cookie banner, a modal, a loading overlay, a sticky header. The error names it. Deal with it as a user would, rather than using force=True, which clicks anyway and makes the test lie (05).

A locator matches nothing and the test still passes
to_have_count(0) is satisfied by a locator that matches nothing at all, so a broken locator can look like a passing test. When a test about absence passes, confirm the locator works by asserting it matches something in a case where it should.


ASSERTIONS

"AssertionError: Locator expected to have text 'X', Actual value: Y"
A genuine difference. Check whitespace and case: to_have_text is exact, including surrounding spaces. Use to_contain_text for part of a longer string.

A test passes alone and fails in the suite
Another test is affecting it. Something shared: data on a server, a file, an environment variable, or a module-level variable in the same worker. Narrow it down by running the file, then fewer tests, until it appears (09).

A test fails only sometimes
Flaky. The usual causes, in order: a reading call used as a check, a fixed pause, shared data, order dependence, an animation, a date, an external service. Reproduce it in a loop before trying to fix it:

```
for i in {1..20}; do pytest -q -k name_of_test || break; done
for i in {1..10}; do pytest -q -n auto || break; done
```

A test fails on CI but not locally
CI machines are slower, run Linux, and start with nothing. Common causes: a timing assumption that a slower machine exposes, a missing environment variable or secret, a path that exists only on your Mac, a font difference (visual tests), or a test that depended on data from an earlier local run.

Download the traces artifact and read it (12).


FIXTURES

"fixture 'X' not found"
Either the name is misspelled, the @pytest.fixture decorator is missing, or the fixture is in a file pytest does not read. Shared fixtures belong in tests/conftest.py. List what is available:

```
pytest --fixtures | grep X
```

If it is a plugin fixture, such as assert_snapshot, the plugin is not installed.

"ScopeMismatch: You tried to access the function-scoped fixture page with a session-scoped request object"
A session or module fixture asked for a function-scoped one. A fixture can only use fixtures of the same or wider scope. The browser_context_args override must be scope="session" (07).

"Fixtures are not meant to be called directly"
Something calls the fixture as a function. Ask for it as an argument instead.

A session fixture runs more than once
With -n, each worker runs its own session, so a session fixture runs once per worker. Expected, but it matters for anything with side effects: logins, created data, shared files. Use worker_id to separate them (09, 11).


NETWORK AND MOCKING

A route has no effect
Almost always the pattern or the timing:

- The pattern must match the whole address. Use "**/users", not "users". A single * does not cross slashes.
- The route must be registered before the request is made. page.route comes before page.goto or page.set_content (10).

Check the exact address in a trace's Network tab.

A page hangs after adding a route
The handler did not finish the route. Every handler must call fulfill, abort or continue_. Note the underscore: continue is a Python keyword.

"net::ERR_CERT_COMMON_NAME_INVALID"
The browser does not trust the certificate it received, typically on a network that inspects HTTPS traffic. Avoid depending on external sites: serve test pages from localhost instead (10).

"net::ERR_CONNECTION_REFUSED"
Nothing is listening at that address. The application or test server is not running, or the port is wrong.

Headers read as None
Playwright gives header names in lower case. Use "content-type", not "Content-Type".


AUTHENTICATION

Every test is suddenly logged out
The storage_state file is missing, empty or expired. It should be created during the run, not reused from a previous one. Check the fixture ran and the file exists.

Workers log each other out
The application allows one active session per account, and each worker's login invalidates the others. Give each worker its own account using worker_id (09, 11).

A password appears in the output
pytest prints local variables in failure reports, and traces record network traffic. Never print or assert on a password. On CI, secrets are masked as ***, but that is a safety net, not a plan.


PARALLEL RUNS

"unrecognized arguments: -n"
pytest-xdist is not installed in the active environment.

print() produces nothing with -n
Output happens in the workers and is discarded. Run that test without -n.

The suite is slower with -n than without
Too many workers for the machine. Each worker runs a whole browser. GitHub's standard runners have 2 cores, so -n 2 is the ceiling there. Measure:

```
time pytest -q
time pytest -q -n 2
time pytest -q -n auto
```

Tests fail only in parallel
They are not independent, or they collide on shared data. Give each test its own data with a unique name, and clean up afterwards (09).


VISUAL AND ACCESSIBILITY

Every visual test fails on CI
The reference images were generated on a different platform. Fonts and text rendering differ between macOS and Linux. Generate the references where the tests run, ideally in a container (13).

A visual test fails intermittently
Something on the page moves or changes: an animation, a blinking cursor, a date, an external image. Disable animations, fix the clock, mask the changing element, or compare a smaller element.

"fixture 'assert_snapshot' not found"
pytest-playwright-visual-snapshot is not installed.

axe reports violations on a page that looks fine
Likely the landmark rules: landmark-one-main and region fire on any page without a main element. They are best-practice rules rather than WCAG failures, but they are real. Either add the landmark or select rules by tag (13).

The axe test is red on an existing application
Expected, and asserting zero will not work. Record today's violation IDs as a known-issues list and fail only on new ones.


CI

The workflow does not run at all
Check the file is at .github/workflows/ and is valid YAML. Tabs are not allowed for indentation. GitHub shows a parse error on the Actions tab.

The browser installs and then fails to start on CI
--with-deps is missing. A Linux runner has none of the libraries a browser needs.

The report or trace is not in the artifacts
The upload step was skipped because an earlier step failed. Add if: always() for reports and if: failure() for traces (12).

A secret is empty in the job
Check the name matches exactly, including capitals, and that it is a repository secret rather than an environment secret. Secrets are not available to workflows triggered by a pull request from a fork.

The nightly job never runs
Scheduled runs are in UTC and may start late. GitHub also disables scheduled workflows on repositories with no activity for 60 days.


GIT

A file that should be ignored shows in git status
.gitignore only affects files Git is not already tracking. If it was committed before the rule was added, remove it from tracking:

```
git rm --cached path/to/file
```

Remember that anything ever committed stays in the history, which matters for secrets. A committed password must be changed, not just deleted.

Check nothing sensitive is staged before committing:

```
git status --short
git diff --cached
```


WHEN NOTHING HERE FITS

1. Read the whole error, including the call log. Playwright's errors list what it waited for and what it found.
2. Record a trace and look at the Before snapshot of the failing step.
3. Reduce it: run the one test alone, then cut it down until it either passes or the cause is obvious.
4. Check the obvious context: right environment, right branch, right virtual environment, dependencies up to date.
5. Compare with a test that works. The difference is usually the answer.
