PLAYWRIGHT WITH PYTHON - MODULE 12: CI/CD AND REPORTING


GOAL

Run the tests automatically, on someone else's computer, every time the code changes, and produce results a team can read without asking you what happened.

Tests that only run when a person remembers to run them are worth far less than tests that run on every change. And a test run that only produces coloured text in a terminal is no use to anyone who was not watching.

By the end of this module you can:

- write a GitHub Actions workflow that installs Python, the packages and the browsers, and runs the tests
- choose sensible triggers: every push, every night, or a button
- keep credentials in CI secrets instead of in the repository
- run a quick smoke job on every push and the full suite overnight
- produce a JUnit XML file and an HTML report, and upload them as artifacts
- get a trace off a CI machine before it is deleted
- understand what changes when a repository is public

Practice: this repository's own workflow, and a set of tests that check it.


WHAT CI IS

Continuous integration means the project is built and tested automatically whenever someone changes it. For a test suite, that is the whole job: every push starts a run, and the result appears next to the commit as a green tick or a red cross.

GitHub Actions does this by starting a fresh virtual machine, called a runner, for each job. It copies the repository onto it, runs the steps you listed, reports the result, and deletes the machine.

That the machine is deleted is the single most important thing to understand about CI:

- Every run starts clean. Nothing is left over from last time, so a test cannot pass because of something an earlier run left behind.
- Nothing is installed. No Python packages, no browsers, no system libraries. The workflow installs everything, every time.
- Nothing survives. Every file the run produced disappears with the machine, unless it is deliberately saved as an artifact.


A WORKFLOW FILE

A workflow is a YAML file in .github/workflows/. GitHub reads every file in that folder. The name of the file does not matter; the folder does.

YAML in brief: indentation shows structure, and it must be spaces, never tabs. A line starting with - is an item in a list. Everything else is name: value.

The outline:

```yaml
name: Playwright tests

on:                     # when to run
  push:
    branches: [main]

jobs:                   # what to run
  smoke:                # a job name you choose
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest
```

- name is what appears in the Actions tab.
- on lists the triggers.
- jobs contains one or more jobs. Jobs run in parallel unless one needs another.
- Each job picks a runner with runs-on, and lists steps.
- A step either uses a ready-made action from the marketplace, or runs a shell command with run.


TRIGGERS

```yaml
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:
```

- push with branches: [main] runs when something lands on the main branch.
- pull_request runs on every pull request, so a change is tested before it is merged. This is where CI earns its keep: a broken change is caught before it reaches main.
- schedule runs at fixed times. The cron expression has five fields: minute, hour, day of month, month, day of week. "0 2 * * *" means minute 0 of hour 2, every day: 02:00 UTC. Scheduled runs are in UTC, and GitHub may start them late when it is busy.
- workflow_dispatch adds a "Run workflow" button in the Actions tab, so you can start a run by hand.


THE STEPS, ONE BY ONE

```yaml
      - uses: actions/checkout@v4
```

Copies the repository onto the runner. Without it the machine is empty. @v4 pins the action's major version.

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
```

Installs Python. Pin the version, so a change in the runner image does not quietly change your Python. cache: pip keeps downloaded packages between runs, which saves a little time.

Note that the pinned version here is not necessarily the one on your own machine. CI should run a version you have deliberately chosen, and ideally one close to what the application runs on.

```yaml
      - name: Install dependencies
        run: pip install -r requirements.txt
```

Installs the pinned packages, and this repository's own package, because requirements.txt ends with -e . (Module 01). No virtual environment is needed: the whole machine is thrown away afterwards.

```yaml
      - name: Install browsers
        run: playwright install --with-deps chromium
```

The important part is --with-deps. A Linux runner is a bare system: the browser downloads, but the libraries it needs to run do not exist, so it cannot start. --with-deps installs those system packages too. On a Mac they come with the operating system, which is why you never need it locally (Module 01).

```yaml
      - name: Run smoke tests
        run: pytest -m smoke -n 2 --tracing retain-on-failure --junit-xml=results.xml --html=report.html --self-contained-html
        env:
          SHOP_USER: ${{ secrets.SHOP_USER }}
          SHOP_PASSWORD: ${{ secrets.SHOP_PASSWORD }}
