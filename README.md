PLAYWRIGHT WITH PYTHON - A HANDS-ON LEARNING COURSE


MODULES AT A GLANCE

| #  | Topic                                       | Notes                                                     | Code                                                     |
|----|---------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------|
| 00 | Git and GitHub (reference)                  | [00-git-github.md](docs/00-git-github.md)                 | -                                                        |
| 01 | Setup                                       | [01-setup.md](docs/01-setup.md)                           | `tests/test_01_setup.py`                                 |
| 02 | Locators and locator strictness             | [02-locators.md](docs/02-locators.md)                     | `tests/test_02_locators.py`                              |
| 03 | Assertions & auto-waiting                   | [03-assertions.md](docs/03-assertions.md)                 | `tests/test_03_assertions.py`                            |
| 04 | Debugging & command-line options            | [04-debugging.md](docs/04-debugging.md)                   | `tests/test_04_debugging.py`                             |
| 05 | Actions and input                           | 05-actions-input.md                                       | `tests/test_05_actions_input.py`                         |
| 06 | Complex interactions                        | 06-complex-interactions.md                                | `tests/test_06_complex_interactions.py`                  |
| 07 | Fixtures, Page Object Model & devices       | 07-fixtures-pom.md                                        | `tests/test_07_fixtures_pom.py`, `src/pw_learn/pages/`   |
| 08 | Data-driven tests & organisation            | 08-data-driven.md                                         | `tests/test_08_data_driven.py`                           |
| 09 | Parallel runs, retries & flaky tests        | 09-parallel-retries.md                                    | `tests/test_09_parallel_retries.py`                      |
| 10 | API testing & network mocking               | 10-api-mocking.md                                         | `tests/test_10_api_mocking.py`                           |
| 11 | Authentication & saved login state          | 11-auth-state.md                                          | `tests/test_11_auth_state.py`                            |
| 12 | CI/CD & reporting                           | 12-ci-cd-reporting.md                                     | `.github/workflows/playwright.yml`                       |
| 13 | Visual & accessibility testing              | 13-visual-a11y.md                                         | `tests/test_13_visual_a11y.py`                           |
| 14 | Capstone project                            | 14-capstone.md                                            | `tests/test_14_capstone.py`, `src/pw_learn/pages/`       |
| A  | Appendix: the async API                     | a-async-api.md                                            | -                                                        |
| B  | Appendix: code quality (optional)           | b-code-quality.md                                         | -                                                        |


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
    .github/workflows/         the GitHub Actions workflow (Module 12)
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


INSTALLING THE PACKAGE

The repo is also an installable Python package called pw_learn. pyproject.toml describes it, and the code lives in src/pw_learn/. There are three ways to install it.

1. Editable, for working on the course (the normal way):

```
pip install -e .
```

- Run it from the repo root, with the venv active. The dot means "the package in this folder".
- -e (editable) means Python reads the files straight from src/, so a change to a page object takes effect immediately, with no reinstall.
- pip install -r requirements.txt does this too, because its last line is -e .

2. A normal, fixed copy, from the repo folder:

```
pip install .
```

Python gets a copy of the package as it is now. Later changes to src/ are not picked up until you install again. Useful when you only want to use the page objects, not change them.

3. Straight from GitHub, into another project, without cloning:

```
pip install "git+https://github.com/<your-username>/pw-learn.git"
```

- pip downloads the repo and installs the pw_learn package.
- Add @main or a tag name at the end to choose a version: "git+https://github.com/<your-username>/pw-learn.git@main"
- For a private repo, this needs access to it. Over SSH: pip install "git+ssh://git@github.com/<your-username>/pw-learn.git"

What gets installed: only the pw_learn package (src/pw_learn/, the page objects and helpers). The tests, docs and settings files stay in the repo.

Installing the package also installs pytest-playwright (and with it pytest and Playwright), because pyproject.toml lists