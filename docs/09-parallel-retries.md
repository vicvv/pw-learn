PLAYWRIGHT WITH PYTHON - MODULE 09: PARALLEL RUNS, RETRIES AND FLAKY TESTS


GOAL

Make the suite fast without making it unreliable. Browser tests are slow, and a suite of a few hundred can take many minutes. Running tests in parallel fixes the speed, but only if every test is independent. And when a test fails only sometimes, retrying it can hide a real problem. This module covers both, and how to find and fix a flaky test instead of hiding it.

By the end of this module you can:

- run tests in parallel with pytest-xdist, and choose how many workers
- explain why parallel runs need independent tests, and spot tests that are not
- know what is shared between workers and what is not, including session fixtures
- give each test its own data when tests share a backend
- retry failing tests with pytest-rerunfailures, and know when that is a mistake
- recognise, reproduce and fix a flaky test

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/).


WHY TESTS GET SLOW

Each browser test opens a page, waits for it, clicks, waits again. A few seconds each, and nearly all of that time is waiting, not computing. Run 300 such tests one after another and the computer spends most of the time idle.

Parallel runs use that idle time: while one test waits for a page, another is clicking in a different browser.


INSTALL THE PLUGINS

```
pip install pytest-xdist pytest-rerunfailures
```

- pytest-xdist runs tests in parallel.
- pytest-rerunfailures retries failed tests.

Pin them in requirements.txt along with the other packages:

```
pip freeze | grep -i -E "^(playwright|pytest|pytest-playwright|pytest-xdist|pytest-rerunfailures)==" > requirements.txt
echo "-e ." >> requirements.txt
```

requirements.txt then has six lines: five pinned packages, and -e . for this repo's own package.


PARALLEL RUNS WITH PYTEST-XDIST

```
pytest -n auto          # one worker per CPU core
pytest -n 4             # exactly four workers
pytest -n 0             # no parallelism (the same as leaving -n out)
```

What happens:

1. pytest starts several worker processes, named gw0, gw1, gw2 and so on.
2. Each worker is a separate Python process with its own browser.
3. pytest collects all the tests and hands them out to the workers.
4. Each worker runs its share and reports back.
5. The results are combined into one report at the end.

With -v, each line shows which worker ran the test:

```
[gw2] PASSED tests/test_09_parallel_retries.py::test_independent_tests[chromium-3]
[gw0] PASSED tests/test_09_parallel_retries.py::test_worker_id
```

The lines come out in whatever order the tests finish, not in file order. That is normal.

Some things behave differently with -n:

- print() output from tests does not appear, even with -s, because it happens in the workers.
- -x (stop at first failure) stops as soon as practical, but tests already running in other workers finish first.
- --headed opens one browser window per worker, all at once.


HOW TESTS ARE SHARED OUT

--dist decides how tests are given to workers:

```
pytest -n 4 --dist load        # the default: any test to any free worker
pytest -n 4 --dist loadfile    # all tests from one file go to the same worker
pytest -n 4 --dist loadscope   # tests in the same module or class go to the same worker
pytest -n 4 --dist loadgroup   # tests with the same xdist_group name go to the same worker
```

load spreads tests most evenly, so it is fastest. The others keep groups of tests together, which is only needed when tests in a group share something expensive.

loadgroup uses a marker:

```python
@pytest.mark.xdist_group(name="reports")
def test_export(): ...
```

Keeping tests together is a workaround, not a fix. If tests need each other to run in a particular place or order, they are not independent.


THE ONE RULE: EVERY TEST MUST BE INDEPENDENT

A test is independent if it passes when run on its own, in any order, alongside any other test. Parallel runs only work when every test is.

Example of tests that are not independent:

```python
created = []

def test_first_creates_user():
    created.append("alice")
    assert created == ["alice"]

def test_second_uses_user():
    assert "alice" in created
```

Run one after another, in file order, both pass. The second test only passes because the first ran before it, in the same process. Now:

- Run test_second_uses_user alone: it fails, because nothing created alice.
- Run with -n 2: the two tests usually go to different workers. Each worker is a separate process with its own empty created list, so the second test fails.
- Change the order, or let xdist hand tests out differently: it fails sometimes and passes sometimes.

That last part is what makes these failures so confusing. The test looks correct, it passed yesterday, and the failure seems random. It is not random: it depends on which worker ran which test, in what order.

