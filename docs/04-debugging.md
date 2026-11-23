PLAYWRIGHT WITH PYTHON - MODULE 04: DEBUGGING AND COMMAND-LINE OPTIONS


GOAL

Find out why a test failed, quickly, whether it ran in front of you or on a machine you cannot see. Playwright gives you tools for three situations:

- While writing a test: watch it, pause it, try locators live (headed mode, the Inspector, codegen).
- After a test failed on your machine: screenshots, videos and traces.
- After a test failed somewhere else, such as CI: a trace file you download and replay.

Most of these are switched on from the command line, without changing any test code, so this module starts with the command-line options.

By the end of this module you can:

- run tests in any browser, headed or headless, slowed down, with any evidence you need
- watch and pause a test, and step through it one action at a time
- record screenshots, videos and traces, only when a test fails
- open a trace in the Trace Viewer and read what happened at every step
- catch messages and errors from the page's own JavaScript
- follow a simple routine for any failing test

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tiny local pages built with page.set_content() (Module 03).


COMMAND-LINE OPTIONS

pytest-playwright adds its own options to pytest. To see them all, with their exact spelling and allowed values:

```
pytest --help
```

Scroll to the section headed "Playwright". The options below are the ones you will use most.


Which browser

```
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit
pytest --browser chromium --browser webkit
pytest --browser-channel chrome
```

- --browser chooses the browser engine. chromium is the default. firefox is Firefox. webkit is the engine behind Safari: it behaves like Safari, but it is not the Safari app.
- Each browser must be installed first: playwright install firefox webkit
- --browser can be given more than once. Every test then runs once per browser, so 23 tests in two browsers give 46 results.
- The browser is shown at the end of each test name: test_has_title[chromium], test_has_title[webkit]. -k webkit runs only the WebKit runs.
- --browser-channel chrome uses your installed Google Chrome instead of Playwright's Chromium. Useful when a problem seems to happen only in real Chrome. msedge does the same for Microsoft Edge.


Watching

```
pytest --headed
pytest --headed --slowmo 500
```

- Tests are headless by default: the browser runs without a window.
- --headed shows the window.
- --slowmo 500 waits 500 milliseconds before every action, so you can follow it. It slows every action, so use it only for watching.


Evidence: screenshots, videos and traces

```
pytest --screenshot only-on-failure
pytest --video retain-on-failure
pytest --tracing retain-on-failure
pytest --output evidence
```

- --screenshot: on (after every test), off (the default), only-on-failure.
- --full-page-screenshot: together with --screenshot, captures the whole page instead of only the visible part.
- --video: on, off (the default), retain-on-failure (record every test, keep the video only if it failed).
- --tracing: on, off (the default), retain-on-failure (record every test, keep the trace only if it failed).
- --output: the folder for all these files. The default is test-results.
- These options can be combined in one command.


Devices (a preview of Module 07)

```
pytest --device "iPhone 13"
```

Runs every test as if on that phone: screen size, touch, and the phone's browser identity. Module 07 covers device emulation properly.


Useful pytest options

These come from pytest itself and work with any test:

```
pytest -v                  # one line per test, with PASSED or FAILED
pytest -q                  # quiet: dots and a summary only
pytest -k todo_flow        # only tests whose name contains "todo_flow"
pytest -x                  # stop at the first failure
pytest --lf                # rerun only the tests that failed last time
pytest -s                  # show print() output (normally hidden)
pytest --durations=0       # list every test with how long it took
pytest tests/test_04_debugging.py::test_todo_flow     # one specific test
```

-k also accepts and, or and not: pytest -k "todo and not flow"


Combining them

A typical command to investigate a failing test:

```
pytest -k todo_flow --headed --slowmo 300 --tracing retain-on-failure --screenshot only-on-failure
```

And a typical CI command, which runs headless by default:

```
pytest --browser chromium --browser webkit --tracing retain-on-failure --video retain-on-failure
```


PAUSING: PAGE.PAUSE()