```

- -m smoke selects the marked tests (Module 08).
- -n 2 runs them in parallel. GitHub's standard runners have 2 cores, so more workers would not help (Module 09).
- --tracing retain-on-failure records every test and keeps the trace only for failures (Module 04).
- --junit-xml and --html produce the reports, covered below.
- env sets environment variables for this step, from secrets.
- There is no --headed, because a runner has no screen. Headless is the default.


SECRETS

Never put a password in a workflow file. The file is in the repository, so on a public repository it is visible to the world, and on a private one to everyone with access, as well as being in the Git history for good.

Instead, store it in the repository's secrets: Settings, then Secrets and variables, then Actions, then New repository secret. The workflow refers to it:

```yaml
        env:
          SHOP_PASSWORD: ${{ secrets.SHOP_PASSWORD }}
```

GitHub stores secrets encrypted, puts the value into the job's environment, and masks it in the logs: anything printing it shows ***. That masking is a safety net, not a licence to print passwords.

The test code needs no changes at all. settings.shop_password() reads an environment variable (Module 11), and it does not care whether that came from your terminal, a .env file, or a CI secret.

One limitation worth knowing: secrets are not available to workflows triggered by a pull request from a fork, because otherwise anyone could open a pull request that prints them. Tests needing credentials have to handle that, usually by skipping.


TWO JOBS: FAST FEEDBACK AND FULL COVERAGE

The workflow has two jobs, and the reason is a trade-off every team meets.

A full suite across several browsers may take half an hour. Waiting that long after every push is unworkable, so people stop paying attention to the result. But a quick subset does not cover enough to trust a release.

So: run a small, fast set on every push, and everything overnight.

```yaml
  smoke:
    name: Smoke tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

The smoke job runs on every push and pull request, uses -m smoke, and finishes in a few minutes.

```yaml
  full:
    needs: smoke
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox]
```

- needs: smoke means this job only starts if the smoke job passed. No point running thirty minutes of tests when the basics are broken.
- if: ... limits it to the nightly schedule and the manual button, so a push does not trigger it.
- matrix runs the job once per value. Here that is two jobs, one per browser, at the same time. ${{ matrix.browser }} is the current value, used in the job's name and in the pytest command.
- fail-fast: false stops one browser's failure from cancelling the other. By default a matrix cancels its siblings on the first failure, which is rarely what you want for tests: you lose the information about the other browser.

A matrix can also vary the Python version, the operating system, or a device (Module 07), and it multiplies: three browsers and two operating systems is six jobs.

```yaml
    timeout-minutes: 45
```

Every job should have a timeout. Without one, a hung test can keep a runner busy for up to six hours, which costs money on a paid plan and holds up other work.


REPORTING: WHO READS WHAT

A terminal full of dots is fine while you are working. It is useless to anyone else, and useless tomorrow. Three outputs cover three audiences.

The terminal, for you, while you work. Nothing to set up.

JUnit XML, for machines:

```
pytest --junit-xml=results.xml
```

An old format that nearly every tool understands: CI systems, dashboards, test management tools. It lists each test with its result and how long it took, and the failure message for the ones that failed. Nobody reads the file; tools do. It is how a test report gets into Jenkins, Azure DevOps, Jira integrations and so on.

HTML, for people:

```
pip install pytest-html
pytest --html=report.html --self-contained-html
```

A single page listing every test, with results you can filter and sort, the duration of each, and the full error for failures. --self-contained-html puts the styling inside the file, so it is one file that can be attached to anything and opened anywhere.

Playwright's traces, for whoever has to debug a failure, are the richest of the three (Module 04). The HTML report says which test failed and why; the trace shows what the browser was doing.


ADDING CONTEXT TO A REPORT