The same happens with real data. Test 1 creates a user on the test server, Test 2 logs in as that user. In parallel, Test 2 may start before Test 1 has finished, or run on a worker where Test 1 never ran.

The fix is always the same: every test sets up what it needs. A login test creates its own user (or uses one that exists before the run starts), and does not rely on another test having created it. Fixtures (Module 07) are the tool for this: the setup is written once, and each test gets its own.

How to check a test is independent:

- Run it alone: pytest -k name_of_test
- Run the whole suite in parallel: pytest -n auto
- Run the suite twice, and see if the same tests fail.


WHAT IS SHARED AND WHAT IS NOT

Not shared between workers (each worker has its own):

- the Python process, so module-level variables and lists
- the browser, and every context and page in it
- session-scoped fixtures: each worker runs its own copy

Shared between workers:

- files on disk, such as the same output file written by two tests
- the app's server and its database, if the tests use a real backend
- anything outside your computer: accounts, email inboxes, third-party services

Inside one worker, the usual pytest rules still apply: each test gets its own page and context (Module 01), so tests in the same worker do not see each other's pages either.


SESSION FIXTURES RUN ONCE PER WORKER

A session-scoped fixture runs once per session, and with -n 4 there are four sessions, one per worker. So a session fixture runs four times, once in each worker.

That is fine for most things, such as browser_context_args. It matters for anything with a side effect outside the worker:

- logging in once and saving the login state to a file: four workers may each log in and write the same file at the same moment
- creating test data on a server: four copies get created
- deleting all test data at the start: one worker can delete what another just created

Module 11 shows how to save login state safely, with one file per worker or a lock.


SHARED BACKEND DATA: GIVE EACH TEST ITS OWN

The TodoMVC demo keeps everything in the browser, so each test's items are private. A real app usually stores data on a server, which every worker shares. Then two tests that create an item called "report" and check there is exactly one will collide: each sees the other's item.

The fix is unique data per test:

```python
from uuid import uuid4

text = f"item-{uuid4().hex[:8]}"
```

uuid4() makes a random identifier, and .hex[:8] takes its first 8 characters, for example item-3f9a1c2e. The chance of two tests picking the same one is tiny. Search for and assert on that exact value, never on "everything there is". test_unique_data_per_test shows the pattern.

Also clean up afterwards: delete what the test created, in a fixture's teardown (Module 07), so the server does not fill up with test data.


WORKER_ID

pytest-xdist provides a worker_id fixture:

- "master" when you run without -n
- "gw0", "gw1" and so on inside parallel workers

Useful for giving each worker its own resource, such as its own test account or its own output file:

```python
@pytest.fixture(scope="session")
def account(worker_id):
    return f"tester-{worker_id}@example.com"
```

The environment variable PYTEST_XDIST_WORKER holds the same name, for code that is not a fixture.


HOW MANY WORKERS

-n auto uses one worker per CPU core. More is not always faster:

- Every worker runs a whole browser, which uses a lot of memory. Too many and the computer starts swapping memory to disk, and everything slows down.
- The app under test has to cope with all the workers at once. A small test server can become the bottleneck.
- CI machines often have only 2 to 4 cores.
- Starting each worker costs a few seconds, so a small suite may not get faster at all.

Try a few values and time them:

```
time pytest -q
time pytest -q -n 4
time pytest -q -n auto
```

time prints how long the command took. The "total" figure at the end of each line is the one to compare.


RETRIES WITH PYTEST-RERUNFAILURES

A retry reruns a failed test, and the test only counts as failed if every attempt fails.

For one test, with a marker:

```python
@pytest.mark.flaky(reruns=2)
def test_something(): ...
```

For the whole run, from the command line:

```
pytest --reruns 2                             # up to 2 extra attempts for any failed test
pytest --reruns 2 --reruns-delay 1            # wait 1 second before each retry
pytest --reruns 2 --only-rerun TimeoutError   # retry only failures whose error matches
```

In the output, a rerun shows as R, and the summary counts them:

```
7 passed, 1 rerun
```

test_flaky_passes_on_retry fails its first attempt on purpose (it counts its attempts) and passes on the second, so every run shows "1 rerun". That is there to show what a rerun looks like.


