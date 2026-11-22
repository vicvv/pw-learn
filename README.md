PLAYWRIGHT WITH PYTHON - A HANDS-ON LEARNING COURSE


MODULES AT A GLANCE

| #  | Topic                                       | Notes                                                     | Code                                                     |
|----|---------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------|
| 00 | Git and GitHub (reference)                  | [00-git-github.md](docs/00-git-github.md)                 | -                                                        |
| 01 | Setup                                       | [01-setup.md](docs/01-setup.md)                           | `tests/test_01_setup.py`                                 |
| 02 | Locators                                    | [02-locators.md](docs/02-locators.md)                     | `tests/test_02_locators.py`                              |
| 03 | Assertions & auto-waiting                   | [03-assertions.md](docs/03-assertions.md)                 | `tests/test_03_assertions.py`                            |
| 04 | Debugging & command-line options            | [04-debugging.md](docs/04-debugging.md)                   | `tests/test_04_debugging.py`                             |
| 05 | Complex interactions                        | 05-complex-interactions.md                                | `tests/test_05_complex_interactions.py`                  |
| 06 | Fixtures, Page Object Model & devices       | 06-fixtures-pom.md                                        | `tests/test_06_fixtures_pom.py`, `src/pw_learn/pages/`   |
| 07 | Parallel runs & retries                     | 07-parallel-retries.md                                    | `tests/test_07_parallel_retries.py`                      |
| 08 | API testing & network mocking               | 08-api-mocking.md                                         | `tests/test_08_api_mocking.py`                           |
| 09 | Authentication & saved login state          | 09-auth-state.md                                          | `tests/test_09_auth_state.py`                            |
| 10 | CI/CD with GitHub Actions                   | 10-ci-cd.md                                               | `.github/workflows/playwright.yml`                       |
| 11 | Visual & accessibility testing              | 11-visual-a11y.md                                         | `tests/test_11_visual_a11y.py`                           |
| 12 | Capstone project                            | 12-capstone.md                                            | `tests/test_12_capstone.py`, `src/pw_learn/pages/`       |


WHAT THIS IS

Notes and practice code from learning browser test automation with Playwright, Python and pytest, from a first test to tests that run automatically on GitHub Actions, ending with a capstone project built from acceptance criteria alone.

Each module has a notes file with explanations, traps, a hands-on exercise and a quiz with detailed answers, plus practice code you can run.

All practice code runs against public demo sites, so no account or special access is needed.


WHO IT IS FOR

- Testers and developers who are new to Playwright
- Some basic Python helps: variables, functions, if statements, loops
- You should be comfortable typing commands in a terminal

The course was done on a Mac, so the commands are for macOS (zsh). On Linux they are mostly the same. For Windows, docs/01-setup.md has a PowerShell cheat sheet (section 12).


QUICK START

You need Python 3.10 or later and Git.

macOS or Linux:

```
git clone https://github.com/<your-username>/pw-learn.git
cd pw-learn
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest
```

Windows (PowerShell):

```
git clone https://github.com/<your-username>/pw-learn.git
cd pw-learn
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
pytest
```

- pip install -r requirements.txt installs the pinned versions of pytest, Playwright and the pytest plugin, and also this repo's own package (pw_learn), because of the -e . line at the end of requirements.txt.
- playwright install chromium downloads the browser. Browsers are not stored in the repo.
- Behind a corporate network, playwright install may fail with a certificate error. See section 4 of docs/01-setup.md.


REPO LAYOUT

```
pw-learn/
    src/
        pw_learn/              the package: code the tests import
            __init__.py
            pages/             page objects and helpers
    tests/                     test files, plus conftest.py (shared fixtures)
    docs/                      notes for each module
    .github/workflows/         the GitHub Actions workflow (Module 10)
    pyproject.toml             describes the package, so pip can install it
    pytest.ini                 pytest settings
    requirements.txt           pinned versions, plus the package itself
    README.md                  this file
    .gitignore                 files Git must never commit
```

- Tests live in tests/. Reusable code (page objects, helpers) lives in a real Python package under src/, installed in editable mode with pip install -e . (done automatically by pip install -r requirements.txt).
- Tests import from the package, for example: from pw_learn.pages.todo_page import TodoPage
- The repo is called pw-learn, but the package is pw_learn, with an underscore, because Python cannot import a name with a dash.

Kept out of Git by .gitignore: .venv/, pw_learn.egg-info/ (created by the editable install), test-results/ (screenshots, videos and traces), playwright-report/, saved login state, and .env files.


NAMING

- Notes: docs/NN-topic.md, for example docs/02-locators.md
- Tests: tests/test_NN_topic.py, for example tests/test_02_locators.py
- NN is a two-digit module number, so files sort in order (01 to 12).
- Test files start with test_ because pytest only collects files with that prefix. They use underscores because Python cannot import a file name with a dash.
- Page objects: src/pw_learn/pages/<page>_page.py, for example todo_page.py
- Commit messages: "Module NN: topic"

Four files must keep their exact names because the tools look for them: README.md, pyproject.toml, pytest.ini and conftest.py.


THE MODULES