Put this line in a test where you want to stop:

```python
page.pause()
```

Run that test headed:

```
pytest tests/test_04_debugging.py --headed -k todo_flow
```

The browser stops at that line and the Playwright Inspector opens. While paused you can look at the page, try locators, and continue step by step. Click Resume to let the test continue.

page.pause() needs a visible (headed) browser. Remove it before committing: it is a debugging aid, not part of a test.


PAUSING: PWDEBUG=1

PWDEBUG=1 debugs a test without editing it:

```
PWDEBUG=1 pytest -s tests/test_04_debugging.py -k todo_flow
```

What each part does:

- PWDEBUG=1 opens the browser headed, opens the Inspector paused before the first action, and switches off timeouts while you look around. Written in front of the command, it applies to that one command only.
- -s stops pytest capturing output, so the Inspector and any print() get through.
- -k todo_flow runs only tests whose name contains that text.
- tests/test_04_debugging.py limits the run to that file.

On Windows (PowerShell), the Mac form does not work. Set the variable first, then clear it afterwards:

```
$env:PWDEBUG = "1"
pytest -s tests/test_04_debugging.py -k todo_flow
Remove-Item Env:PWDEBUG
```

Use page.pause() when you know which line to look at, and PWDEBUG=1 when you want to step through the whole test from the start.


THE PLAYWRIGHT INSPECTOR

The Inspector is the window that opens with page.pause(), PWDEBUG=1 and codegen.


What appears on screen

Two separate windows open:

1. A Chromium browser window, showing a blank page at first.
2. The Playwright Inspector: a narrower window with your test code and a row of buttons along the top.

If you only see the browser, the Inspector is probably behind it or on another part of the screen. Check the Dock, or press Cmd+Tab (Alt+Tab on Windows) and look for a second window.


The buttons along the top

They are icons without labels. Hover over one to see its name. From left to right:

- Resume (a play triangle) - run to the end of the test, or to the next page.pause().
- Pause (two vertical bars) - pause a test that is running.
- Step over (an arrow curving over a dot) - run only the next action, then stop again. This is the one for going through a test line by line.
- Record (a circle) - start recording your clicks and typing as code.
- Pick locator (a target or crosshair) - click any element on the page to get the locator Playwright would use for it.
- Clear - clear the recorded code.

Below the buttons:

- Locator box - type a locator, such as get_by_role("button", name="Clear completed"). Matching elements light up on the page, and the box shows how many matched. This is the quickest way to fix a locator: try variations until exactly one element lights up, then copy it into the test.
- Your test code, with the line about to run highlighted. The same action is also highlighted on the page.
- Log - each action, and what Playwright waited for before doing it.


Using it

1. Start the test with PWDEBUG=1 (previous section) or page.pause().
2. Click Step over once for each action, and watch the page change.
3. At any point, type a locator in the locator box to see what it matches right now.
4. Click Resume to run the rest of the test, or close the browser window to stop.


If the Inspector does not open

Check that the variable reached pytest:

```
echo $PWDEBUG
```

If it prints nothing, the usual causes are:

- PWDEBUG=1 was typed on a separate line. It has to be on the same line, in front of pytest.
- You are using PowerShell on Windows, where that form does not work. See the previous section.
- The -s option is missing, so pytest captures the output. Add -s.

If the test runs to the end without stopping, there is no page.pause() in it and PWDEBUG was not set, so nothing paused it.


PAUSING IN PYTHON: BREAKPOINT()

Python's own debugger is an alternative that works in the terminal, with no extra window.

Add this line in the test, where you want to stop:

```python
breakpoint()
```

Run the test headed, so you can see the page:

```
pytest -s tests/test_04_debugging.py -k todo_flow --headed
```

The test stops at that line and the terminal shows a (Pdb) prompt. There you can type:

- n then Enter - run the next line (the same idea as Step over)
- c then Enter - continue to the end
- any Python, to look at things: page.url, or page.get_by_test_id("todo-item").count()
- q then Enter - quit the test