RETRIES ARE A BANDAGE, NOT A CURE

A retry makes the run green, but the test still failed. Something in the test or the app behaved differently from one attempt to the next, and the retry hides that.

The risks:

- A real, intermittent bug in the app, such as a race condition that loses data one time in five, is retried away. The test was the only thing that noticed it.
- Flaky tests pile up, because nobody sees them. The suite gets slower with every retry, and one day a test fails every attempt and nobody knows why.
- Trust erodes. "It probably just needs a rerun" becomes the reaction to every red build.

A sensible policy:

- Use retries in CI only, not on your own computer, where you want to see every failure.
- Keep the number low: 1 or 2.
- Report reruns, and treat every rerun as a bug to look at.
- Never add a retry to make a new test pass.


WHAT A FLAKY TEST IS

A flaky test sometimes passes and sometimes fails, with no change to the test or the app. Each failure is either a false positive (the test fails although the app works, Module 03), or the test catching a real intermittent bug. You cannot tell which until you investigate.


COMMON CAUSES

- Timing: a reading call used as a check (inner_text, count, is_visible), or a fixed pause that is sometimes too short (Module 03).
- Shared state: a test relies on data or a page left by another test.
- Order: a test passes only after another test has run.
- Data collisions: two tests in parallel use the same name or account on a shared server.
- External services: an email server, a payment sandbox or a third-party API that is slow or down.
- Animations and transitions: an element still moving, or a dialog still fading out.
- Dates and times: a test that fails just after midnight, at month end, or in another time zone.
- Randomness in the test data, so each run uses different values.
- Resources: a slow or overloaded CI machine, especially with too many workers.


FINDING A FLAKY TEST

Run it many times and count the failures. In zsh (Mac):

```
for i in {1..20}; do pytest -q -k name_of_test || break; done
```

The loop runs the test up to 20 times and stops at the first failure, so the failure is the last thing on screen. || break means "if this run failed, stop the loop".

Then add pressure, because many flaky tests only fail under load:

```
for i in {1..10}; do pytest -q -n auto || break; done
```

Record evidence while you do it:

```
pytest -k name_of_test --tracing retain-on-failure
```

Open the trace of a failure (Module 04) and compare it with a passing run. The difference is usually the cause: an element still loading, a different item, a dialog in the way.

The optional plugin pytest-repeat adds a --count option that does the same as the loop: pytest --count 20 -k name_of_test


FIXING THEM

- Timing: replace reading calls and fixed pauses with expect (Module 03).
- Shared state or order: give each test its own setup through fixtures (Module 07).
- Data collisions: unique data per test, and clean up in teardown.
- External services: mock them (Module 10).
- Animations: wait for the final state with expect, for example to_be_hidden on a dialog that fades out.
- Dates and times: fix the clock (Module 10) and the time zone (browser_context_args, Module 07).
- Randomness: use fixed test data, or log the random value so a failure can be reproduced.
- Resources: fewer workers, or a bigger machine.


EXPECT RETRIES VERSUS TEST RETRIES

They sound alike and are completely different:

- expect retries one assertion for a few seconds, waiting for the page to reach a state. That is correct and is how Playwright is meant to be used.
- A test rerun throws away the whole test and runs it again from the start. That hides a test that failed.

Lean on the first. Be suspicious of the second.


THE FILES

- tests/test_09_parallel_retries.py - 4 test functions, 7 tests

test_independent_tests (4 cases)
  Each case adds one item and checks the counter says "1 item left". In parallel, the four cases run in different workers at the same time, and each still sees only its own item, because each test has its own browser context.

test_worker_id
  Shows the worker_id fixture: "master" without -n, "gw" and a number with -n.

test_unique_data_per_test
  Adds an item with a random name and checks there is exactly one item with that name.

test_flaky_passes_on_retry
  Fails its first attempt on purpose and passes its second, to show what a rerun looks like. It is marked @pytest.mark.flaky(reruns=2).


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Tests that depend on each other.
They pass in order and fail in parallel, or when run alone. The failure looks random. Every test must set up what it needs.

Trap 2 - Module-level variables as shared storage.
Each worker is a separate process with its own copy, so a list filled by one test is empty in another worker.

Trap 3 - Session fixtures with side effects.
With -n 4, a session fixture runs four times, once per worker. Four logins, four copies of data, or four writes to the same file.

