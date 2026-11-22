PLAYWRIGHT WITH PYTHON - MODULE 04: DEBUGGING


GOAL

Find out why a test failed, quickly, whether it ran in front of you or on a machine you cannot see. Playwright gives you tools for three situations:

- While writing a test: watch it, pause it, try locators live (headed mode, the Inspector, codegen).
- After a test failed on your machine: screenshots, videos and traces.
- After a test failed somewhere else, such as CI: a trace file you download and replay.

By the end of this module you can:

- watch and pause a test, and step through it one action at a time
- record screenshots, videos and traces, only when a test fails
- open a trace in the Trace Viewer and read what happened at every step
- catch messages and errors from the page's own JavaScript
- follow a simple routine for any failing test

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tiny local pages built with page.set_content() (Module 03).


THE TOOLKIT AT A GLANCE

- --headed, --slowmo - watch the test run
- page.pause() - stop at a chosen line and open the Inspector
- PWDEBUG=1 - stop before the first action and step through the whole test
- codegen - record actions and find locators
- screenshots - a picture of the page or one element
- videos - a recording of the whole test
- traces - a full, replayable record: every action, a snapshot of the page before and after it, console messages, network requests and the test's source code
- page.on("console") and page.on("pageerror") - what the page's own JavaScript printed or crashed with

Traces are the most useful of all. If you learn one tool from this module, learn traces.


WATCHING A TEST

```
pytest FILES/test_04_debugging.py --headed
pytest FILES/test_04_debugging.py --headed --slowmo 500
pytest FILES/test_04_debugging.py --headed --browser-channel chrome
```

- --headed shows the browser window. Tests are headless by default.
- --slowmo 500 waits 500 milliseconds before every action, so you can follow it.
- --browser-channel chrome uses your installed Google Chrome instead of Playwright's Chromium. Useful if a problem only seems to happen in real Chrome.

Watching is good for a first look, but things happen fast and leave nothing behind. For anything more, use the tools below.


PAUSING: PAGE.PAUSE()

Put this line in a test where you want to stop:

```python
page.pause()
```

Run that test headed:

```
pytest FILES/test_04_debugging.py --headed -k todo_flow
```

The browser stops at that line and the Playwright Inspector opens. While paused you can look at the page, try locators, and continue step by step (next section). Click Resume to let the test continue.

page.pause() needs a visible (headed) browser. Remove it before committing: it is a debugging aid, not part of a test.


PAUSING: PWDEBUG=1

PWDEBUG=1 debugs a test without editing it:

```
PWDEBUG=1 pytest -s FILES/test_04_debugging.py -k todo_flow
```

- The browser opens headed, and the Inspector opens paused before the first action.
- Timeouts are switched off while debugging, so nothing fails while you look around.
- -s lets the Inspector and any print() output through. pytest normally captures output.
- PWDEBUG=1 at the start of the line sets an environment variable for that one command only.

Use page.pause() when you know which line to look at, and PWDEBUG=1 when you want to step through the whole test from the start.


THE PLAYWRIGHT INSPECTOR

The Inspector is the window that opens with page.pause(), PWDEBUG=1 and codegen.

- Resume (play button): run until the end, or until the next page.pause().
- Step over: run only the next action, then stop again. The action about to run is highlighted on the page.
- Locator box: type a locator, such as get_by_role("button", name="Clear completed"). Matching elements light up on the page, and the box shows how many matched.
- Pick locator (target icon): click any element on the page to get the locator Playwright would use for it.
- Log: each action, and what Playwright waited for before doing it.

The locator box is the quickest way to fix a locator: try variations until exactly one element lights up, then copy it into the test.


PAUSING IN PYTHON: BREAKPOINT()

Python's own debugger works too:

```python
breakpoint()
```

The test stops at that line and the terminal shows a (Pdb) prompt. With --headed, the browser stays open, so you can look at it. In the prompt you can run Python, for example page.url or page.get_by_test_id("todo-item").count(). Type c and press Enter to continue.

Breakpoints set in VS Code with the Python extension work the same way, if you run the test from VS Code's Testing panel.


CODEGEN IN DEPTH

Module 02 used codegen to find locators. More options:

```
playwright codegen https://demo.playwright.dev/todomvc/
playwright codegen --target python-pytest https://demo.playwright.dev/todomvc/
playwright codegen --target python-pytest -o recorded.py https://demo.playwright.dev/todomvc/
playwright codegen --viewport-size "800,600" https://demo.playwright.dev/todomvc/
playwright codegen --device "iPhone 13" https://demo.playwright.dev/todomvc/
```