A pytest hook can attach extra information to failures, in conftest.py:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
    if page is None:
        return
    try:
        report.sections.append(("Browser state", f"url: {page.url}\ntitle: {page.title()}"))
    except Exception:
        pass
```

A hook is a function pytest calls at a particular moment, recognised by its name. This one runs as each test's report is made.

- hookwrapper=True means it runs around the normal behaviour: yield lets pytest build the report, and the code after it adds to the result.
- report.when != "call" skips the setup and teardown phases, so only the test body is considered.
- item.funcargs holds the fixtures the test used, so this finds whichever page fixture it asked for.
- The try block matters: the page may already be closed by the time the report is made, and a hook that raises an exception breaks reporting for everything.

The URL and the title then appear in the terminal output and the HTML report for every failed test, with no change to any test. It is a small thing that answers the first question anyone asks about a failure: where was the browser?


ARTIFACTS: GETTING FILES OFF THE RUNNER

The runner is deleted when the job ends, and every file with it. An artifact is a file the CI system keeps and attaches to the run.

```yaml
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: smoke-report
          path: |
            report.html
            results.xml
          retention-days: 7
```

- if: always() uploads whether the tests passed or failed. Without it, a step is skipped once something earlier has failed, which is exactly when you want the report.
- name is what the download is called on the run's page.
- path takes one path or several. The | starts a multi-line value.
- retention-days sets how long GitHub keeps it. Without it, the repository's default applies, often 90 days.

Traces get their own step, with a different condition:

```yaml
      - name: Upload traces
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: smoke-traces
          path: test-results/