Trap 4 - Shared data on a real server.
Two tests using the same name or account on a shared backend collide in parallel. Use unique names and clean up.

Trap 5 - Too many workers.
Each worker runs a whole browser. Beyond a point, memory runs out and the suite gets slower, not faster.

Trap 6 - Retries everywhere.
--reruns on every run makes intermittent bugs invisible, and the suite gets slower and less trustworthy.

Trap 7 - Adding a retry to make a new test pass.
A brand-new test that needs a retry is not working yet. Find out why it fails.

Trap 8 - Confusing expect retries with test reruns.
expect waiting for the page is correct. Rerunning a failed test hides a failure.

Trap 9 - Expecting print() output with -n.
It happens in the workers and does not appear. Run that test without -n to see it.

Trap 10 - Assuming the order of the output means something.
With -n, results appear as tests finish. The order says nothing about which test caused which.


HANDS-ON PRACTICE

1. Run the Module 09 tests:

```
pytest tests/test_09_parallel_retries.py -v
```

   Expect 7 passed and 1 rerun. test_flaky_passes_on_retry shows RERUN on its first line, then PASSED. A plain "pytest" now runs 96 tests: 95 passed, 1 xfailed, plus 1 rerun.

2. Run the same file in parallel and look at the worker names:

```
pytest tests/test_09_parallel_retries.py -v -n 4
```

   Each line starts with [gw0] to [gw3]. The order changes from run to run. test_worker_id now passes with a gw name instead of master.

3. Time the whole suite with and without parallel workers:

```
time pytest -q
time pytest -q -n auto
```

   Compare the total time at the end of each. The parallel run should be noticeably faster. The exact numbers depend on your computer and the demo site's speed.

4. Run one test many times, the way you would hunt a flaky test:

```
for i in {1..10}; do pytest -q -k test_unique_data_per_test || break; done
```

   It should pass all ten times, because it is independent and uses unique data.

If a test fails because the demo site changed:

The tests use the TodoPage page object, so a changed locator is fixed in one place: src/pw_learn/pages/todo_page.py. Open the site with playwright codegen https://demo.playwright.dev/todomvc/, hover over the element, and update the locator.

If pytest says "unrecognized arguments: -n", pytest-xdist is not installed in the active venv. If it says "'flaky' not found in markers", pytest-rerunfailures is not installed. Run the install step again.

Break it on purpose (this step is MEANT to fail):

1. In VS Code, create a new file in the tests folder called test_09_order_dependent.py, paste these lines and save:

```python
created = []


def test_first_creates_user():
    created.append("alice")
    assert created == ["alice"]


def test_second_uses_user():
    assert "alice" in created
```

2. Run them in order. Both pass:

```
pytest tests/test_09_order_dependent.py -v
```

3. Run the second one alone. It fails, because nothing created alice:

```
pytest tests/test_09_order_dependent.py -v -k second
```

4. Run them in parallel. With two workers, each test usually lands in a different process, so the second test fails:

```
pytest tests/test_09_order_dependent.py -v -n 2
```

   Run it a few times: the result can change. That is exactly what an order-dependent test looks like in a real suite.

5. Delete the file, so it does not stay in the suite:

```
rm tests/test_09_order_dependent.py
```


MENTAL MODEL

- -n runs tests in parallel workers, each a separate process with its own browser.
- Parallel only works if every test is independent: passes alone, in any order.
- Each worker has its own memory and its own session fixtures. The server and the disk are shared.
- Shared backend: unique data per test, cleaned up afterwards.
- Retries hide failures. Use them sparingly, in CI only, and investigate every rerun.
- A flaky test: reproduce it in a loop, record a trace, compare, fix the cause.


FOR YOUR OWN APP LATER

- Make parallel runs the default on CI from the start. Order-dependent tests are much easier to prevent than to untangle later.
- Give each worker its own test account using worker_id, if the app limits one session per account.
- Name all test data with a unique part and a recognisable prefix, such as autotest-3f9a1c2e, so leftovers are easy to find and delete.
- Agree as a team what a rerun means: a ticket to investigate, not a green build.
- Watch the time per test (pytest --durations=10). A few slow tests often dominate the total, and are worth speeding up before adding workers.
- If the test server struggles with many workers, that may be a real performance finding worth reporting.


