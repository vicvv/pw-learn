PLAYWRIGHT WITH PYTHON - MODULE 01: SETUP


GOAL

Build a working Playwright + pytest project under Git, laid out as an installable Python package, with two passing tests, pushed to GitHub.

By the end of this module you have:

- a Git repo with a .gitignore that keeps junk and secrets out
- a virtual environment with pytest, Playwright and a browser
- your own package (pw_learn) installed in editable mode
- pinned versions in requirements.txt
- two passing tests, pushed to GitHub

Order matters: folder -> git init -> .gitignore -> venv -> install -> package -> test -> commit -> push. Creating .gitignore before the first git add means junk (.venv, reports, secrets) can never be committed by accident.


THE PROJECT LAYOUT

```
pw-learn/
    src/
        pw_learn/              the package: code the tests import
            __init__.py
            pages/             page objects and helpers (Module 06)
                __init__.py
                todo_page.py
    tests/                     test files, plus conftest.py
        conftest.py
        test_01_setup.py
    docs/                      notes for each module
    .github/workflows/         the CI workflow (Module 10)
    pyproject.toml             describes the package, so pip can install it
    pytest.ini                 pytest settings
    requirements.txt           pinned versions, plus the package itself
    README.md
    .gitignore
```

Why this layout:

- Tests live in tests/. Reusable code (page objects, helpers) lives in a real Python package under src/.
- The repo is called pw-learn, but the package is pw_learn, with an underscore, because Python cannot import a name with a dash.
- Tests import from the installed package, for example: from pw_learn.pages.todo_page import TodoPage
- The src/ folder means Python can only find pw_learn after it has been installed. That sounds strict, but it keeps tests honest: they always use the package exactly as it is installed, not whatever file happens to be in the current folder.


1. CREATE THE PROJECT AND GIT REPO

```
mkdir -p pw-learn/docs pw-learn/tests pw-learn/src/pw_learn/pages
cd pw-learn
pwd
git init -b main
```

- mkdir -p creates all these folders at once, including the parent folders.
- pwd shows where you are. Always check it before creating a venv or a repo.
- git init -b main creates the repo with "main" as the default branch. On Git older than 2.28, run git init, then git branch -M main after the first commit.

Check that Git knows who you are:

```
git config --global user.name
git config --global user.email
```

If either prints nothing, set it (use the same email as your GitHub account):

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Every commit stores this name and email, and anyone who can see the repo can read them. For a private repo that is fine. Before making a repo public, consider GitHub's private no-reply address (GitHub: Settings -> Emails -> "Keep my email addresses private"). Setting it before the first commit is easiest: changing it later means rewriting history.


2. .GITIGNORE - BEFORE ANYTHING IS ADDED

Create .gitignore in the repo root, in VS Code, with these contents:

```
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Python packaging
*.egg-info/
build/
dist/

# Playwright output
test-results/
playwright-report/

# Secrets and saved login state (Module 09)
.env
auth/
*.storage.json

# Editors and OS
.vscode/
.idea/
.DS_Store
```

Check it:

```
cat .gitignore
```

- Lines starting with # are comments.
- A name ending in / means a folder and everything in it.
- *.egg-info/ is a folder that pip install -e . creates (section 6). It must never be committed.


3. VIRTUAL ENVIRONMENT

```
python3 -m venv .venv
source .venv/bin/activate
```

- The prompt now starts with (.venv). Repeat source .venv/bin/activate in every new terminal.
- The venv keeps this project's packages separate from other projects and from the system Python.
- A venv cannot be moved: paths are written into it. Created it in the wrong folder? Delete it and create it again.
- To leave the venv: deactivate
- On Windows, see section 12.


4. CERTIFICATE ERRORS - ONLY ON SOME NETWORKS

Symptom: playwright install (section 5) fails with SELF_SIGNED_CERT_IN_CHAIN, or a similar certificate error.

Why: many company networks inspect HTTPS traffic and re-sign it with the company's own root certificate. A program only accepts that if it trusts the company certificate.

- Your browser uses the Mac's keychain (the Mac's list of trusted certificates). If the company certificate is in the keychain, the browser works.
- Playwright's installer runs on Node.js, which has its own built-in certificate list and ignores the keychain. The company certificate is not on that list, so Node refuses the connection.