```

if: failure() only runs when something failed, which is the only time test-results/ contains anything worth having. Traces are large, so there is no reason to upload them after a green run.

To use them: open the run in the Actions tab, scroll to Artifacts at the bottom, download the zip, unpack it, and open the trace with playwright show-trace or at trace.playwright.dev.


ARTIFACTS AND PRIVACY

An artifact can be downloaded by anyone who can see the repository. On a private repository that is the people with access. On a public one, that is anyone at all.

That matters because a Playwright trace records everything: the pages, their content, cookies, and network traffic including authentication headers. A trace of a logged-in session effectively contains a usable session. The same goes for a storage_state file (Module 11), screenshots, and videos.

For this repository, which is private now and may be public later, the rules are the same either way:

- Never upload auth/ or any storage_state file.
- Keep traces to a short retention, and remember they become public if the repository does.
- Use a dedicated test account, never a real one.

For a real application, keep any repository whose CI logs into a real system private, and review what the artifacts contain before changing that.


READING A FAILED RUN

1. Open the Actions tab and click the run. A red cross marks the failed job.
2. Click the job, then the failed step. The log shows the pytest output, exactly as it appears in a terminal.
3. Scroll to the summary line: which tests failed, and the assertion errors.
4. Download the traces artifact and open the trace for the failed test.
5. If it fails on CI but not locally, look for the usual causes: a timing assumption that a slower machine exposes (Module 03), a test depending on another (Module 09), a missing environment variable, or data left over from an earlier run.


WHEN TO FAIL THE BUILD

A red build should mean something is wrong with the application. Everything else teaches people to ignore it:

- Flaky tests: fix them, or mark them, rather than letting them fail the build at random (Module 09).
- Third-party outages: mock them (Module 10), or move those tests to a separate job whose failure is reported differently.
- Known bugs: mark them xfail with the ticket number, so they do not fail the build but do tell you when they are fixed (Module 08).

The --reruns 1 in the full job is a compromise: a single retry absorbs the occasional network hiccup on a shared runner. It is not a licence to leave flaky tests alone, and every rerun in the report deserves a look.


BEYOND GITHUB ACTIONS

The same ideas apply to Jenkins, GitLab CI, Azure Pipelines, CircleCI and the rest. The syntax differs; the shape does not:

- a trigger
- a clean machine
- install dependencies and browsers
- run the tests
- publish reports and keep artifacts
- secrets from the CI system, never from the repository

JUnit XML is what makes that portable: every one of those tools reads it.

If the application is only reachable inside a company network, GitHub's hosted runners cannot see it. The options are a self-hosted runner on a machine inside the network, or the company's own CI system. That is a decision for whoever runs the infrastructure.


THE FILES

- .github/workflows/playwright.yml - the workflow, with a smoke job and a full matrix job
- tests/conftest.py - the pytest_runtest_makereport hook
- tests/test_12_ci_reporting.py - 9 tests that check the workflow itself
- .gitignore - now also ignores report*.html and results*.xml
- requirements.txt - now includes pytest-html

The tests in this module are unusual: they test the repository's own configuration rather than an application. That is worth doing, because a workflow file is code that nobody runs locally, and a mistake in it is only discovered when CI behaves oddly.

- test_workflow_file_exists - the file is where GitHub looks for it
- test_workflow_is_valid_yaml - it parses, and has the two expected jobs. Needs PyYAML; skipped if it is not installed
- test_browsers_are_installed_with_dependencies - --with-deps is present, without which the browser cannot start on Linux
- test_traces_are_kept_on_failure - failures will be debuggable
- test_reports_are_produced - both report formats are generated
- test_credentials_come_from_secrets - the workflow reads from secrets
- test_no_password_is_hard_coded - no line sets a password, token or secret to a literal value. Lines containing ${{ are skipped, because those are references
- test_jobs_have_a_timeout - both jobs can be stopped if they hang
- test_reports_are_not_committed - test-results/, auth/, reports and XML files are all in .gitignore


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Forgetting --with-deps.
The browser installs and then fails to start, with an error about missing shared libraries. A Mac never shows this, because macOS already has them.

Trap 2 - Assuming files survive the job.
The runner is deleted. Anything not uploaded as an artifact is gone, including every trace and report.

Trap 3 - Uploading artifacts only on success.
A step after a failure is skipped unless it says if: always() or if: failure(). Without that, the report you need is the one you do not get.

Trap 4 - A password in the workflow file.
It is in the repository and in the history. Use secrets, and remember that a private repository can become public later.

Trap 5 - No timeout on a job.
A hung test can hold a runner for hours. Set timeout-minutes on every job.

Trap 6 - Too many parallel workers.
GitHub's standard runners have 2 cores. -n 8 there makes the run slower, not faster (Module 09).

Trap 7 - fail-fast left at its default.
One browser failing cancels the others, so you never learn whether the problem affects them all.

Trap 8 - Running everything on every push.
A thirty-minute wait after each push means people stop reading the results. Split it: smoke now, everything overnight.

Trap 9 - Tabs in YAML.
YAML does not allow tab characters for indentation. The error GitHub shows is not always clear about it.

Trap 10 - An unpinned Python version or action.
python-version: "3.x" or an action without @v4 can change under you, and a run that passed last week fails for no visible reason.

Trap 11 - Uploading a trace of a logged-in session from a public repository.
Anyone can download it, and it contains cookies and authentication headers.

Trap 12 - Treating a rerun as a pass.
--reruns hides a failure. It is there for genuine infrastructure noise, not for tests that need fixing (Module 09).


HANDS-ON PRACTICE

1. Install the reporting plugin, if you have not:

```
pip install pytest-html
```

2. Run the Module 12 tests:

```
pytest tests/test_12_ci_reporting.py -v
```

   Expect 9 passed, or 8 passed and 1 skipped if PyYAML is not installed. These need no browser and finish in under a second. A plain "pytest" now runs 135 tests: 133 passed, 1 xfailed and 1 rerun.

3. Produce both reports locally, exactly as CI does:

```
pytest -m smoke --junit-xml=results.xml --html=report.html --self-contained-html
open report.html
```

   The HTML report lists each test with its duration, and lets you filter by result. Look at results.xml too: it is the same information in a form built for tools.

4. See the reporting hook at work. Break a smoke test on purpose, for example change an expected text in tests/test_08_data_driven.py, then run:

```
pytest -m smoke --html=report.html --self-contained-html
open report.html
```

   Open the failed test in the report: the Browser state section shows the URL and page title at the moment of failure. Change the test back afterwards.

5. Push the workflow and watch it run:

```
git add -A
git commit -m "Module 12: CI/CD and reporting"
git push
```

   Open the repository on GitHub, click the Actions tab, and open the run. Click through to the Smoke tests job and watch the steps. The first run takes a few minutes, mostly installing the browser.

6. Download the report artifact: at the bottom of the run's page, under Artifacts, click smoke-report. Unzip it and open report.html.

7. Optional: add the secrets. In Settings, Secrets and variables, Actions, add SHOP_USER as standard_user and SHOP_PASSWORD as secret_sauce. The tests already pass without them, because settings.py falls back to the published demo credentials, but adding them is how a real project works. Run the workflow again from the Actions tab with the Run workflow button.

If the workflow fails on its first run:

- An error before any step means the YAML is invalid. GitHub names the line. Check for tabs.
- A failure in Install browsers usually means --with-deps is missing.
- A test failing on CI but not locally is the interesting case: download the traces artifact and read it as in READING A FAILED RUN.
- The nightly job will not appear until the schedule fires, or until you press Run workflow.

Break it on purpose (this step is MEANT to fail):

1. In .github/workflows/playwright.yml, remove --with-deps from the smoke job's browser step, so it reads:
   run: playwright install chromium
2. Commit and push, then watch the Actions tab.
3. The install step passes, and the test step fails: the browser is there but cannot start, because the Linux libraries it needs are missing. The error mentions missing shared libraries. This is Module 01's section 13 happening for real.
4. Put --with-deps back, commit and push, and the run is green again.


MENTAL MODEL

- A runner is a clean machine that is deleted afterwards: install everything, save anything you want to keep.
- Smoke on every push, everything overnight.
- Secrets come from the CI system; the test code reads environment variables and does not know the difference.
- Three outputs: the terminal for you, JUnit XML for tools, HTML for people. Traces for whoever debugs.
- Artifacts are the only way files leave the runner, and anyone who can see the repository can download them.
- A red build must mean the application is broken, or people stop reading it.


FOR YOUR OWN APP LATER

- Start with one job that runs a handful of smoke tests on pull requests. It is more valuable than a perfect suite that runs nowhere.
- Make the check required on the main branch, so a pull request cannot be merged while it is red. That is where CI changes behaviour rather than just producing information.
- Agree what the team does about a red nightly run, and who looks at it. An unwatched nightly job is wasted effort.
- Keep the smoke job under five minutes. Past that, people start pushing without waiting.
- Attach the HTML report to the release notes or the test plan. It is the evidence that the tests ran.
- If the application is only reachable on the company network, raise the self-hosted runner question early: it needs someone with infrastructure access and takes time to arrange.
- Watch the cost. Minutes are free on public repositories and limited on private ones, and a matrix multiplies them quickly.


QUIZ (answers below - try before peeking)

1. Why does the workflow install Python, the packages and the browsers on every run, when your own machine has them already?

2. What does --with-deps do, and why is it needed on CI but never on a Mac?

3. A test fails on CI and you want the trace. What two things must the workflow do for you to get it?

4. Why does the upload step say if: always() instead of leaving the condition out?

5. Where should a password for CI be kept, and what does the test code have to change to read it from there?

6. Why run a smoke job on every push and the full suite only at night?

7. What does needs: smoke do in the full job, and what does fail-fast: false do in its matrix?

8. GitHub's standard runners have 2 cores. What does that imply for -n?

9. Your repository is private today and public next month. What becomes riskier about the artifacts the workflow uploads?

10. DevOps stretch question: the nightly suite takes 40 minutes even with -n 2. How would you make it finish in about 10? (Just guess.)


ANSWERS


1. Because the runner is a brand-new machine with nothing on it, created for this job and deleted when it ends. It has never seen your repository or your packages.

Why that is a feature rather than a nuisance: a clean machine proves the project can be set up from scratch, using only what is committed. If requirements.txt is missing something, CI finds out immediately, while your own machine would carry on working because the package was installed months ago. The same applies to the browsers: nothing is cached between runs unless you arrange it.

It is also why pinned versions matter (Module 01). The runner installs exactly what requirements.txt says, so the run is reproducible rather than dependent on whatever happened to be installed.

Common mistakes:
- Assuming the runner keeps anything between runs. Only the pip cache, and only because setup-python was asked for it.

See: WHAT CI IS, and THE STEPS, ONE BY ONE.


2. It installs the system libraries a browser needs in order to run, as well as the browser itself. A Mac never needs it because macOS already has equivalents; a bare Linux runner does not.

Why the failure is confusing without it: the install step succeeds, because downloading the browser works fine. The failure comes later, when a test tries to start it, and the error is about missing shared libraries rather than anything to do with Playwright or your test. People reasonably look at the test first.

```
playwright install --with-deps chromium
```

On a Linux runner this uses the system package manager, which is why it needs the elevated permissions GitHub's runners already have. The alternative is the official Playwright Docker image, which has everything already (Module 01, section 13).

Common mistakes:
- Copying a local command into the workflow unchanged. What works on your machine is not enough on Linux.

See: THE STEPS, ONE BY ONE, Trap 1, and Module 01.


3. The test run must record the trace (--tracing retain-on-failure), and a later step must upload test-results/ as an artifact, with a condition that runs after a failure.

Why both are needed: recording alone puts the file on the runner, which is then deleted. Uploading alone has nothing to upload. Together:

```yaml
      - name: Run tests
        run: pytest --tracing retain-on-failure

      - name: Upload traces
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          path: test-results/
```

retain-on-failure records every test and keeps only the failures, so a green run uploads nothing and costs nothing (Module 09 explains the recording happens in memory throughout).

Then download the zip from the run's page and open the trace locally.

Common mistakes:
- Reading the CI log instead. The log says what failed; the trace shows the page at every step.

See: ARTIFACTS: GETTING FILES OFF THE RUNNER, and Trap 2.


4. Because a step is skipped by default once an earlier step in the job has failed, and a failed test run is exactly when the report matters most.

Why: GitHub stops running a job's steps after a failure, on the assumption that the rest depended on what failed. if: always() overrides that for one step. The conditions worth knowing:

- if: always() runs whatever happened. Use it for reports.
- if: failure() runs only after a failure. Use it for traces, which are large and only useful then.
- if: success() is the default.

The report step uses always() because a passing run's report is still worth keeping: it is the evidence that the tests ran, and how long they took.

Common mistakes:
- Putting the report and the traces in one step. They want different conditions.

See: ARTIFACTS: GETTING FILES OFF THE RUNNER, and Trap 3.


5. In the repository's secrets, under Settings, Secrets and variables, Actions. The test code changes nothing at all.

Why nothing changes: settings.shop_password() reads an environment variable (Module 11). The workflow puts the secret into the environment for that step:

```yaml
        env:
          SHOP_PASSWORD: ${{ secrets.SHOP_PASSWORD }}