QUIZ (answers below - try before peeking)

1. What does pytest -n auto do, and what does each worker have of its own?

2. Test A creates a user and Test B logs in as that user. They pass when run in order, but Test B fails with -n 4. Why, and how do you fix it?

3. A session-scoped fixture logs in and saves the login state to a file. How many times does it run with -n 4, and what can go wrong?

4. Two tests on a shared test server each create an item called "report" and then check there is exactly one. They pass alone but fail in parallel. Why, and what is the fix?

5. What is the difference between expect retrying an assertion and pytest-rerunfailures rerunning a test?

6. A team adds --reruns 3 to every CI run, and the suite goes green. What is the risk?

7. How do you find out whether a test is flaky, and how do you find the cause?

8. A test passes when run alone with -k, but fails in the full suite. What is the most likely cause?

9. Is more workers always faster?

10. DevOps stretch question: even in parallel, the suite takes 20 minutes on one CI machine. How could it run on several machines at once? (Just guess.)


ANSWERS


1. -n auto starts one worker process per CPU core and shares the tests out between them. Each worker is a separate Python process with its own browser, its own memory (module-level variables), and its own session-scoped fixtures.

Why it is faster: browser tests spend most of their time waiting for pages. While one worker waits, the others are busy, so the computer is used fully instead of sitting idle.

What each worker has of its own matters as much as the speed: anything a test keeps in memory is invisible to tests in other workers. What is shared is everything outside the processes: files on disk, and any server or database the tests use.

Common mistakes:
- Thinking the workers are threads in one program sharing memory. They are separate processes.
- Expecting the output in file order. Results appear as tests finish.

See: PARALLEL RUNS WITH PYTEST-XDIST, and WHAT IS SHARED AND WHAT IS NOT.


2. Test B depends on Test A having run first. With -n 4 they can run in different workers, or B can run before A finishes, so the user does not exist when B needs it. The fix is to make B independent: B creates its own user, or uses one set up by a fixture, and never relies on A.

Why it passed before: run one after another in the same process, A always ran first and left the user behind, so the dependency was invisible. Parallel runs, running B alone, or any change in order all expose it. The failure looks random because it depends on which worker gets which test.

The fix with a fixture:

```python
@pytest.fixture
def user():
    name = f"user-{uuid4().hex[:8]}"
    create_user(name)          # whatever creates a user in your app
    yield name
    delete_user(name)          # clean up, even if the test failed
```

Any test that needs a user asks for user and gets its own.

Common mistakes:
- Forcing the two tests onto the same worker with --dist loadfile or loadgroup. That hides the dependency instead of removing it.

See: THE ONE RULE: EVERY TEST MUST BE INDEPENDENT, and Trap 1.


3. Four times: once in each worker, because each worker is its own pytest session. The four logins can run at the same moment and write the same file, so one worker may read a half-written file, or one login may cancel another if the app allows only one session per account.

Why: "session" scope means once per session, and with xdist every worker runs a session of its own. Nothing coordinates them.

Ways to make it safe:
- One file per worker, using worker_id in the name, such as auth-gw0.json.
- A lock, so only one worker logs in and the others wait and reuse the file. Module 11 shows this.
- One account per worker, if the app allows only one session per account.

Common mistakes:
- Assuming session scope means once for the whole run, as it does without -n.

See: SESSION FIXTURES RUN ONCE PER WORKER, and Trap 3.


4. Because the server is shared by every worker. When both tests run at the same time, each creates a "report", so each sees two, and the check for exactly one fails. Give each test its own unique name, such as f"report-{uuid4().hex[:8]}", and check for that exact name.

Why: browser contexts keep each test's page private, but they do nothing for data stored on a server. Two tests in parallel are like two people using the same account at the same moment.

Also delete what each test created, in a fixture's teardown, so leftovers from failed runs do not confuse later ones.

Common mistakes:
- Counting "everything there is". Search for and assert on the test's own data only.
- Fixing it by running those tests without -n. That gives up the speed and leaves the collision for later.

See: SHARED BACKEND DATA: GIVE EACH TEST ITS OWN, and Trap 4.


5. expect keeps checking one assertion for a few seconds while the page catches up, which is normal and correct. A rerun throws away a whole failed test and runs it again from the start, which hides the failure.