-s is needed, otherwise pytest captures the output and you never see the prompt.

Remove the breakpoint() line when you are done. A forgotten one makes the test wait forever, and on CI the job runs until it times out.

Breakpoints set in VS Code with the Python extension work the same way, if you run the test from VS Code's Testing panel.

Which to use: the Inspector is better for locators, because it highlights matches on the page as you type. breakpoint() is better for inspecting Python values.


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
- -o recorded.py also saves the code to a file when you close the browser. It saves it in the repo root, which is outside tests/.
- --viewport-size and --device record at a different window size, or as a phone.
- The Inspector also has buttons to add assertions while recording (for example "assert visibility" and "assert text"): click the button, then the element.

What to do with recorded code:

- Copy the good locators and steps into your own test.
- Add real assertions: recorded code mostly clicks and types, and a test without assertions proves very little.
- Remove repeated or accidental steps.
- Do not save recordings into tests/ with a name starting with test_, or pytest will run them as tests.


SCREENSHOTS IN CODE

```python
page.screenshot(path="page.png")                               # what is visible in the window
page.screenshot(path="page.png", full_page=True)               # the whole page, including what needs scrolling
page.get_by_test_id("todo-item").screenshot(path="item.png")   # one element only
```

A screenshot shows one moment. Taken by --screenshot, that moment is the end of the test, not the step that went wrong.


VIDEOS

A video (--video) shows the whole test in motion, which helps with things a single picture misses, such as a popup that flashes up and closes. Recording makes the run a little slower.


TRACES

A trace is a zip file with a complete record of a test:

- every action and assertion, with how long it took and what it waited for
- a snapshot of the page before and after each action: real HTML you can inspect, not just a picture
- a filmstrip of screenshots
- console messages and page errors
- network requests and responses
- the test's source code, with the current line highlighted

From the command line, --tracing retain-on-failure is the usual choice. A green run leaves nothing behind, and a red run leaves a full record of each failed test.

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

Find the exact folder name with ls test-results first, or type test-results/ and press Tab to complete it. The folder is named after the test, for example tests-test-04-debugging-py-test-todo-flow-chromium.

You can also open https://trace.playwright.dev in a browser and drag the zip onto it. The page reads the file inside your browser and does not upload it, which is useful for a trace someone sends you from their CI run.

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

The with block starts listening first, then runs the code inside it, then waits until the message arrives. The order matters: a console message happens once and is not stored anywhere, so anything not already listening misses it.

Traces record console messages and page errors too, in the Console and Errors tabs.


WHERE THE FILES GO

Screenshots, videos and traces from --screenshot, --video and --tracing are saved under test-results/ in the folder you run pytest from, one subfolder per test:

```
ls test-results
```

- Each run clears test-results/ first, so old files do not pile up. Copy a trace somewhere else if you want to keep it.
- --output other-folder saves them somewhere else.
- test-results/ is in .gitignore (Module 01). Never commit these files: they are large, change on every run, and show whatever was on the page.

Files saved by your own code, such as page.screenshot(path=...), go wherever the path says. The tests use tmp_path (a temporary folder pytest creates for each test), so nothing is left in the repo.


PLAIN ASSERT ON FILES IS FINE

Module 03 said to check results with expect, not with a plain assert. That rule is about the page, which keeps changing. A file is different: page.screenshot() returns only after the file has been written, so checking it straight away is correct:

```python
page.screenshot(path=shot, full_page=True)
assert shot.exists()
```

The same goes for any value that cannot change after you read it: a file, a message that has already arrived, a number you calculated. Use expect for the page, and a plain assert for everything else.


A DEBUGGING ROUTINE

1. Read the error message. It names the step, the locator, and what was expected versus found.
2. Run the failing test alone: pytest -k name_of_test
3. Rerun it with a trace: pytest -k name_of_test --tracing retain-on-failure
4. Open the trace, click the red step, and look at the Before snapshot.
5. If the locator is the problem, fix it with the pick-locator button or the Inspector's locator box.
6. If the timing is the problem, replace any reading call or fixed pause with an expect (Module 03).
7. If the page's own script is the problem, look at the Console and Errors tabs.
8. If it fails in only one browser, run that browser alone with --browser and --headed, and compare.