- --target python-pytest writes the code as a pytest test with the page fixture, the same style as these notes.
- -o recorded.py also saves the code to a file when you close the browser.
- --viewport-size and --device record at a different window size, or as a phone.
- The Inspector also has buttons to add assertions while recording (for example, "assert visibility" and "assert text"): click the button, then the element.

What to do with recorded code:

- Copy the good locators and steps into your own test.
- Add real assertions: recorded code mostly clicks and types, and a test without assertions proves very little.
- Remove repeated or accidental steps.
- Do not save recordings into FILES/ with a name starting with test_, or pytest will run them as tests.


SCREENSHOTS

In a test:

```python
page.screenshot(path="page.png")                          # what is visible in the window
page.screenshot(path="page.png", full_page=True)          # the whole page, including what needs scrolling
page.get_by_test_id("todo-item").screenshot(path="item.png")   # one element only
```

From the command line, for every test without changing any code:

```
pytest --screenshot only-on-failure
```

Values: on (after every test), off (the default), only-on-failure.

A screenshot shows one moment, the end of the test. It does not show what happened before.


VIDEOS

```
pytest --video retain-on-failure
```

Values: on, off (the default), retain-on-failure (record every test, keep the video only if the test failed).

A video shows the whole test in motion, which helps with things a single picture misses, such as a popup that flashes up and closes. Recording makes the run a little slower.


TRACES

A trace is a zip file with a complete record of a test:

- every action and assertion, with how long it took and what it waited for
- a snapshot of the page before and after each action: real HTML you can inspect, not just a picture
- a filmstrip of screenshots
- console messages and page errors
- network requests and responses
- the test's source code, with the current line highlighted

From the command line:

```
pytest --tracing retain-on-failure
```

Values: on (keep a trace for every test), off (the default), retain-on-failure (record every test, keep the trace only if the test failed).

retain-on-failure is the usual choice: no extra files when everything passes, and a full record when something fails.

In code, for one block of steps (test_manual_trace does this):

```python
context = browser.new_context()
context.tracing.start(screenshots=True, snapshots=True, sources=True)
page = context.new_page()
# ... steps ...
context.tracing.stop(path="trace.zip")
context.close()
```

- Tracing belongs to the browser context (the "incognito window" each test gets, Module 01), so it is started and stopped on the context.
- screenshots=True records the filmstrip, snapshots=True records the page before and after each action, sources=True includes the test code.
- The test uses its own context from the browser fixture, so its tracing never clashes with the --tracing option.


THE TRACE VIEWER

Open a trace:

```
playwright show-trace test-results/<test-folder>/trace.zip
```

Or open https://trace.playwright.dev in a browser and drag the zip onto it. The page reads the file inside your browser and does not upload it.

What you see:

