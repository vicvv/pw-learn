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

This whole block is a terminal command that creates the file. If you create the file in VS Code instead, paste only the lines between the cat line and the EOF line. The cat and EOF lines are never part of the file.

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


4. CERTIFICATE ERRORS - ONLY ON SOME NETWORKS

Symptom: playwright install fails with SELF_SIGNED_CERT_IN_CHAIN (or a similar certificate error).

Why: many company networks inspect HTTPS traffic and re-sign it with the company's own root certificate. A program only accepts that if it trusts the company certificate.

- Your browser uses the Mac's keychain (the Mac's list of trusted certificates). If the company certificate is in the keychain, the browser works.
- Playwright's installer runs on Node.js, which has its own built-in certificate list and ignores the keychain. The company certificate is not on that list, so Node refuses the connection.

Do you need a fix?

- Home network, no VPN: no. Public sites present normal certificates that Node already trusts. Run playwright install chromium and skip the rest of this section.
- Company network (office or company Wi-Fi): often yes.
- Company VPN on any Mac: maybe. Many VPNs only send company traffic through the VPN (split tunneling), and public sites go straight over your home internet. Others send everything through the company network, where it may be inspected.

How to check: try playwright install chromium first. You only need a fix if it fails with a certificate error. You can also see who signed the certificate you are getting:

```
openssl s_client -connect cdn.playwright.dev:443 </dev/null 2>/dev/null | grep "issuer="
```