THE FILES

- tests/test_04_debugging.py - 6 tests

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
It needs a headed browser and someone to click Resume. Remove it before committing. The same applies to breakpoint().

Trap 3 - --tracing on for everyday runs.
Every test then keeps a trace, which takes time and disk space and buries the one you need. Use retain-on-failure, and on only when you want a trace of a passing test.

Trap 4 - Committing test-results/.
Traces, videos and screenshots are large, change on every run, and contain whatever the page showed. Keep test-results/ in .gitignore.

Trap 5 - Listening too late.
page.on("console", ...) registered after the page has loaded misses everything printed while loading. Register listeners first, or wrap the action in a with page.expect_... block.

Trap 6 - Saving codegen output as test_something.py in tests/.
pytest collects it and runs it on every run. Recorded scripts have no assertions, so they pass whether or not the app works.

Trap 7 - Trusting a single screenshot.
A screenshot shows the end of the test, not the step that went wrong. A trace shows every step.

Trap 8 - Forgetting -s with PWDEBUG=1.
Without -s, pytest captures output, which gets in the way of the debugging session.

Trap 9 - --browser for a browser that is not installed.
pytest --browser webkit fails at once with "Executable doesn't exist" and a hint to run playwright install. Install each browser once: playwright install firefox webkit

Trap 10 - Leaving --slowmo or --headed in a CI command.
--slowmo makes every action slower for no benefit, and a CI machine has no screen for --headed. Keep them for watching tests on your own computer.

Trap 11 - A typo in -k runs nothing, quietly.
pytest -k tody_flow does not fail. It reports "6 deselected" and runs no tests, which is easy to misread as a pass. Check the collected and deselected counts in the output.


HANDS-ON PRACTICE

1. Run the Module 04 tests:

```
pytest tests/test_04_debugging.py -v
```

   Expect 6 passed. A plain "pytest" now runs 23 tests: 2 from Module 01, 7 from Module 02, 8 from Module 03 and 6 from Module 04.

2. Try other browsers:

```
playwright install firefox webkit
pytest tests/test_04_debugging.py --browser chromium --browser webkit -v
```

   Expect 12 passed: each test once per browser, with [chromium] or [webkit] at the end of its name. The first install takes a minute or two.

3. Step through a test with PWDEBUG:

```
PWDEBUG=1 pytest -s tests/test_04_debugging.py -k todo_flow
```

   Two windows open: a Chromium browser and the Playwright Inspector, paused before the first action. In the Inspector, click Step over (the third button, an arrow curving over a dot) a few times, and watch each action highlighted on the page. Type get_by_test_id("todo-item") in the locator box and see how many elements light up. Click Resume (the play triangle) to finish. If you cannot see the Inspector, look behind the browser window or press Cmd+Tab.

4. Record a trace of a passing test and open it:

```
pytest tests/test_04_debugging.py -k todo_flow --tracing on
ls test-results
```

   ls prints the folder name, for example tests-test-04-debugging-py-test-todo-flow-chromium. Use that name in the next command (type test-results/ and press Tab to complete it):

```
playwright show-trace test-results/tests-test-04-debugging-py-test-todo-flow-chromium/trace.zip
```

   Click through the actions on the left, and switch between the Before and After tabs on the "check" step to see the item get ticked.

If a test fails because the demo site changed:

The TodoMVC tests rely on the demo site's current placeholder, test ids and counter text. The site can change after these notes were written. If one of them times out on a locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

test_console_message and test_page_error use local pages built with set_content(), so they work without the internet. If one of those fails, the cause is in the test file itself.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_04_debugging.py, line 65, change
   expect(page.get_by_test_id("todo-count")).to_have_text("1 item left")
   to
   expect(page.get_by_test_id("todo-count")).to_have_text("2 items left")
   To confirm the line number: grep -n "1 item left" tests/test_04_debugging.py