- Actions (left): every step, in order. Click one to jump to it. A failed step is shown in red.
- Timeline (top): a filmstrip of the page over time. Hover to preview.
- Snapshot (middle): the page at that step, with tabs for Before, Action and After. It is real HTML: you can open browser DevTools on it, and use the pick-locator button to get a locator for any element.
- Tabs (bottom): Call (the action's details and how long it waited), Log (what it waited for), Errors, Console, Network, Source (your test code with the current line highlighted), Attachments.

How to read a failure: click the red step, look at the Before snapshot, and read the error and the Log tab. Usually the snapshot shows the reason straight away: a different text, a missing element, a popup covering a button, a loading spinner still showing.


CONSOLE MESSAGES AND PAGE ERRORS

Web pages run their own JavaScript, which can print messages (console.log) or crash (an uncaught error). Both are invisible in a normal test run, but often explain a failure, for example a button that does nothing because the page's script crashed.

Collect everything a page prints:

```python
messages = []
page.on("console", lambda message: messages.append(f"{message.type}: {message.text}"))
errors = []
page.on("pageerror", lambda error: errors.append(error.message))
```

page.on registers a function that runs every time the event happens. Register it before the page is loaded, or you miss anything printed while loading.

Wait for one specific message or error, which is what the tests do:

```python
with page.expect_console_message() as message_info:
    page.set_content("<script>console.log('hello from the page')</script>")
assert message_info.value.text == "hello from the page"
```

The with block starts listening first, then runs the code inside it, then waits until the message arrives. Starting to listen before the action matters: the message is printed while set_content is running, so listening afterwards would be too late.

Traces record console messages and page errors too, in the Console and Errors tabs.


WHERE THE FILES GO

Screenshots, videos and traces from --screenshot, --video and --tracing are saved under test-results/ in the folder you run pytest from, one subfolder per test:

```
ls test-results
```

- Each run clears test-results/ first, so old files do not pile up.
- --output other-folder saves them somewhere else.
- test-results/ is in .gitignore (Module 01). Never commit these files: they are large, change on every run, and can show whatever was on the page.

Files saved by your own code, such as page.screenshot(path=...), go wherever the path says. The tests use tmp_path (a temporary folder pytest creates for each test), so nothing is left in the repo.


PLAIN ASSERT ON FILES IS FINE

Module 03 said to check results with expect, not with a plain assert. That rule is about the page, which keeps changing. A file is different: page.screenshot() returns only after the file has been written, so checking it straight away is correct:

```python
page.screenshot(path=shot, full_page=True)
assert shot.exists()
```

The same goes for any value that does not change after you read it: a file, a returned message, a number you calculated. Use expect for the page, and a plain assert for everything else.


A DEBUGGING ROUTINE

1. Read the error message. It names the step, the locator, and what was expected versus found.
2. Run the failing test alone: pytest -k name_of_test
3. Rerun it with a trace: pytest -k name_of_test --tracing retain-on-failure
4. Open the trace, click the red step, and look at the Before snapshot.
5. If the locator is the problem, fix it with the pick-locator button or the Inspector's locator box.
6. If the timing is the problem, replace any reading call or fixed pause with an expect (Module 03).
7. If the page's own script is the problem, look at the Console and Errors tabs.


THE FILES

- FILES/test_04_debugging.py - 6 tests

add_todos(page, *items)
  A helper that opens the TodoMVC demo and adds any number of items. *items collects all the extra arguments into a tuple, so add_todos(page, "buy milk", "walk the dog") adds two items.

test_page_screenshot
  Adds an item, takes a full-page screenshot into tmp_path, and checks the file exists and is not empty.

test_element_screenshot
  The same, for one element: the to-do item.

test_manual_trace
  Starts tracing on its own browser context, adds two items, checks there are two, saves the trace into tmp_path, and checks the file exists.

test_console_message
  Loads a tiny page whose script prints "hello from the page", and checks the message was received.

test_page_error
  Loads a tiny page whose script crashes with the error "boom", and checks the error was received.

test_todo_flow
  A normal test: adds two items, ticks "buy milk", checks the counter says "1 item left" and that both items are still listed. The break-it-on-purpose step uses this test to produce a trace.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Debugging without a trace.
Rerunning a failing test again and again, adding prints, guessing. One run with --tracing retain-on-failure usually shows the reason in a minute.

Trap 2 - Leaving page.pause() in a test.
It needs a headed browser and someone to click Resume. Remove it before committing.

Trap 3 - --tracing on for everyday runs.
Every test then keeps a trace, which takes time and disk space. Use retain-on-failure, and on only when you want a trace of a passing test.

Trap 4 - Committing test-results/.
Traces, videos and screenshots are large, change on every run, and can contain data from the page. Keep test-results/ in .gitignore.

Trap 5 - Listening too late.
page.on("console", ...) registered after the page has loaded misses everything printed while loading. Register listeners first, or wrap the action in a with page.expect_... block.

Trap 6 - Saving codegen output as test_something.py in FILES/.
pytest collects it and runs it on every run. Recorded scripts usually have no assertions, so they pass whether or not the app works (a false negative).

Trap 7 - Trusting a single screenshot.
A screenshot shows the end of the test, not the step that went wrong. A trace shows every step.

Trap 8 - Forgetting -s with PWDEBUG=1.
Without -s, pytest captures output, which can get in the way of the debugging session.


HANDS-ON PRACTICE

1. Run the Module 04 tests:

```
pytest FILES/test_04_debugging.py -v
```

   Expect 6 passed. A plain "pytest" now runs 23 tests: 2 from Module 01, 7 from Module 02, 8 from Module 03 and 6 from Module 04.

2. Step through a test with PWDEBUG:

```
PWDEBUG=1 pytest -s FILES/test_04_debugging.py -k todo_flow
```

   The browser and the Inspector open, paused before the first action. Click Step over a few times and watch each action highlighted on the page. Type get_by_test_id("todo-item") in the locator box and see how many elements light up. Click Resume to finish.

3. Record a trace of a passing test and open it:

```
pytest FILES/test_04_debugging.py -k todo_flow --tracing on
ls test-results
playwright show-trace test-results/<folder from ls>/trace.zip
```

   Click through the actions on the left, and switch between the Before and After tabs on the "check" step to see the item get ticked.

If a test fails because the demo site changed:

The TodoMVC tests rely on the demo site's current placeholder, test ids and counter text. The site can change after these notes were written. If one of them times out on a locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

test_console_message and test_page_error use local pages built with set_content(), so they work without the internet. If one of those fails, the cause is in the test file itself.

Break it on purpose (this step is MEANT to fail):

1. In FILES/test_04_debugging.py, line 65, change
   expect(page.get_by_test_id("todo-count")).to_have_text("1 item left")
   to
   expect(page.get_by_test_id("todo-count")).to_have_text("2 items left")
   To confirm the line number: grep -n "1 item left" FILES/test_04_debugging.py
2. Run it with a trace, a screenshot and a video, kept only on failure:

```
pytest FILES/test_04_debugging.py -k todo_flow --tracing retain-on-failure --screenshot only-on-failure --video retain-on-failure
```

3. The test fails after about 5 seconds: the counter says "1 item left", not "2 items left".
4. Look at what was saved, and open the trace:

```
ls test-results/*
playwright show-trace test-results/<folder from ls>/trace.zip
```

   In the Trace Viewer, click the red step. The snapshot shows the counter with "1 item left", and the error shows the expected and the actual text. The folder also has the screenshot and the video.
5. Change line 65 back to "1 item left" and run again. It passes, and test-results/ no longer contains a trace for it.


MENTAL MODEL

- Writing a test: watch it (--headed), pause it (page.pause, PWDEBUG=1), find locators (Inspector, codegen).
- A test failed: rerun it with --tracing retain-on-failure and open the trace.
- In the trace: click the red step, look at the Before snapshot, read the error and the log.
- The page's own JavaScript: console messages and page errors.
- Evidence files live in test-results/ and never go into Git.


FOR YOUR OWN APP LATER

- Make --tracing retain-on-failure part of every CI run (Module 09). A trace from a CI failure is often the only way to see what happened there.
- When a test fails only sometimes, keep the traces of a few failures and compare them. The difference between them is usually the cause.
- Watch the Console and Errors tabs for crashes in the app's own scripts. Those are real bugs to report to the developers, with the trace attached.
- A trace contains whatever the page showed, including any real data. Only share traces from apps with test data, and only with people who are allowed to see it.


QUIZ (answers below - try before peeking)

1. A test fails on CI with a timeout, and you cannot reproduce it on your Mac. Which pytest option records what happened, and which command opens the result?

2. What is the difference between --tracing on and --tracing retain-on-failure, and which should a normal CI run use?

3. You want to step through test_todo_flow one action at a time without editing the file. Which command do you run?

4. In test_console_message (line 51), why is page.set_content() inside the with page.expect_console_message() block instead of before it?

5. Module 03 said to check results with expect, but test_page_screenshot uses a plain assert shot.exists() (line 26). Why is that correct here?

6. You record a session with playwright codegen --target python-pytest -o FILES/test_recorded.py and leave it there. pytest now runs it and it passes every time. What is the problem?

7. Where do --screenshot, --video and --tracing save their files, and why must that folder stay out of Git?

8. DevOps stretch question: a test fails on CI with --tracing retain-on-failure, but the CI machine is deleted when the job ends. How do you get the trace? (Just guess.)


ANSWERS


1. --tracing retain-on-failure records a trace of every test and keeps it only if the test failed. Open it with playwright show-trace test-results/<test-folder>/trace.zip, or by dragging the zip onto https://trace.playwright.dev.

Why: a trace is a complete record of the run: every action, a snapshot of the page before and after each one, console messages, network requests and the test code. You can replay the CI failure step by step on your own machine, even though you could not reproduce it there. Click the red step and look at the Before snapshot: it usually shows the reason (a different text, a missing element, a popup in the way).

Common mistakes:
- Choosing --screenshot only-on-failure. A screenshot shows only the end of the test, not the step that went wrong or why.
- Rerunning the test on your Mac until it fails. It may never fail there, and a passing rerun tells you nothing about CI.

See: TRACES, and THE TRACE VIEWER.


2. on keeps a trace for every test. retain-on-failure records every test but keeps the trace only when the test failed. A normal CI run should use retain-on-failure.

Why: with on, every passing test also leaves a trace, which costs time and disk space and buries the one trace you need. With retain-on-failure, a green run leaves nothing behind, and a red run leaves exactly the traces of the failed tests. Use on only when you want to study a passing test, as in hands-on step 3.

The same pattern exists for videos (--video retain-on-failure) and screenshots (--screenshot only-on-failure).

Common mistakes:
- Thinking retain-on-failure records only after the failure. It records the whole test from the start, then decides at the end whether to keep it.

See: TRACES, and Trap 3.


3. PWDEBUG=1 pytest -s FILES/test_04_debugging.py -k todo_flow

Why: PWDEBUG=1 opens the browser headed and the Inspector paused before the first action, and switches off timeouts while you look around. Step over runs one action at a time. -k todo_flow selects the test, and -s lets the debugging output through.

page.pause() would also work, but you would have to add it to the file and remember to remove it.

Common mistakes:
- pytest --headed --slowmo 500. That only slows the test down. You can watch, but you cannot stop it or try locators.
- Writing PWDEBUG=1 on a separate line. Written in front of the command, it applies to that command only. On a line of its own, without export, pytest does not see it.

See: PAUSING: PWDEBUG=1, and THE PLAYWRIGHT INSPECTOR.


4. Because the message is printed while set_content() is running. The with block starts listening first, then runs set_content(), then waits for the message. If set_content() ran before the block, the message would already have been printed, and the test would wait for one that never comes.

Why: an event can only be caught by something that is already listening. The with page.expect_... pattern guarantees the order: listen, act, wait. If nothing arrives, it fails after the timeout with a clear error.

The same applies to page.on("console", ...): register it before loading the page, or you miss messages printed while loading.

Common mistakes:
- Thinking the with block is just tidier code. The order is the point: listening has to start before the action that triggers the event.

See: CONSOLE MESSAGES AND PAGE ERRORS, and Trap 5.


5. Because shot.exists() checks a file, not the page. page.screenshot() returns only after the file has been written, so the file is already there when the assert runs, and it does not change afterwards.

Why: the Module 03 rule exists because the page keeps changing: text arrives late, items appear after a moment, so a check that reads once can be too early. A file on disk does not change after the call that wrote it. expect is made for page elements and the page itself, and a plain assert is right for everything else: files, returned values, numbers you calculated.

The same applies on line 53: message_info.value.text is a value that has already arrived, so a plain assert is correct.

Common mistakes:
- Concluding that plain asserts are always wrong. They are wrong for page state, and fine for values that cannot change anymore.

See: PLAIN ASSERT ON FILES IS FINE.


6. It has no real assertions, so it passes whether or not the app works. That is a false negative. It also runs on every pytest run, because its name starts with test_ and it is in FILES/.

Why: codegen records what you did (clicks and typing), not what should be true afterwards. A test that clicks through the app and never checks a result can only fail if a click cannot find its element. If the app silently stops saving, the recording still passes. Recorded code also tends to contain repeated and accidental steps.

What to do: use the recording as raw material. Copy the useful locators and steps into a proper test, add assertions on what the user should see, and delete the recording or save it outside FILES/ (or under a name that does not start with test_).

Common mistakes:
- Thinking a recorded test is fine because it is green. A test that cannot fail for the right reason proves nothing.

See: CODEGEN IN DEPTH, and Trap 6.


7. In test-results/, in the folder you run pytest from, one subfolder per test. It stays out of Git because the files are large, change on every run, and can show whatever was on the page.

Why: traces and videos are often several megabytes each, and a new set is made on every run, so committing them would bloat the repo quickly. They also contain everything the page displayed, which for a real app can include personal or internal data. test-results/ is already in .gitignore from Module 01. Each run clears the folder first, so files do not pile up locally either.

Common mistakes:
- Thinking files in test-results/ are kept between runs. Each run starts by clearing the folder, so copy a trace somewhere else if you want to keep it.

See: WHERE THE FILES GO, and Trap 4.


8. Upload test-results/ as a CI artifact before the job ends, then download it from the CI run's page and open the trace on your machine.

Why: a CI machine is created for one job and deleted afterwards, together with every file on it. An artifact is a file the CI system keeps after the job, attached to the run. On GitHub Actions this is done with the actions/upload-artifact step, usually set to run when the job failed. You download the zip, unpack it, and open the trace with playwright show-trace or https://trace.playwright.dev.

If the repo is public, artifacts can be downloaded by others, so the same care applies as with committing them.

Common mistakes:
- Printing more output in the CI log instead. Logs help, but a trace shows what the page actually looked like at every step.

See: TRACES, and Module 09 for CI.


End of Module 04. Next up: Module 05, fixtures and the Page Object Model (your own pytest fixtures, and page objects that keep locators out of tests).