Why the difference matters: expect waits for a state you expect to arrive, such as text that loads after a moment. That is how Playwright is meant to be used, and the test still fails if the state never comes. A rerun gives a test that already failed another chance. If the second attempt passes, the run is green, and the reason for the first failure is never looked at.

Common mistakes:
- Thinking reruns are the same as waiting. A rerun repeats every step, including any that worked.

See: EXPECT RETRIES VERSUS TEST RETRIES, and Trap 8.


6. Intermittent bugs become invisible. A failure that happens one time in five is retried until it passes, so the one test that noticed a real race condition in the app now reports green. Flaky tests also pile up unseen, the suite gets slower, and eventually a test fails every attempt and nobody knows why.

Why: a rerun answers "can this test pass?", not "does the app work?". Most apps under test have some real intermittent bugs, and those are exactly the failures a blanket retry hides.

A better policy: no retries on your own computer, at most 1 or 2 on CI, every rerun reported and treated as something to investigate, and never a retry added to make a new test pass.

Common mistakes:
- Treating "green after a rerun" as "passed". The test failed at least once.

See: RETRIES ARE A BANDAGE, NOT A CURE, and Trap 6.


7. Run it many times and count the failures, then record a trace of a failing run and compare it with a passing one.

How:

```
for i in {1..20}; do pytest -q -k name_of_test || break; done
```

The loop stops at the first failure. Then run with load, because many flaky tests only fail when the computer is busy:

```
for i in {1..10}; do pytest -q -n auto || break; done
```

Add --tracing retain-on-failure, open the trace of the failure (Module 04), and compare it with a passing run. The difference is usually the cause: an element not loaded yet, a different item in a list, a dialog in the way. Then check the common causes: reading calls used as checks, fixed pauses, shared data, order, external services, dates.

Common mistakes:
- Running it once, seeing it pass, and concluding it is fine.
- Adding a retry instead of finding out.

See: FINDING A FLAKY TEST, and COMMON CAUSES.


8. Another test is affecting it: it relies on something a different test left behind, or something another test changes breaks it. It is not independent.

Why: run alone, the test starts from a clean state and passes. In the full suite, another test that runs before it, or at the same time in another worker, changes something it depends on: data on a server, a shared file, an environment variable, or a module-level variable in the same worker.

To find which test: run the file it is in, then the tests just before it, narrowing down until the failure appears. Look for shared things: names, accounts, files, os.environ (Module 08 used monkeypatch for exactly this reason).

Common mistakes:
- Concluding the test is flaky and adding a retry. It fails for a specific reason that can be found.

See: THE ONE RULE: EVERY TEST MUST BE INDEPENDENT, and WHAT IS SHARED AND WHAT IS NOT.


9. No. Each worker runs a whole browser, so beyond a point the computer runs out of memory or CPU, and the app under test can become the bottleneck. Starting workers also takes time, so a small suite may not speed up at all.

Why: the speed-up comes from using time that would otherwise be spent waiting. Once the machine is fully busy, extra workers only compete for the same CPU and memory, and everything slows down. A test server may also struggle with many browsers at once, and start responding slowly, which causes timeouts.

Measure instead of guessing:

```
time pytest -q -n 2
time pytest -q -n 4
time pytest -q -n auto
```

Common mistakes:
- Setting -n 16 on a CI machine with 2 cores.

See: HOW MANY WORKERS, and Trap 5.


10. Split the suite into parts and run each part on a separate CI machine at the same time. This is called sharding.

Why: one machine can only run as many browsers as its CPU and memory allow. Several machines each running a share of the tests, in parallel, cut the total time roughly by the number of machines. Each machine can still use -n for its own workers.

In GitHub Actions, a matrix starts several copies of the same job, and each copy runs a different slice of the tests. A plugin such as pytest-split can divide the tests into balanced groups by how long they take:

```yaml
strategy:
  matrix:
    group: [1, 2, 3, 4]
```

with each job running something like pytest --splits 4 --group ${{ matrix.group }}. Module 12 sets this up.

Common mistakes:
- Splitting by hand, by file. Files take very different times, so one machine finishes long after the others.

See: Module 12 for CI.


End of Module 09. Next up: Module 10, API testing and network mocking (the request fixture, page.route, waiting for responses, and controlling time, permissions and offline mode).