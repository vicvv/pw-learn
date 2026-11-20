PLAYWRIGHT WITH PYTHON - MODULE 01: SETUP


GOAL

Build a working Playwright + pytest project under Git, with two passing tests, pushed to GitHub.

Order matters: folder -> git init -> .gitignore -> venv -> install -> test -> commit -> push. Creating .gitignore before the first git add means junk (.venv, reports, secrets) can never be committed by accident.


1. CREATE THE PROJECT AND GIT REPO

```
mkdir -p pw-learn/DOCS pw-learn/FILES
cd pw-learn
pwd
git init -b main
```

- pwd shows where you are. Always check it before creating a venv or a repo.
- git init -b main creates the repo with "main" as the default branch. On Git older than 2.28, run git init, then git branch -M main after the first commit.

Check that Git knows who you are:

```
git config --global user.name
git config --global user.email
```

If the repo will be public, protect your email. Every commit stores the author's name and email, and on a public repo anyone can read them. On GitHub: Settings -> Emails -> tick "Keep my email addresses private", copy the no-reply address it shows, then set it for this repo only:

```
git config user.email "<id>+<username>@users.noreply.github.com"
git config user.name "<public display name>"
```

Without --global, these apply to this repo only. Do this before the first commit: changing it later means rewriting history.


2. .GITIGNORE - BEFORE ANYTHING IS ADDED

```
cat > .gitignore << 'EOF'
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Playwright output
test-results/
playwright-report/

# Secrets and saved login state (Module 08)
.env
auth/
*.storage.json

# Editors and OS
.vscode/
.idea/
.DS_Store
EOF
```

The quoted 'EOF' makes the heredoc literal: no variables or commands inside it are expanded.

Check it was written correctly:

```
cat .gitignore
```


3. VIRTUAL ENVIRONMENT AND PACKAGES

```
python3 -m venv .venv
source .venv/bin/activate
pip install pytest-playwright
```

- The prompt now starts with (.venv). Repeat source .venv/bin/activate in every new terminal.
- pytest-playwright installs pytest, the Playwright library and the plugin that connects them.
- The venv keeps this project's packages separate from other projects and from the system Python.
- A venv cannot be moved: paths are written into it. Created in the wrong folder? Delete it and create it again.
- To leave the venv: deactivate


4. CORPORATE NETWORKS ONLY - CERTIFICATE FIX

Symptom: playwright install fails with SELF_SIGNED_CERT_IN_CHAIN.

Why: many corporate networks inspect HTTPS traffic and re-sign it with their own root certificate. The computer trusts it, but Playwright's installer runs on Node.js, which uses its own certificate list and ignores the computer's keychain.

Fix (macOS): export the certificates the Mac already trusts, and point Node at them.

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

Never use NODE_TLS_REJECT_UNAUTHORIZED=0. It switches off certificate checking completely.


5. INSTALL THE BROWSER AND PIN VERSIONS

```
playwright install chromium
pip freeze > requirements.txt
```

- playwright install downloads the browser. Firefox and WebKit are optional: playwright install firefox webkit
- Browser builds are tied to the Playwright version. pip freeze writes the exact versions to requirements.txt, so you, teammates and CI all run the same ones. Run it again whenever you install something new.

