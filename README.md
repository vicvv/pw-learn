PLAYWRIGHT WITH PYTHON - A HANDS-ON LEARNING COURSE


MODULES AT A GLANCE

| #  | Topic                                   | Notes                                                | Code                                   |
|----|-----------------------------------------|------------------------------------------------------|----------------------------------------|
| 01 | Setup                                   | [01-setup.md](DOCS/01-setup.md)                      | `FILES/test_01_setup.py`               |
| 02 | Locators                                | 02-locators.md                                       | `FILES/test_02_locators.py`            |
| 03 | Assertions & auto-waiting               | 03-assertions.md                                     | `FILES/test_03_assertions.py`          |
| 04 | Debugging (Inspector, trace viewer)      | 04-debugging.md                                      | `FILES/test_04_debugging.py`           |
| 05 | Fixtures & Page Object Model            | 05-fixtures-pom.md                                   | `FILES/test_05_fixtures_pom.py`        |
| 06 | Parallel runs & retries                 | 06-parallel-retries.md                               | `FILES/test_06_parallel_retries.py`    |
| 07 | API testing & network mocking           | 07-api-mocking.md                                    | `FILES/test_07_api_mocking.py`         |
| 08 | Authentication & storage state          | 08-auth-state.md                                     | `FILES/test_08_auth_state.py`          |
| 09 | CI/CD with GitHub Actions               | 09-ci-cd.md                                          | `.github/workflows/playwright.yml`     |
| 10 | Visual & accessibility testing          | 10-visual-a11y.md                                    | `FILES/test_10_visual_a11y.py`         |


WHAT THIS IS

Notes and practice code from learning browser test automation with Playwright, Python and pytest, from a first test to tests that run automatically on GitHub Actions.

Each module has a notes file with explanations, traps, a hands-on exercise and a quiz with answers, plus practice code you can run.

All practice code runs against public demo sites, so no account or special access is needed.


WHO IT IS FOR

- Testers and developers who are new to Playwright
- Some basic Python helps: variables, functions, if statements, loops
- You should be comfortable typing commands in a terminal

The course was done on a Mac, so the commands are for macOS (zsh). On Linux they are mostly the same. On Windows, several commands differ.


QUICK START

You need Python 3 and Git.

```
git clone https://github.com/<your-username>/pw-learn.git
cd pw-learn
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest
```

Behind a corporate network, playwright install may fail with a certificate error. See section 4 of DOCS/01-setup.md.


REPO LAYOUT

```
pw-learn/
    README.md              this file
    DOCS/                  notes for each module
    FILES/                 tests (and later conftest.py and page objects)
    .github/workflows/     the GitHub Actions workflow (Module 09)
    pytest.ini             pytest settings
    requirements.txt       Python packages and versions
    .gitignore             files Git must never commit
```

Kept out of Git by .gitignore: .venv/, test-results/, playwright-report/, saved login state, .env files.


NAMING

- Notes: DOCS/NN-topic.md, for example DOCS/02-locators.md
- Tests: FILES/test_NN_topic.py, for example FILES/test_02_locators.py
- NN is a two-digit module number, so files sort in order (01 to 10).
- Test files start with test_ because pytest only collects files with that prefix. They use underscores because Python cannot import a file name with a dash.
- Commit messages: "Module NN: topic"

Three files must keep their exact names because the tools look for them: README.md, pytest.ini and conftest.py.


THE MODULES

Module 01 - Setup
  Notes: DOCS/01-setup.md
  Code:  FILES/test_01_setup.py
  Git repo and .gitignore, virtual environment, installing pytest-playwright and a browser, corporate certificate errors, pytest.ini, a first test, pushing to GitHub.

Module 02 - Locators
  Notes: DOCS/02-locators.md
  Code:  FILES/test_02_locators.py
  get_by_role, get_by_label, get_by_text, get_by_test_id, filtering and chaining locators, and why CSS and XPath break more often.

Module 03 - Assertions and auto-waiting
  Notes: DOCS/03-assertions.md
  Code:  FILES/test_03_assertions.py
  How actions wait automatically, expect() assertions that retry, timeouts, and why time.sleep() is never needed.

Module 04 - Debugging
  Notes: DOCS/04-debugging.md
  Code:  FILES/test_04_debugging.py
  Headed and slow-motion runs, the Playwright Inspector, codegen, traces and the Trace Viewer, screenshots and videos.

Module 05 - Fixtures and Page Object Model
  Notes: DOCS/05-fixtures-pom.md
  Code:  FILES/test_05_fixtures_pom.py, FILES/conftest.py, FILES/pages/
  Custom pytest fixtures, hooks for setup and teardown, and page objects that keep locators out of tests.

Module 06 - Parallel runs and retries
  Notes: DOCS/06-parallel-retries.md
  Code:  FILES/test_06_parallel_retries.py
  Running tests in parallel with pytest-xdist, retries, finding and fixing flaky tests.

Module 07 - API testing and network mocking
  Notes: DOCS/07-api-mocking.md
  Code:  FILES/test_07_api_mocking.py
  The request fixture for API tests, page.route() to mock or block network calls, and waiting for responses.

Module 08 - Authentication and saved login state
  Notes: DOCS/08-auth-state.md
  Code:  FILES/test_08_auth_state.py
  Logging in once and reusing the saved state, credentials in environment variables, keeping auth files out of Git.

Module 09 - CI/CD with GitHub Actions
  Notes: DOCS/09-ci-cd.md
  Code:  .github/workflows/playwright.yml
  Running tests on every push, installing browsers on Linux, repository secrets, sharding, saving reports and traces as artifacts.

Module 10 - Visual and accessibility checks
  Notes: DOCS/10-visual-a11y.md
  Code:  FILES/test_10_visual_a11y.py
  Screenshot comparison, ARIA snapshots, and basic accessibility checks.


HOW EACH NOTES FILE IS ORGANIZED

- Goal
- Explanation with examples
- Why it matters / traps: the mistakes that cause most problems
- Hands-on practice, including a "break it on purpose" step that shows what a failure looks like
- Mental model: a short summary
- Quiz, with answers at the end


RESOURCES

Links may move over time. If one does not work, search for the page title.

- Playwright for Python: https://playwright.dev/python/
- pytest plugin (pytest-playwright): https://playwright.dev/python/docs/test-runners
- pytest documentation: https://docs.pytest.org/
- Python venv: https://docs.python.org/3/library/venv.html
- Pro Git, a free book: https://git-scm.com/book
- GitHub Actions documentation: https://docs.github.com/en/actions


ABOUT THE PRACTICE SITES

The demo sites are run by other people and are sometimes down. If every test fails with a timeout at its first step, open the site in your browser. If it does not load, wait and try again later.

No real data is used anywhere in this repo.