- A public certificate authority (for example Google Trust Services, Let's Encrypt, DigiCert): no fix needed.
- A company name or a security product: that network re-signs traffic, so a fix is needed.


4A. WORK MAC ON THE COMPANY NETWORK (CERTIFICATE ALREADY INSTALLED)

On a company-managed Mac, IT has usually already put the company certificate in the keychain. Export the certificates the Mac trusts and point Node at them:

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

On a personal Mac, the company certificate is not installed, so there is nothing to export. Get it from the company:

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
playwright install chromium
```

If IT gave you a .cer file, convert it first, because Node needs PEM text. If the file is already PEM, openssl just rewrites it:

```
openssl x509 -in ~/Downloads/company-root.cer -out "$HOME/.certs/company-root.pem"
```

- If IT also tells you to add the certificate to the keychain (double-click the file, then set it to "Always Trust"), that covers browsers and most other apps. Node still needs NODE_EXTRA_CA_CERTS, because it ignores the keychain.
- When you stop using that VPN, remove the NODE_EXTRA_CA_CERTS line from ~/.zshrc and the certificate from the keychain.


4C. PERSONAL MAC AT HOME (NO VPN)

No certificate is needed. Run:

```
playwright install chromium
```

If you copied ~/.zshrc from a work Mac, it may contain a NODE_EXTRA_CA_CERTS line pointing to a .pem file that does not exist on this Mac. Node warns that it is ignoring the extra certificates and carries on, so it is harmless. To keep things tidy, remove that line.


4D. RULES FOR EVERY CASE

- Never use NODE_TLS_REJECT_UNAUTHORIZED=0. It switches off certificate checking completely.
- Other tools with their own certificate list (for example Python's requests library or Docker) can fail the same way on the same network. Each has its own setting for pointing at a certificate file.


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
filterwarnings =
    ignore:Session-scoped fixtures defined as instance methods
EOF
```

If you create the file in VS Code instead, paste only the lines between the cat line and the EOF line.

- testpaths = FILES: a plain "pytest" only looks in FILES/.
- pythonpath = FILES: later modules can import helpers from FILES/pages/.
- filterwarnings: hides one harmless deprecation warning that comes from the pytest-playwright plugin, not from your code. Other warnings still show.
- pytest.ini must keep this exact name, with no module prefix.
- When pytest reads the file, its output shows a "configfile: pytest.ini" line. If that line is missing, the file is missing or misnamed (check with ls pytest.ini).


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

If you create the file in VS Code instead, paste only the lines between the cat line and the EOF line. A cat line inside a .py file makes pytest fail with "NameError: name 'cat' is not defined".

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

1. Run the tests:

```
pytest -v
```

   Expect 2 passed. Near the top of the output there should be a "configfile: pytest.ini" line. If it is missing, pytest.ini is missing or misnamed (check with ls pytest.ini).

2. Watch them run:

```
pytest --headed --slowmo 500
```

   Chrome opens playwright.dev, clicks "Get started" and lands on the Installation page.

If a test fails because the site changed:

The tests rely on playwright.dev's current page title, link text and heading. The site can change after these notes were written. If a test times out on a locator:

- Open the site with playwright codegen https://playwright.dev/ and hover over the link or heading. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

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

8. The browser uses the macOS keychain, which contains the corporate root certificate. The installer runs on Node.js, which has its own certificate list. Fix: NODE_EXTRA_CA_CERTS pointing to a .pem file with the trusted certificates. On a home network without a VPN, traffic is not re-signed, so no fix is needed.

9. The author name and email stored in every commit (git log shows them). Use GitHub's no-reply address before the first commit.

10. Install the browser with its system libraries: playwright install --with-deps chromium. Or run the tests inside Microsoft's official Playwright Docker image (mcr.microsoft.com/playwright/python), with a tag that matches your Playwright version. Bonus: CI has no screen, so the tests run headless, which is already the default.

On a Mac, playwright install chromium is all you need. It downloads only the browser, into Playwright's own folder. The system libraries Chromium needs to run (for drawing, fonts, sound and so on) already come with macOS.

A Linux machine, such as a GitHub Actions runner or a server, is different. It is often a bare system, and many of those libraries are missing. The browser downloads fine, but it cannot start. The error usually mentions missing shared libraries (files ending in .so) or says the browser failed to launch.

There are two fixes.


Fix 1 - install the browser together with its Linux libraries

```
playwright install --with-deps chromium
```

- --with-deps means "also install the system packages this browser needs".
- It is meant for Linux. It uses the system package manager, so it may need sudo, which GitHub's runners already have. You never need it on your Mac.
- The libraries are installed on that machine only. On a runner, which is thrown away after each job, this runs on every job.


Fix 2 - run the tests inside the official Playwright Docker image

Microsoft publishes a Docker image that already has Python, the browsers and all their Linux libraries:

```
mcr.microsoft.com/playwright/python
```

The tests run inside a container started from that image, so nothing has to be installed on the machine itself.

Choose an image tag that matches your Playwright version. Browser builds are tied to the library version, so a mismatch can fail in strange ways (for example, "Executable doesn't exist"). Check your version:

```
pip show playwright
```

The Version line, for example 1.49.0, gives the tag, for example v1.49.0-noble. The tag list is on Playwright's Docker page: https://playwright.dev/python/docs/docker

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


Which fix to use

- Fix 1 is the simplest on GitHub Actions, and Module 09 uses it.
- Fix 2 gives the same environment on every machine (your Mac, a teammate's laptop, any CI system), because everyone uses the same image.
- Either way, a CI machine has no screen, so tests run headless. That is already the default, so do not add --headed in CI.


Traps

- Do not use your Mac's .venv inside the container. It was built for macOS and does not work on Linux. Install from requirements.txt inside the container instead, as above.
- If you use the official image, the playwright version in requirements.txt must match the image tag. When you upgrade Playwright, change both.
- On a company network, pip install inside a container can fail with a certificate error, because the container does not see your Mac's keychain or NODE_EXTRA_CA_CERTS. The proper fix is to add the company certificate to the image, not to switch off certificate checks.
- Docker Desktop is free for personal use, but larger companies need a paid license. On a work Mac, check what your company provides before installing it.


End of Module 01. Next up: Module 02, locators (finding elements the way users see them).