2. Run it with a trace, a screenshot and a video, kept only on failure:

```
pytest tests/test_04_debugging.py -k todo_flow --tracing retain-on-failure --screenshot only-on-failure --video retain-on-failure
```

3. The test fails after about 5 seconds: the counter says "1 item left", not "2 items left".
4. Look at what was saved, and open the trace:

```
ls test-results/*
playwright show-trace test-results/tests-test-04-debugging-py-test-todo-flow-chromium/trace.zip
```

   In the Trace Viewer, click the red step. The snapshot shows the counter with "1 item left", and the error shows the expected and the actual text. The folder also has the screenshot and the video.
5. Change line 65 back to "1 item left" and run again. It passes, and test-results/ no longer contains a trace for it.


MENTAL MODEL

- Command-line options switch on browsers, watching and evidence, without changing tests.
- Writing a test: watch it (--headed), pause it (page.pause, PWDEBUG=1), find locators (Inspector, codegen).
- A test failed: rerun it with --tracing retain-on-failure and open the trace.
- In the trace: click the red step, look at the Before snapshot, read the error and the log.
- The page's own JavaScript: console messages and page errors.
- Evidence files live in test-results/ and never go into Git.


FOR YOUR OWN APP LATER

- Make --tracing retain-on-failure part of every CI run (Module 12). A trace from a CI failure is often the only way to see what happened there.
- Run the browsers your users actually use. If most users are on Chrome and Safari, test chromium and webkit.
- When a test fails only sometimes, keep the traces of a few failures and compare them. The difference between them is usually the cause.
- Watch the Console and Errors tabs for crashes in the app's own scripts. Those are real bugs to report to the developers, with the trace attached.
- A trace contains whatever the page showed, including any real data. Only share traces from apps with test data, and only with people who are allowed to see it.


QUIZ (answers below - try before peeking)

1. A test fails on CI with a timeout, and you cannot reproduce it on your own computer. Which pytest option records what happened, and which command opens the result?

2. What is the difference between --tracing on and --tracing retain-on-failure, and which should a normal CI run use?

3. You want to step through test_todo_flow one action at a time, without editing the file. Write the full command, and say what each part does.

4. In test_console_message, why is page.set_content() inside the with page.expect_console_message() block instead of on the line before it?

5. Module 03 said to check results with expect, but test_page_screenshot uses a plain assert shot.exists(). Why is that correct here?

6. You record a session with playwright codegen --target python-pytest -o tests/test_recorded.py and leave the file there. pytest now runs it, and it passes every time. The app's Save button silently stops saving. Does the recorded test fail?

7. Where do --screenshot, --video and --tracing save their files, and why must that folder stay out of Git?

8. Write the command that runs every test in both Chromium and WebKit. How many results do you get for the 23 tests, and what must you do once before it works?

9. DevOps stretch question: a test fails on CI with --tracing retain-on-failure, but the CI machine is deleted when the job ends. How do you get the trace? (Just guess.)


ANSWERS


1. --tracing retain-on-failure records the run, and playwright show-trace test-results/<test-folder>/trace.zip opens it.

Why: a trace holds every action, a snapshot of the page before and after each one, console messages, network traffic and your test code. You can replay the CI failure on your own computer, step by step, even though it never fails there. Click the red step and look at the Before snapshot: the reason is usually visible straight away, such as a different text, a missing element or a popup covering a button.

Find the folder name with ls test-results first, or type test-results/ and press Tab. You can also open https://trace.playwright.dev and drag the zip onto it, which is how you open a trace someone else sends you.

Common mistakes:
- Choosing --screenshot only-on-failure instead. A screenshot shows only the end of the test, not the step that went wrong or why.
- Rerunning the test on your own computer until it fails. It may never fail there, and a passing rerun tells you nothing about CI.
- Giving the command with <test-folder> left in. That is a placeholder, and the terminal reports "no such file or directory".