Module 00 - Git and GitHub (reference)
  Notes: docs/00-git-github.md
  Creating an empty GitHub repo, the first commit and push in the right order, the everyday loop, cloning on another computer, and what each Git error message means.

Module 01 - Setup
  Notes: docs/01-setup.md
  Code:  tests/test_01_setup.py
  Git repo and .gitignore, virtual environment, installing pytest-playwright and a browser, corporate certificate errors, the src/ package with pyproject.toml and pip install -e ., pinned versions, pytest.ini, a first test, a Windows cheat sheet, and running on Linux or in Docker.

Module 02 - Locators
  Notes: docs/02-locators.md
  Code:  tests/test_02_locators.py
  get_by_role, get_by_label, get_by_text, get_by_test_id, the accessible name, strict mode, filtering and chaining locators, first/nth/last, codegen, and why CSS and XPath break more often.

Module 03 - Assertions and auto-waiting
  Notes: docs/03-assertions.md
  Code:  tests/test_03_assertions.py
  How actions wait automatically, expect() assertions that retry, reading calls that do not wait, timeouts, false positives and false negatives, and why time.sleep() is never needed.

Module 04 - Debugging and command-line options
  Notes: docs/04-debugging.md
  Code:  tests/test_04_debugging.py
  The pytest-playwright command-line options (--headed, --slowmo, --browser, --tracing, --screenshot, --video), page.pause() and PWDEBUG, the Playwright Inspector, codegen, traces and the Trace Viewer, console messages and page errors.

Module 05 - Complex interactions
  Notes: docs/05-complex-interactions.md
  Code:  tests/test_05_complex_interactions.py
  Iframes with frame_locator(), new tabs and popups with expect_popup(), file uploads with set_input_files(), downloads with expect_download(), and browser dialogs.

Module 06 - Fixtures, Page Object Model and device emulation
  Notes: docs/06-fixtures-pom.md
  Code:  tests/test_06_fixtures_pom.py, tests/conftest.py, src/pw_learn/pages/
  Custom pytest fixtures, fixture scopes, page objects that keep locators out of tests, and testing responsive layouts with --device and browser_context_args.

Module 07 - Parallel runs and retries
  Notes: docs/07-parallel-retries.md
  Code:  tests/test_07_parallel_retries.py
  Running tests in parallel with pytest-xdist, retries, finding and fixing flaky tests.

Module 08 - API testing and network mocking
  Notes: docs/08-api-mocking.md
  Code:  tests/test_08_api_mocking.py
  API tests with Playwright's request context, page.route() to mock or block network calls, and waiting for responses.

Module 09 - Authentication and saved login state
  Notes: docs/09-auth-state.md
  Code:  tests/test_09_auth_state.py
  Logging in once and reusing the saved state, credentials in environment variables, and why a storage_state file is as sensitive as a password.

Module 10 - CI/CD with GitHub Actions
  Notes: docs/10-ci-cd.md
  Code:  .github/workflows/playwright.yml
  Running tests on every push, installing browsers on Linux, repository secrets, sharding, and saving reports and traces as artifacts.

Module 11 - Visual and accessibility testing
  Notes: docs/11-visual-a11y.md
  Code:  tests/test_11_visual_a11y.py
  Screenshot comparison, ARIA snapshots, and basic accessibility checks.

Module 12 - Capstone project
  Notes: docs/12-capstone.md
  Code:  tests/test_12_capstone.py, src/pw_learn/pages/
  An end-to-end checkout flow on a public demo shop (saucedemo.com), built with no starter code, only acceptance criteria. It must use page objects, fixtures and saved login state.


HOW EACH NOTES FILE IS ORGANIZED

- Goal
- Explanation with examples
- Why it matters / traps: the mistakes that cause most problems
- Hands-on practice, with the expected results, what to do if a demo site has changed, and a "break it on purpose" step that shows what a failure looks like
- Mental model: a short summary
- For your own app later: how the module applies to a real project
- Quiz, with detailed answers at the end: the direct answer first, then why, the common mistakes, and where to read more


PRACTICE SITES

- https://playwright.dev/ (Module 01)
- https://demo.playwright.dev/todomvc/ (Modules 02 to 06)
- https://www.saucedemo.com/ (Module 12)
- Tiny local pages built inside the tests with page.set_content(), which need no internet at all

Each module lists the sites it uses. These sites are run by other people and are sometimes down. If every test fails with a timeout at its first step, open the site in your browser. If it does not load, wait and try again later.

No real data is used anywhere in this repo.


RESOURCES

Links may move over time. If one does not work, search for the page title.

- Playwright for Python: https://playwright.dev/python/
- pytest plugin (pytest-playwright): https://playwright.dev/python/docs/test-runners
- Playwright Trace Viewer: https://trace.playwright.dev
- pytest documentation: https://docs.pytest.org/
- Python venv: https://docs.python.org/3/library/venv.html
- Python packaging guide (pyproject.toml, editable installs): https://packaging.python.org/
- Pro Git, a free book: https://git-scm.com/book
- Connecting to GitHub with SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- GitHub Actions documentation: https://docs.github.com/en/actions