```

As far as Python is concerned, that is identical to exporting it in a terminal or putting it in .env. This is the payoff for reading credentials from the environment in the first place: the same code runs everywhere, and only the source of the value differs.

GitHub encrypts secrets and masks them in logs, showing *** if something prints one.

Common mistakes:
- Committing a .env file so CI can read it. That puts the password in the repository, which is the thing secrets exist to avoid.
- Assuming masking makes printing safe. It is a safety net, not a feature to rely on.

See: SECRETS, Trap 4, and Module 11.


6. Because fast feedback and thorough coverage pull in opposite directions, and splitting them gives both.

Why it matters in practice: if every push waits thirty minutes for a result, people stop waiting. They push and move on, and the result arrives when they are thinking about something else. A five-minute smoke job is short enough that the person who made the change is still looking.

But a smoke set does not cover enough to trust a release, so the full suite runs overnight across several browsers, when nobody is waiting and a longer run costs nothing in attention.

The mechanism is markers (Module 08): the same tests, selected differently. No duplicate test code.

Common mistakes:
- Keeping a separate copy of the smoke tests, which then drifts out of step with the real ones.
- Letting the smoke set grow until it is no longer fast.

See: TWO JOBS: FAST FEEDBACK AND FULL COVERAGE, and Trap 8.


7. needs: smoke makes the full job wait for the smoke job and run only if it passed. fail-fast: false stops one matrix job's failure from cancelling the others.

Why needs: there is no value in thirty minutes of tests across two browsers when the basics are already broken. It also saves runner minutes, which are limited on private repositories.

Why fail-fast: false: by default, a matrix cancels its remaining jobs as soon as one fails. For a build that is sensible, because the answer is already known. For tests it destroys information: if Chromium fails, you still want to know whether Firefox failed in the same way, because "both" and "only Chromium" point at completely different causes.

Common mistakes:
- Leaving fail-fast at its default and then wondering why the other browser's job says "cancelled".

See: TWO JOBS: FAST FEEDBACK AND FULL COVERAGE, and Trap 7.


8. Use -n 2. More workers than cores makes the run slower, because each worker runs a whole browser and they compete for the same CPU and memory.

Why: the speed-up from parallel runs comes from using time that would otherwise be spent waiting for pages. Once both cores are busy, extra workers add contention and memory pressure, and a runner that starts swapping is far slower than one running two workers cleanly. Browsers are heavy: four Chromium instances on a 2-core runner with limited memory is a reliable way to produce timeouts that look like test failures (Module 09).

If 2 workers are not enough, the answer is more machines, not more workers on one machine, which is the next question.

Common mistakes:
- Using -n auto and assuming it is optimal. It matches the core count, which is the right ceiling, but on a small runner even that can be too much once memory is counted.

See: Trap 6, and Module 09.


9. Anyone at all can download them, including the traces. A trace records the pages, their content, cookies and network traffic, so a trace of a logged-in session effectively hands over a working session.

Why this is easy to miss: artifacts feel like an internal detail of the build, and on a private repository they are. Making a repository public changes the audience for everything in it at once, including artifacts, logs and the whole Git history.

What to do before making this repository public:

- Check that no artifact path includes auth/ or any storage_state file.
- Keep retention short, so old traces expire.
- Remember the Git history: anything ever committed is still there, even if deleted later.
- Review the repository for personal data, as this repository's end-of-course review will do.

For a real application, the simplest rule is that any repository whose CI logs into a real system stays private.

Common mistakes:
- Thinking a deleted file is gone. In Git it is not.

See: ARTIFACTS AND PRIVACY, and Trap 11.


10. Split the tests across several machines, running at the same time. That is sharding, and a matrix is the mechanism.

Why: one runner can only do so much, and 2 cores is the ceiling for -n. Four runners each taking a quarter of the tests turn 40 minutes into roughly 10, plus a couple of minutes of setup per machine. Each runner still uses -n 2 internally, so the two techniques multiply.

```yaml
    strategy:
      matrix:
        group: [1, 2, 3, 4]
    steps:
      - run: pytest --splits 4 --group ${{ matrix.group }} -n 2
```

A plugin such as pytest-split divides the tests into balanced groups by how long each one took previously, which matters: dividing by file gives one machine all the slow tests.

This only works because the tests are independent (Module 09). Tests that rely on each other, or on shared data, fail unpredictably once they are spread across machines.

Other things worth doing first, which are often cheaper: find the slowest tests with --durations=10 and speed them up, move setup from the user interface to the API (Module 10), and remove tests that duplicate each other.

Common mistakes:
- Sharding a suite that is not independent, and spending the saved time debugging it instead.

See: TWO JOBS: FAST FEEDBACK AND FULL COVERAGE, and Module 09.