See: TRACES, and THE TRACE VIEWER.


2. Both record every test. The difference is what is kept: on writes a trace for every test, retain-on-failure keeps the trace only for tests that failed. A normal CI run should use retain-on-failure.

Why: the recording runs the whole time, held in memory. At the end of the test, Playwright decides whether to write it to disk. With retain-on-failure, a passing test's recording is simply thrown away. That is why nothing is lost: by the time a test fails, everything that happened has already been recorded.

With on, a green run of 23 tests leaves 23 trace files, which costs time and disk space and buries the one trace you need. With retain-on-failure, a green run leaves nothing behind and a red run leaves exactly the traces of the failed tests. Use on only when you deliberately want a trace of a passing test, as in hands-on step 4.

--video retain-on-failure and --screenshot only-on-failure work the same way.

Common mistakes:
- Thinking retain-on-failure starts recording when the test fails. By then the actions have already happened, so there would be nothing to show.

See: COMMAND-LINE OPTIONS, and Trap 3.


3. PWDEBUG=1 pytest -s tests/test_04_debugging.py -k todo_flow

What each part does:
- PWDEBUG=1 opens the browser headed, opens the Inspector paused before the first action, and switches off timeouts while you look around. Written in front of the command, it applies to that one command only.
- pytest runs the tests.
- -s stops pytest capturing output, so the Inspector and any print() get through.
- tests/test_04_debugging.py limits the run to that file.
- -k todo_flow runs only tests whose name contains that text.

Then click Step over (the third button in the Inspector) once per action.

page.pause() would also work, but the question said without editing the file.

Common mistakes:
- Typing the filename as .pl instead of .py. pytest then reports "file or directory not found". Press Tab to complete filenames.
- A typo in the test name, such as tody_flow. This one is quiet: -k does not fail on a name that matches nothing, so you get "6 deselected", no tests run, and it is easy to misread as a pass (Trap 11).
- Leaving out -s, so the Inspector session is disturbed by pytest's output capture.
- Using pytest --headed --slowmo 500 instead. That only slows the test down: you can watch, but you cannot stop it or try locators.
- On Windows, using the Mac form. PowerShell needs $env:PWDEBUG = "1" on its own line first.

See: PAUSING: PWDEBUG=1, and THE PLAYWRIGHT INSPECTOR.


4. Because the message is printed the moment set_content() runs. The with block starts listening first, then runs set_content(), then waits for the message. With set_content() on the line before, the message would already have come and gone, so the block would wait for an event that never happens, and fail after the timeout.

Why: a console message is not stored anywhere. It happens once, and only something already listening receives it. The with page.expect_... pattern guarantees the order: listen, act, wait. test_page_error uses the same pattern for a script crash.

The same applies to page.on("console", ...). Register it before the page loads, or you miss everything printed during loading (Trap 5).

Common mistakes:
- Thinking it is about making sure the content can be set. set_content() works the same either way. The point is timing.
- Thinking the with block is just tidier code. The order is the whole reason.

See: CONSOLE MESSAGES AND PAGE ERRORS.


5. Because page.screenshot() only returns after the file has been written. By the time the next line runs, the file is definitely there, and a file does not change on its own afterwards, so checking once is enough.

Why: the Module 03 rule exists because the page keeps changing. Text arrives late, items appear a moment after a click, so a check that reads once can be too early. That is why expect retries. A file on disk is the opposite: it is finished, and it stays finished.

The rule:
- expect for anything on the page: text, visibility, counts, values.
- A plain assert for anything that cannot change after you read it: a file, a value already returned, a number you calculated.

In the same test file, assert message_info.value.text == "hello from the page" is the second kind: the message has already arrived.

Common mistakes:
- Concluding that plain asserts are always wrong. They are wrong for page state, and right for finished values.

See: PLAIN ASSERT ON FILES IS FINE.


6. No, it passes. That is a false negative: the test passes although the app is broken.