Anyone who clones the repo sets up with:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```


6. PYTEST SETTINGS - PYTEST.INI

Create pytest.ini in the repo root, next to DOCS/ and FILES/:

```
cat > pytest.ini << 'EOF'
[pytest]
testpaths = FILES
pythonpath = FILES
EOF
```

- testpaths = FILES: a plain "pytest" only looks in FILES/.
- pythonpath = FILES: later modules can import helpers from FILES/pages/.
- pytest.ini must keep this exact name.


7. FIRST TEST - FILES/TEST_01_SETUP.PY

```
cat > FILES/test_01_setup.py << 'EOF'
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
EOF
```

Key ideas:

- page is a pytest fixture from pytest-playwright. Each test gets a brand-new browser context and page: no shared cookies, storage or login. Tests can run in any order, or in parallel.
- expect(...) is a web-first assertion. It retries until the condition passes or the timeout (5 seconds by default) runs out. A plain assert checks only once.
- get_by_role("link", name="Get started") finds the element the way a user or screen reader sees it: "the link called Get started". This is far more robust than CSS or XPath (Module 02).
- pytest-playwright uses the sync API (playwright.sync_api).


8. RUN THE TESTS

```
pytest
pytest -v
pytest --headed
pytest --headed --slowmo 500
pytest -k title
pytest FILES/test_01_setup.py::test_has_title
pytest --browser firefox --browser webkit
```

- pytest: headless (no window), Chromium, everything in FILES/
- -v: one line per test with PASSED or FAILED
- --headed: show the browser window
- --slowmo 500: wait 500 ms before every action, so you can follow it
- -k title: only tests whose name contains "title"
- FILE::TEST: one specific test
- --browser: other browsers (install them first with playwright install firefox webkit)

Expected result: 2 passed.


9. COMMIT AND PUSH

First commit:

```
git status
git add .gitignore pytest.ini requirements.txt README.md DOCS FILES
git commit -m "Module 01: setup"
git log --oneline
```

- git status must not list .venv/. If it does, stop and fix .gitignore first.
- Add files by name for the first commit, so you see exactly what goes in. Once .gitignore is proven, git add . is fine.

Create the GitHub repo. Option A, GitHub CLI:

```
brew install gh
gh auth status || gh auth login
gh repo create pw-learn --public --source=. --remote=origin --push
```

For gh auth login, choose GitHub.com -> HTTPS -> log in with a web browser.

Option B, the GitHub website: New repository -> name pw-learn -> Public -> leave README, .gitignore and license unticked (the repo must be empty). Then:

```
git remote add origin https://github.com/<your-username>/pw-learn.git
git push -u origin main
```

-u sets the upstream. After that, a plain git push is enough.

Everyday loop for every module:

```
git pull
git add .
git commit -m "Module NN: topic"
git push
```

Start each session with git pull, especially if you ever edit files on the GitHub website.

Never put a token in the remote URL (https://<token>@github.com/...). It is stored in plain text in .git/config. Let gh auth login or the macOS keychain handle the login.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Test discovery.
pytest only collects files named test_*.py or *_test.py, and only functions that start with test_. Wrong names give "collected 0 items", with no error.

Trap 2 - Name shadowing.
Never call your own file playwright.py or pytest.py. Python imports your file instead of the real package, and the import fails.

Trap 3 - Inactive venv.
A new terminal gives "command not found: pytest" or "No module named playwright". Run source .venv/bin/activate.

Trap 4 - time.sleep().
Too short is flaky, too long is slow. Playwright actions wait automatically and expect retries. Wait for a condition, not for time.

Trap 5 - Tests that depend on each other.
Each test gets a fresh browser context. Never rely on a login or data left by another test.

Trap 6 - "Nothing happens".
Headless is the default, so no window appears. The test is still running. Use --headed to watch.

Trap 7 - .gitignore only affects untracked files.
A file that was already committed stays tracked until you run git rm --cached on it.

Trap 8 - A GitHub repo created with a README.
The remote then has a commit your local repo does not have, and the push is rejected. Create the repo empty.

Trap 9 - zsh and # comments.
By default, zsh does not treat # as a comment when you paste commands, so the comment text gets passed along. Enable comments once: echo 'setopt interactive_comments' >> ~/.zshrc

Trap 10 - A typo in a variable name fails silently.
echo $NODE_EXTRA_CA_CERT (missing the S) prints an empty line, not an error.

Trap 11 - Public repo hygiene.
No personal emails, tokens, internal URLs or company data in code, commits or docs. Test only against public demo sites.


HANDS-ON PRACTICE

1. Run the tests and confirm 2 passed:

```
pytest -v
```

2. Watch them run:

```
pytest --headed --slowmo 500
```

Break it on purpose (this step is MEANT to fail):

1. In FILES/test_01_setup.py, line 15, change
   expect(page.get_by_role("heading", name="Installation")).to_be_visible()
   to
   expect(page.get_by_role("heading", name="Instalation")).to_be_visible()
   To confirm the line number: grep -n "Installation" FILES/test_01_setup.py
2. Run pytest -v. The test fails after about 5 seconds, because expect keeps retrying before it gives up.
3. Read the error: it names the locator it was waiting for and says it timed out.
4. Change line 15 back and run again. 2 passed.


MENTAL MODEL

- Setup order: folder, git init, .gitignore, venv, install, test, commit, push.
- page: a fresh browser page for every test, given by a fixture.
- expect: retries until true or timeout.
- get_by_role: find elements the way a user sees them.
- Headless by default, --headed to watch.
- requirements.txt pins versions, .gitignore keeps junk and secrets out.


FOR YOUR OWN APP LATER

- Your team will likely keep a shared requirements.txt. Install from it instead of installing packages yourself, so everyone runs the same Playwright version.
- If browser downloads fail at work, ask the team how they solved it. They probably already have a certificate bundle or a mirror.
- Keep tests for a real app in a private repo, and never point practice tests at an internal system.


QUIZ (answers below - try before peeking)

1. A test is saved as checks.py with the function def verify_title(page):, and pytest reports "collected 0 items". Name both problems.

2. After you create a helper file called playwright.py, "from playwright.sync_api import ..." fails. Why?

3. A teammate adds time.sleep(3) before every assertion "for stability". What is wrong with that?

4. Test A logs in. Test B expects to already be logged in. Does it work?

5. In a new terminal, pytest gives "command not found". What did you forget?

6. .venv/ was committed before .gitignore existed. Adding it to .gitignore now does not remove it from the repo. How do you fix it?

7. The GitHub repo was created with a README, and git push is rejected. Why, and what are the options?

8. Your browser opens cdn.playwright.dev fine, but playwright install fails with SELF_SIGNED_CERT_IN_CHAIN. Why the difference?

9. On a public repo, what personal information can leak through Git even if no file contains it?

10. DevOps stretch question: the tests pass on your Mac, but on a GitHub Actions Linux runner Chromium will not start because of missing shared libraries. Name two fixes. (Covered in Module 09. Just guess.)


ANSWERS

1. The file name does not match test_*.py or *_test.py, so rename it to test_checks.py. The function does not start with test_, so rename it to def test_title(page):. Fixing only one of them still collects zero tests.

2. Name shadowing. Python finds your local playwright.py first and imports it instead of the installed package. Rename the file and delete __pycache__/.

3. It is both flaky (sometimes 3 seconds is not enough) and slow (usually far too much, multiplied by hundreds of tests). Playwright actions already wait automatically, and expect retries.

4. No. Each test gets a fresh, isolated browser context, and the order is not guaranteed. Each test must set up its own state, or reuse a saved login state (Module 08).

5. The venv is not active. Run source .venv/bin/activate.

6. Stop tracking it without deleting it from disk:
   git rm -r --cached .venv
   git commit -m "Stop tracking .venv"
   --cached removes it from the repo but keeps the local files. It still exists in old history. That is harmless for a venv, but a secret would also need to be changed (rotated).

7. The remote has a commit you do not have, so the histories are unrelated. Options: git pull origin main --allow-unrelated-histories, then push; or delete the GitHub repo and create it again empty; or git push --force, but only on a brand-new personal repo, never on a shared branch.

8. The browser uses the macOS keychain, which contains the corporate root certificate. The installer runs on Node.js, which has its own certificate list. Fix: NODE_EXTRA_CA_CERTS pointing to a .pem file with the trusted certificates.

9. The author name and email stored in every commit (git log shows them). Use GitHub's no-reply address before the first commit.

10. Install the browser with its system libraries: playwright install --with-deps chromium. Or run the tests inside Microsoft's official Playwright Docker image (mcr.microsoft.com/playwright/python), with a tag that matches your Playwright version. Bonus: CI has no screen, so the tests run headless, which is already the default.


End of Module 01. Next up: Module 02, locators (finding elements the way users see them).