Do you need a fix?

- Home network, no VPN: no. Public sites present normal certificates that Node already trusts. Skip this section.
- Company network (office or company Wi-Fi): often yes.
- Company VPN, on any Mac: maybe. Many VPNs only send company traffic through the VPN (split tunneling), and public sites go straight over your home internet. Others send everything through the company network, where it may be inspected.

How to check: try playwright install chromium first. You only need a fix if it fails with a certificate error. You can also see who signed the certificate you are getting:

```
openssl s_client -connect cdn.playwright.dev:443 </dev/null 2>/dev/null | grep "issuer="
```

- A public certificate authority (for example Google Trust Services, Let's Encrypt, DigiCert): no fix needed.
- A company name or a security product: that network re-signs traffic, so a fix is needed.


4A. WORK MAC ON THE COMPANY NETWORK (CERTIFICATE ALREADY INSTALLED)

On a company-managed Mac, IT has usually already put the company certificate in the keychain. Export the certificates the Mac trusts, and point Node at them:

```
mkdir -p "$HOME/.certs"
security find-certificate -a -p /Library/Keychains/System.keychain > "$HOME/.certs/macos-system-ca.pem"
grep -c "BEGIN CERTIFICATE" "$HOME/.certs/macos-system-ca.pem"
grep -q NODE_EXTRA_CA_CERTS ~/.zshrc || echo 'export NODE_EXTRA_CA_CERTS="$HOME/.certs/macos-system-ca.pem"' >> ~/.zshrc
source ~/.zshrc
source .venv/bin/activate
echo $NODE_EXTRA_CA_CERTS
```

- The first grep should print a number greater than 0.
- grep -q X file || echo ... >> file only adds the line if it is not there yet, so it is safe to run again.
- The last echo should print the path to the .pem file.
- The .pem file holds only public certificates, no secrets. It is machine-specific, and it lives outside the repo.

Still failing? Also add the login keychain:

```
security find-certificate -a -p ~/Library/Keychains/login.keychain-db >> "$HOME/.certs/macos-system-ca.pem"
```

Or ask your IT team for the official certificate bundle, or an internal mirror (set with PLAYWRIGHT_DOWNLOAD_HOST).


4B. PERSONAL MAC ON A COMPANY VPN (CERTIFICATE NEEDED)

On a personal Mac the company certificate is not installed, so there is nothing to export. Get it from the company:

1. Ask the company's IT or support desk for the root certificate used for traffic inspection. It usually comes as a .pem, .cer or .crt file, often with their own instructions.
2. Before installing it, check with them:
   - Are personal devices allowed on the VPN? Some companies only allow managed devices.
   - Privacy: once your Mac trusts their root certificate, the company can read your HTTPS traffic whenever it goes through their network. Only install it if you are comfortable with that.
3. Never download a "company certificate" from anywhere else, and never trust one just because a connection showed it to you. Whoever controls a trusted root certificate can read your HTTPS traffic.

Then point Node at the file (use the real file name):

```
mkdir -p "$HOME/.certs"
cp ~/Downloads/company-root.pem "$HOME/.certs/"
grep -q NODE_EXTRA_CA_CERTS ~/.zshrc || echo 'export NODE_EXTRA_CA_CERTS="$HOME/.certs/company-root.pem"' >> ~/.zshrc
source ~/.zshrc
source .venv/bin/activate
```

If IT gave you a .cer file, convert it first, because Node needs PEM text. If the file is already PEM, openssl just rewrites it:

```
openssl x509 -in ~/Downloads/company-root.cer -out "$HOME/.certs/company-root.pem"
```

- If IT also tells you to add the certificate to the keychain (double-click the file, then set it to "Always Trust"), that covers browsers and most other apps. Node still needs NODE_EXTRA_CA_CERTS, because it ignores the keychain.
- When you stop using that VPN, remove the NODE_EXTRA_CA_CERTS line from ~/.zshrc and the certificate from the keychain.


4C. PERSONAL MAC AT HOME (NO VPN)

No certificate is needed.

If you copied ~/.zshrc from a work Mac, it may contain a NODE_EXTRA_CA_CERTS line pointing to a .pem file that does not exist on this Mac. Node warns that it is ignoring the extra certificates and carries on, so it is harmless. To keep things tidy, remove that line.


4D. RULES FOR EVERY CASE

- Never use NODE_TLS_REJECT_UNAUTHORIZED=0. It switches off certificate checking completely.
- Other tools with their own certificate list (for example Python's requests library or Docker) can fail the same way on the same network. Each has its own setting for pointing at a certificate file.


5. INSTALL PYTEST, PLAYWRIGHT AND A BROWSER

With the venv active:

```
pip install pytest-playwright
playwright install chromium
```

- pytest-playwright installs three things: pytest (the test runner), Playwright (the library that drives browsers) and the plugin that connects them, which gives tests the page fixture.
- playwright install chromium downloads the Chromium browser into Playwright's own folder. Firefox and WebKit (the engine behind Safari) are optional: playwright install firefox webkit
- Browser builds are tied to the Playwright version. After upgrading Playwright, run playwright install again.


6. YOUR PACKAGE: PYPROJECT.TOML AND PIP INSTALL -E .

Create the package's files. Each __init__.py marks its folder as a Python package. They can be almost empty.

src/pw_learn/__init__.py:

```python
"""pw_learn - helpers and page objects for the Playwright course."""
```

src/pw_learn/pages/__init__.py:

```python
"""Page objects and helpers."""
```

src/pw_learn/pages/todo_page.py:

```python
"""Page object for the TodoMVC demo. Filled in during Module 06."""
```

pyproject.toml, in the repo root:

```
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "pw-learn"
version = "0.1.0"
description = "A hands-on course for learning Playwright with Python and pytest"
readme = "README.md"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["src"]
```

What it says:

- [build-system] - pip uses setuptools to build the package.
- [project] - the package's name and version, and the Python versions it needs.
- [tool.setuptools.packages.find] where = ["src"] - look for packages inside src/. That is how pip finds pw_learn.

Install it, with the venv active:

```
pip install -e .
python -c "import pw_learn.pages; print('import OK')"
```

- The dot means "the package in this folder".
- -e means editable: Python reads the files straight from src/, so a change to a page object takes effect immediately, with no reinstall.
- The second line should print "import OK".
- The install creates a src/pw_learn.egg-info/ folder. It is in .gitignore (section 2) and must not be committed.


7. PIN VERSIONS: REQUIREMENTS.TXT

requirements.txt lists the exact versions everyone should install, so you, teammates and CI all run the same ones. Pin only the packages the project uses directly, and add the package itself on the last line:

```
pip freeze | grep -i -E "^(playwright|pytest|pytest-playwright)==" > requirements.txt
echo "-e ." >> requirements.txt
cat requirements.txt
```

The result looks like this (your version numbers may differ):

```
playwright==1.xx.x
pytest==9.2.0
pytest-playwright==0.10.0
-e .
```

- == pins an exact version. Playwright changes often, and a new version can change behaviour, so pinning keeps the exercises working.
- -e . on the last line installs your package too, so one command sets up everything.
- Do not use plain pip freeze > requirements.txt in this project. After an editable install, it writes a line with the full path to your own folder, which breaks for everyone else and puts your username in a public file. It also lists every sub-dependency, which makes upgrades harder.

To upgrade later: pip install -U pytest-playwright, run the three lines above again, run playwright install chromium, and run the tests.

Anyone who clones the repo sets up with:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```


8. PYTEST SETTINGS: PYTEST.INI

Create pytest.ini in the repo root with these contents:

```
[pytest]
testpaths = tests
filterwarnings =
    ignore:Session-scoped fixtures defined as instance methods
```

- testpaths = tests: a plain "pytest" only looks in tests/.
- filterwarnings: hides one harmless deprecation warning that comes from the pytest-playwright plugin, not from your code. Other warnings still show. The second line must start with spaces.
- pytest.ini must keep this exact name.
- When pytest reads the file, its output shows a "configfile: pytest.ini" line. If that line is missing, the file is missing or misnamed (check with ls pytest.ini).

Also create an empty tests/conftest.py, which Module 06 fills with shared fixtures:

```python
"""Shared pytest fixtures for all tests. Filled in during Module 06."""
```


9. FIRST TEST: TESTS/TEST_01_SETUP.PY

Create tests/test_01_setup.py with these contents:

```python
"""Module 01 - Setup: first Playwright tests."""
import re

from playwright.sync_api import Page, expect


def test_has_title(page: Page):
    page.goto("https://playwright.dev/")
    expect(page).to_have_title(re.compile("Playwright"))


def test_get_started_link(page: Page):
    page.goto("https://playwright.dev/")
    page.get_by_role("link", name="Get started").click()
    expect(page.get_by_role("heading", name="Installation")).to_be_visible()
```

Paste only the code. A terminal line such as cat > file << 'EOF' inside a .py file makes pytest fail with "NameError: name 'cat' is not defined".

Key ideas:

- page is a pytest fixture from pytest-playwright. Each test gets a brand-new browser context and page: no shared cookies, storage or login. Tests can run in any order, or in parallel.
- expect(...) is a web-first assertion. It retries until the condition passes or the timeout (5 seconds by default) runs out. A plain assert checks only once.
- get_by_role("link", name="Get started") finds the element the way a user or screen reader sees it: "the link called Get started" (Module 02).
- page: Page is a type hint. It helps VS Code suggest methods. pytest ignores it: def test_has_title(page): works the same.


10. RUN THE TESTS

```
pytest
pytest -v
pytest --headed
pytest --headed --slowmo 500
pytest -k title
pytest tests/test_01_setup.py::test_has_title
pytest --browser firefox --browser webkit
```

- pytest: headless (no window), Chromium, everything in tests/
- -v: one line per test, with PASSED or FAILED
- --headed: show the browser window
- --slowmo 500: wait 500 ms before every action, so you can follow it
- -k title: only tests whose name contains "title"
- FILE::TEST: one specific test
- --browser: other browsers (install them first with playwright install firefox webkit)

Module 04 covers all the command-line options in detail.

Expected result: 2 passed.


11. COMMIT AND PUSH

First commit:

```
git status
git add .gitignore pyproject.toml pytest.ini requirements.txt README.md docs src tests
git status
git commit -m "Module 01: setup"
git log --oneline
```

- The first git status shows what is new. .venv/ and pw_learn.egg-info/ must NOT be listed. If they are, fix .gitignore first.
- The second git status shows what will be committed, under "Changes to be committed". Check nothing is missing.
- Add files by name for the first commit, so you see exactly what goes in.

Create an empty repo on GitHub (github.com/new, name pw-learn, leave README, .gitignore and license unticked), then connect and push. With an SSH key set up for GitHub:

```
git remote add origin git@github.com:<your-username>/pw-learn.git
git push -u origin main
```

- -u links your local main branch to main on GitHub. It is needed once, on the first push. After that, plain git push and git pull work.
- docs/00-git-github.md explains every step, and what each error message means.

Everyday loop:

```
git pull
git add <files>
git commit -m "Module NN: topic"
git push
```

Never put a token in the remote URL (https://<token>@github.com/...). It is stored in plain text in .git/config.


12. WINDOWS CHEAT SHEET (POWERSHELL)

The course commands are for macOS (zsh). On Windows, use PowerShell, and these equivalents:

Create and activate the venv:

```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

- Windows uses python, not python3.
- If PowerShell says running scripts is disabled, allow scripts for your user once, then activate again:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

- In the older Command Prompt (cmd), activate with .venv\Scripts\activate.bat instead.

These are the same on every system:

```
pip install -r requirements.txt
playwright install chromium
pytest -v
deactivate
```

Other differences:

- Creating files: create them in VS Code. The cat > file and heredoc commands in these notes do not exist in PowerShell.
- Environment variables, for the current window only:

```
$env:PWDEBUG = "1"
pytest -s tests/test_04_debugging.py
Remove-Item Env:PWDEBUG
```

  The Mac form PWDEBUG=1 pytest ... does not work in PowerShell.

- A permanent variable, such as a certificate file for 4B (applies to new windows):

```
setx NODE_EXTRA_CA_CERTS "C:\certs\company-root.pem"
```

- Paths: pytest accepts forward slashes on Windows too (tests/test_01_setup.py), so the course commands work as written.
- Line endings: Windows saves text files with different line endings. To avoid every line showing as changed in Git, run once: git config --global core.autocrlf true


13. RUNNING ON LINUX AND CI: BROWSER LIBRARIES AND DOCKER

On a Mac, playwright install chromium is all you need. It downloads only the browser. The system libraries Chromium needs to run (for drawing, fonts, sound and so on) already come with macOS.

A Linux machine, such as a GitHub Actions runner or a server, is different. It is often a bare system, and many of those libraries are missing. The browser downloads fine, but it cannot start. The error usually mentions missing shared libraries (files ending in .so) or says the browser failed to launch.

Fix 1 - install the browser together with its Linux libraries:

```
playwright install --with-deps chromium
```

- --with-deps means "also install the system packages this browser needs".
- It is meant for Linux. It uses the system package manager, so it may need sudo, which GitHub's runners already have. You never need it on your Mac.
- The libraries are installed on that machine only. On a runner, which is thrown away after each job, this runs on every job.

Fix 2 - run the tests inside the official Playwright Docker image, which already has Python, the browsers and all their Linux libraries:

```
mcr.microsoft.com/playwright/python
```

Choose an image tag that matches your Playwright version. Browser builds are tied to the library version, so a mismatch can fail in strange ways (for example, "Executable doesn't exist"). Check your version with pip show playwright. The Version line, for example 1.49.0, gives the tag, for example v1.49.0-noble. The tag list is on Playwright's Docker page: https://playwright.dev/python/docs/docker

Trying it on your Mac (needs Docker installed), from the repo root, using your real version in the tag:

```
docker run --rm -it --ipc=host -v "$PWD":/work -w /work mcr.microsoft.com/playwright/python:v<version>-noble /bin/bash
```

Then, inside the container:

```
pip install -r requirements.txt
pytest
```

- --rm deletes the container when you exit, so nothing is left behind.
- -it gives you an interactive shell inside the container.
- --ipc=host is recommended by Playwright for Chromium. Without it, Chromium can run out of memory and crash.
- -v "$PWD":/work makes your repo folder available inside the container as /work, and -w /work starts you in that folder.
- Type exit to leave the container.

Which fix to use:

- Fix 1 is the simplest on GitHub Actions, and Module 10 uses it.
- Fix 2 gives the same environment on every machine (your Mac, a teammate's laptop, any CI system), because everyone uses the same image.
- Either way, a CI machine has no screen, so tests run headless. That is already the default, so do not add --headed in CI.

Traps with Docker:

- Do not use your Mac's .venv inside the container. It was built for macOS and does not work on Linux. Install from requirements.txt inside the container instead, as above.
- The playwright version in requirements.txt must match the image tag. When you upgrade Playwright, change both.
- On a company network, pip install inside a container can fail with a certificate error, because the container does not see your Mac's keychain or NODE_EXTRA_CA_CERTS. The proper fix is to add the company certificate to the image, not to switch off certificate checks.
- Docker Desktop is free for personal use, but larger companies need a paid license. On a work Mac, check what your company provides before installing it.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Test discovery.
pytest only collects files named test_*.py or *_test.py, and only functions that start with test_. Wrong names give "collected 0 items", with no error.

Trap 2 - Name shadowing.
Never call your own file playwright.py or pytest.py. Python imports your file instead of the real package, and the import fails.

Trap 3 - Inactive venv.
A new terminal gives "command not found: pytest" or "No module named playwright". Run source .venv/bin/activate.

Trap 4 - Forgetting pip install -e .
Any import of pw_learn fails with "No module named pw_learn". With the src/ layout, Python only finds the package after it is installed. pip install -r requirements.txt also does it, because of the -e . line.

Trap 5 - Plain pip freeze > requirements.txt.
It writes the full path to your own folder for the editable package, and every sub-dependency. Use the three-line command in section 7.

Trap 6 - time.sleep().
Too short is flaky, too long is slow. Playwright actions wait automatically and expect retries. Wait for a condition, not for time.

Trap 7 - Tests that depend on each other.
Each test gets a fresh browser context. Never rely on a login or data left by another test.

Trap 8 - "Nothing happens".
Headless is the default, so no window appears. The test is still running. Use --headed to watch.

Trap 9 - .gitignore only affects untracked files.
A file that was already committed stays tracked until you run git rm --cached on it.

Trap 10 - A GitHub repo created with a README.
The remote then has a commit your local repo does not have, and the first push is rejected. Create the repo empty.

Trap 11 - Pasting terminal commands into files.
Only file contents go into a file. A cat or EOF line inside a .py file breaks it.

Trap 12 - zsh and # comments.
By default, zsh does not treat # as a comment when you paste commands, so the comment text gets passed along. Enable comments once: echo 'setopt interactive_comments' >> ~/.zshrc

Trap 13 - A typo in a variable name fails silently.
echo $NODE_EXTRA_CA_CERT (missing the S) prints an empty line, not an error.

Trap 14 - Public repo hygiene.
No personal emails, tokens, internal URLs or company data in code, commits or docs. Test only against public demo sites.


HANDS-ON PRACTICE

1. Check the package is installed:

```
python -c "import pw_learn.pages; print('import OK')"
```

   Expect "import OK". If it says "No module named pw_learn", activate the venv and run pip install -e .

2. Run the tests:

```
pytest -v
```

   Expect 2 passed from this module. Near the top of the output, check for "configfile: pytest.ini" and "testpaths: tests". If either is missing, pytest.ini is missing, misnamed or in the wrong folder (check with ls pytest.ini).

3. Watch them run:

```
pytest tests/test_01_setup.py --headed --slowmo 500
```

   Chrome opens playwright.dev, clicks "Get started" and lands on the Installation page.

If a test fails because the site changed:

The tests rely on playwright.dev's current page title, link text and heading. The site can change after these notes were written. If a test times out on a locator:

- Open the site with playwright codegen https://playwright.dev/ and hover over the link or heading. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_01_setup.py, line 15, change
   expect(page.get_by_role("heading", name="Installation")).to_be_visible()
   to
   expect(page.get_by_role("heading", name="Instalation")).to_be_visible()
   To confirm the line number: grep -n "Installation" tests/test_01_setup.py
2. Run pytest tests/test_01_setup.py -v. The test fails after about 5 seconds, because expect keeps retrying before it gives up.
3. Read the error: it names the locator it was waiting for and says it timed out.
4. Change line 15 back and run again. 2 passed.


MENTAL MODEL

- Setup order: folder, git init, .gitignore, venv, install, package, test, commit, push.
- Tests in tests/, reusable code in the pw_learn package under src/, installed with pip install -e .
- requirements.txt: three pinned packages plus -e . - one command sets up everything.
- page: a fresh browser page for every test, given by a fixture.
- expect: retries until true or timeout.
- Headless by default, --headed to watch.


FOR YOUR OWN APP LATER

- Your team will likely keep a shared requirements.txt. Install from it instead of installing packages yourself, so everyone runs the same Playwright version.
- If browser downloads fail at work, ask the team how they solved it. They probably already have a certificate bundle or a mirror.
- Keep tests for a real app in a private repo, and never point practice tests at an internal system.


QUIZ (answers below - try before peeking)

1. A test is saved as checks.py with the function def verify_title(page):, and pytest reports "collected 0 items". Name both problems.

2. You create a helper file called playwright.py next to your tests. Now every test that starts with from playwright.sync_api import Page, expect fails. Why?

3. A teammate adds time.sleep(3) before every assertion "for stability". What is wrong with that?

4. Test A logs in. Test B runs next and expects to already be logged in. Does it work?

5. In a new terminal, pytest gives "command not found". What did you forget?

6. Suppose .venv/ was committed before .gitignore existed. Adding it to .gitignore now does not remove it from the repo. Write the commands that fix it.

7. You created the GitHub repo with "Add a README" ticked, and your first git push -u origin main is rejected. Why, and what are the options?

8. Your browser opens cdn.playwright.dev fine, but playwright install fails with SELF_SIGNED_CERT_IN_CHAIN. Why the difference, and is a fix needed on a home network without a VPN?

9. On a public repo, what personal information is stored in Git even if none of your files contain it?

10. A test starts with from pw_learn.pages.todo_page import TodoPage and fails with "No module named pw_learn". What is the most likely cause?

11. DevOps stretch question: the tests pass on your Mac, but on a GitHub Actions Linux runner Chromium will not start because of missing shared libraries. Name two fixes. (Covered in section 13 and Module 10.)


ANSWERS


1. The file name does not start with test_ (rename it test_checks.py), and the function name does not start with test_ (rename it def test_title(page):).

Why: pytest finds tests by name only. It opens files named test_*.py or *_test.py, and inside them runs functions whose names start with test_. checks.py matches neither pattern, so pytest never opens it. Fixing only one name still gives 0 tests: a correctly named file with def verify_title() is opened, but the function is skipped.

Common mistakes:
- Blaming the missing type hint (page: Page). A type hint only helps VS Code suggest methods. pytest ignores it: def test_title(page): works exactly like def test_title(page: Page):.

See: Trap 1.


2. Name shadowing: Python finds your own playwright.py first and imports it instead of the real Playwright package. Your file has no sync_api, so the import fails. Rename the file (for example helpers.py) and delete the __pycache__/ folder.

Why: when Python imports a name, it looks in the test's own folder before the installed packages. A file called playwright.py hides the real package from every test in that folder. __pycache__/ holds a cached copy of the old file, so delete it too.

The same applies to pytest.py, and to any name that matches a package you use. In this project, reusable code goes in the pw_learn package, which avoids the problem.

Common mistakes:
- Reinstalling Playwright. The real package is fine; Python just never reaches it.

See: Trap 2.


3. It is slow and still unreliable. It always waits 3 seconds, even when the page is ready in a fraction of a second, and on a slow day 3 seconds may not be enough. Playwright already waits, so remove it.

Why:
- Slow: 100 assertions x 3 seconds is 5 extra minutes per run.
- Unreliable: if the page needs 4 seconds (a slow network, a busy CI machine), the test fails anyway.
- Playwright's own waiting moves on the moment the page is ready: actions such as click() wait for the element, and expect() retries for up to 5 seconds.

Common mistakes:
- Making the pause longer "to be safe". Every run gets slower, and it still guarantees nothing.

See: Trap 6, and Module 03.


4. No. Each test gets its own fresh browser context, like a new incognito window, with no cookies and no login from other tests. Test B starts logged out.

Why: Playwright usually reuses one browser for many tests, but gives every test a new, empty context. That isolation is deliberate. Also:
- The order is not guaranteed. Run only Test B (pytest -k test_b), or run tests in parallel (Module 07), and Test A may not run first, or at all.
- If Test A breaks, Test B fails too, although its own feature works.

Each test sets up what it needs. Module 09 shows how to log in once, save the login state, and reuse it safely.

Common mistakes:
- Thinking each test gets its own browser. It gets its own context, which is what keeps it isolated.

See: Trap 7.


5. The venv is not active. Run source .venv/bin/activate (Windows: .venv\Scripts\Activate.ps1).

Why: pytest and Playwright are installed inside the venv only. Every new terminal starts outside it, so the terminal cannot find them. When the venv is active, the prompt starts with (.venv). Activation lasts only until you close that terminal window.

Common mistakes:
- Reinstalling pytest outside the venv. It then ends up in the system Python, mixed with everything else.

See: Trap 3, and section 3.


6. git rm -r --cached .venv, then git commit -m "Stop tracking .venv", then git push.

Why:
- git rm -r --cached .venv removes the folder from the repo but keeps it on your Mac. -r includes everything inside it. --cached means "from Git only".
- The removal is a change like any other, so it has to be committed and pushed.
- After that, .gitignore keeps it out for good.

The old commits still contain .venv. That is harmless for a venv. A password or token is different: removing it in a new commit does not erase it from history, so the secret itself must also be changed.

Common mistakes:
- Deleting the folder itself (rm -rf .venv or in Finder). That deletes your working venv, and you have to rebuild it.
- Running git pull. A pull only brings changes down from GitHub. It cannot remove anything from the repo.

See: Trap 9.


7. GitHub's "Add a README" created a first commit on GitHub that your local repo does not have. The two histories do not connect, so Git refuses to overwrite GitHub's commit. Options: git pull origin main --allow-unrelated-histories, then push; or delete the GitHub repo and create it again empty.

Why: the problem is the commit, not the README file. It would happen whatever file that first commit contained, and even if your local repo has no README at all.

- Combining: --allow-unrelated-histories tells Git it is fine to join the two histories. If both sides have a README.md, Git stops with a conflict in that file: choose a version, then commit and push.
- Starting over: on GitHub, Settings -> "Delete this repository", then create it again with nothing ticked, then git push -u origin main. Simplest for a brand-new repo.
- git push --force replaces GitHub's history with yours. Acceptable on a brand-new personal repo, never on a repo others use.

Common mistakes:
- Deleting the README on GitHub, then pulling. Deleting makes a second commit on GitHub, so the histories still do not connect, and a plain pull refuses unrelated histories.

See: Trap 10, and docs/00-git-github.md.


8. The browser trusts the company certificate through the Mac's keychain. Playwright's installer runs on Node.js, which has its own certificate list and ignores the keychain. On a home network without a VPN, no fix is needed, because the traffic is not re-signed.

Why: company networks often inspect HTTPS traffic and re-sign it with the company's root certificate. The browser accepts it because IT put that certificate in the keychain. Node does not look there, so it rejects the connection. The fix points Node at a file with the trusted certificates: export NODE_EXTRA_CA_CERTS="$HOME/.certs/macos-system-ca.pem" (section 4A), or the file from IT on a personal Mac (section 4B).

At home, cdn.playwright.dev presents its normal certificate from a public authority, which Node already trusts.

Common mistakes:
- Switching off checks with NODE_TLS_REJECT_UNAUTHORIZED=0. That removes all protection.
- Downloading a "company certificate" from anywhere other than the company's IT.

See: section 4.


9. Your name and email. Git stores them as the author of every commit, separately from your files, and anyone who can see the repo can read them with git log.

Why: git log --format='%an <%ae>' prints the name and email of every commit. On GitHub, anyone can also see them by adding .patch to a commit's address. To keep your email private on a public repo, set GitHub's no-reply address before the first commit.

Passwords and keys are a different risk: they only get into Git if a committed file contains them, and they then stay in the history even after the file is deleted. Keep them out with .gitignore and environment variables (Module 09).

Common mistakes:
- Listing passwords and keys only. They can leak too, but only through files you commit. The name and email are there automatically.

See: section 1.


10. The package is not installed in the active venv. Activate the venv and run pip install -e . (or pip install -r requirements.txt, which includes -e .).

Why: with the src/ layout, Python cannot find pw_learn just by looking in the repo folder. It only finds it after pip has installed it. Typical causes: a fresh clone that skipped the install, a new venv, or a different venv being active. Check with:

```
python -c "import pw_learn.pages; print('import OK')"
```

Common mistakes:
- Adding the src/ folder to the path by hand, or moving tests into src/. The install is the fix: it is a one-time step per venv, and editable mode means you never repeat it after code changes.

See: Trap 4, and section 6.


11. Fix 1: playwright install --with-deps chromium, which installs the browser and the Linux libraries it needs. Fix 2: run the tests inside the official Playwright Docker image (mcr.microsoft.com/playwright/python), with a tag that matches your Playwright version.

Why: on a Mac, the libraries Chromium needs come with macOS, so playwright install chromium is enough. A Linux runner is a bare system: the browser downloads but cannot start. --with-deps installs the missing system packages. The Docker image already contains Python, the browsers and every library. Either way, CI has no screen, so tests run headless, which is the default.

Common mistakes:
- Running --with-deps on your Mac. It is for Linux only.
- Mixing an image tag and a requirements.txt version that do not match. Browser builds are tied to the Playwright version.

See: section 13, and Module 10.


End of Module 01. Next up: Module 02, locators (finding elements the way users see them).