Why: codegen records your actions (clicks and typing), not your expectations. The recorded test clicks Save, the button is still on the page, so the click succeeds and the test ends. Nothing ever checks that anything was saved, so a broken save function cannot make it fail. The only way a recorded test fails is when a click cannot find its element.

A second problem: the file is in tests/ with a name starting with test_, so pytest collects it on every run. A test that can never fail for the right reason now sits in the suite, staying green and giving false confidence.

What to do: treat the recording as raw material. Copy the useful locators and steps into a proper test, add assertions on what the user should see (a success message, a new row, a changed value), remove repeated steps, and delete the recording or keep it outside tests/.

Common mistakes:
- Answering that the UI might change. True, but that is about maintenance. The question is whether this test can detect a broken app, and it cannot.

See: CODEGEN IN DEPTH, and Trap 6.


7. In test-results/, in the folder you run pytest from, with one subfolder per test. It stays out of Git because the files show whatever was on the page, they are large, and they change on every run.

Why, in order of importance:
- Privacy: a trace, video or screenshot shows the page exactly as it was. For a real app that can mean customer names, addresses or internal system details. The same care applies to uploading them from a public repo.
- Size: traces and videos are often several megabytes, and a fresh set is made on every run. Git keeps every version forever, so the repo would grow quickly.
- They are generated output, not source. Running the tests again recreates them.

test-results/ is already in .gitignore from Module 01. --output changes the folder. Each run clears the folder first, so copy a trace elsewhere if you want to keep it.

Common mistakes:
- Writing the folder as tests_results or tests-results. It is test-results.
- Expecting files to stay there between runs.

See: WHERE THE FILES GO, and Trap 4.


8. pytest --browser chromium --browser webkit gives 46 results, and WebKit must be installed first with playwright install webkit.

Why: --browser can be given more than once, and every test then runs once per browser: 23 tests x 2 browsers = 46. The browser appears at the end of each test name, such as test_todo_flow[chromium] and test_todo_flow[webkit], so you can see which browser failed and rerun just that one with -k webkit.

Module 01 only ran playwright install chromium, so the other browsers are not downloaded yet. Without the install, the run fails at once with "Executable doesn't exist" and a hint to run playwright install. Installing both at once: playwright install firefox webkit

Common mistakes:
- Writing --browser chromium webkit with one option. Each browser needs its own --browser.
- Expecting webkit to open the Safari app. It is Safari's engine, run by Playwright, not Safari itself.

See: COMMAND-LINE OPTIONS, Which browser, and Trap 9.


9. Upload test-results/ as a CI artifact before the job ends, then download it from the job's page afterwards.

First, what a CI machine is: when you push a commit, the CI system (for example GitHub Actions) starts a fresh virtual computer, copies your repo onto it, installs Python, the packages and the browsers, runs pytest, reports the result as a tick or a cross on your commit, and then deletes the machine. Every run starts clean, so nothing left over from a previous run can affect a test, nothing is paid for after the job, and any secrets used disappear with the machine.

So the trace is written to test-results/ on that machine, and a few seconds later the machine and the file are gone. Saving the file is not enough: it has to leave the machine before that happens.

An artifact is a file the CI system keeps after the job and attaches to the run. On GitHub Actions:

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: traces
    path: test-results/
```

if: failure() only uploads when the tests failed, so green runs store nothing. Afterwards, open that run's page on GitHub, download the zip, unpack it, and open the trace with playwright show-trace or at https://trace.playwright.dev.

In a public repo, anyone can download artifacts, so never upload traces of a real app from one.

Module 12 sets this up for real.

Common mistakes:
- Answering "save the trace to a file". It is already saved to a file. The problem is that the whole machine is deleted.
- Printing more output to the CI log instead. Logs help, but a trace shows what the page actually looked like at every step.

See: TRACES, and Module 12 for CI.


End of Module 04. Next up: Module 05, actions and input (typing, keys, clicks, hover, drag and drop, dropdowns and scrolling).