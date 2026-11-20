PLAYWRIGHT WITH PYTHON - MODULE 03: ASSERTIONS AND AUTO-WAITING


GOAL

Check results reliably, without fixed pauses. Web pages are never instant: content arrives from servers, buttons become enabled, messages appear and disappear. A test has to wait for the right moment, every time, on fast and slow machines alike. Playwright does most of that waiting for you, as long as you use it the right way.

By the end of this module you can:

- explain the two kinds of waiting Playwright does
- choose the right expect assertion for text, values, counts, visibility and state
- tell which calls wait and which do not, and avoid the ones that make tests flaky
- change timeouts properly when something is legitimately slow
- explain why time.sleep() is never the answer

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tiny local pages that the tests build themselves with page.set_content().


THE TWO KINDS OF WAITING

1. Actions wait before they act. click(), fill(), check() and the other actions first wait until the element is ready for that action, then act.
2. Assertions retry until they pass. expect(...).to_have_text("Done") checks, and if the text is not "Done" yet, checks again and again until it is, or until the timeout runs out.

Together they cover almost every timing problem. You do not write any waiting code yourself.

A flaky test is one that sometimes passes and sometimes fails, without any change to the app or the test. Most flaky tests are timing problems: the test checked too early. Both kinds of waiting exist to prevent exactly that.


ACTIONS WAIT: ACTIONABILITY CHECKS

Before an action, Playwright checks that the element is ready for it. It keeps checking until every check passes, then acts. The checks depend on the action:

- click(): the element is attached to the page, visible, stable (not moving, for example in the middle of an animation), receives events (not covered by another element, such as a popup or a loading overlay), and enabled
- fill(): visible, enabled, and editable (not read-only)
- check() and uncheck(): visible, stable, receives events, enabled
- hover(): visible, stable, receives events

What the checks mean:

- attached - the element exists on the page
- visible - it has a size, and is not hidden with CSS
- stable - it has stayed in the same place for a moment, so the click lands where it should
- receives events - a click at that spot would really reach this element, not something on top of it
- enabled - it is not disabled (a disabled button cannot be clicked)
- editable - a field that accepts typing

If the checks do not pass within the action timeout (30 seconds by default), the action fails. The error says which check was still failing, for example "element is not enabled" or "element is outside of the viewport", or that another element "intercepts pointer events" (something is covering it).

Example from the test file: test_click_waits_for_enabled loads a page where the Go button is disabled for one second. click() simply waits until the button becomes enabled, then clicks. No waiting code is needed.


ASSERTIONS RETRY: WEB-FIRST ASSERTIONS

expect() assertions are called web-first assertions, because they are made for pages that change over time:

```python
expect(page.get_by_test_id("result")).to_have_text("Done")
```

What happens:

1. Playwright finds the element and reads its text.
2. If the text is "Done", the assertion passes at once.
3. If not, it waits a short moment and tries again, from step 1.
4. If the timeout (5 seconds by default) runs out first, the assertion fails, and the error shows the expected value, the last value it actually saw, and a log of the attempts.

It waits only as long as needed: if the text arrives after 0.2 seconds, the assertion passes after 0.2 seconds.

Because the locator is searched again on every attempt (Module 02, locators are lazy), the assertion also works when the page redraws the element while it waits.


ASSERTIONS YOU WILL USE MOST

On the page:

```python
expect(page).to_have_title("Exact title")
expect(page).to_have_title(re.compile("TodoMVC"))
expect(page).to_have_url("https://example.com/done")
expect(page).to_have_url(re.compile("/done"))
```

On an element (a locator):

```python
expect(locator).to_be_visible()             # shown on the page
expect(locator).to_be_hidden()              # not shown, or not on the page at all
expect(locator).to_be_attached()            # on the page, visible or not
expect(locator).to_have_text("buy milk")    # the whole text
expect(locator).to_contain_text("milk")     # part of the text
expect(locator).to_have_value("draft")      # what is typed in a field
expect(locator).to_be_empty()               # an empty field, or an element with no text
expect(locator).to_be_checked()             # a ticked checkbox or radio
expect(locator).to_be_enabled()             # can be used
expect(locator).to_be_disabled()            # greyed out, cannot be used
expect(locator).to_be_editable()            # a field you can type in
expect(locator).to_be_focused()             # has the keyboard focus
expect(locator).to_have_count(3)            # how many elements match
expect(locator).to_have_attribute("href", "/help")
expect(locator).to_have_class(re.compile("completed"))
```

Every assertion can also be negated with not_ (next section).


NEGATIVE ASSERTIONS

To check that something is not true, put not_ in front:

```python
expect(checkbox).not_to_be_checked()
expect(message).not_to_be_visible()
expect(title).not_to_have_text("old name")
```

Negative assertions retry too: not_to_be_visible() keeps checking until the element is gone, then passes. That is exactly what you want after closing a dialog or after a message should disappear.

to_be_hidden() and not_to_be_visible() mean the same thing. Both pass when the element is hidden or not on the page at all.


TEXT: WHOLE, PART, LISTS AND PATTERNS

- to_have_text("buy milk") checks the whole text of the element. Extra spaces and line breaks are tidied up before comparing.
- to_contain_text("milk") checks that the text contains this part.
- Both accept a regular expression: to_have_text(re.compile(r"\d+ items? left"))
- ignore_case=True ignores upper and lower case: to_have_text("Buy Milk", ignore_case=True)

When the locator matches several elements, pass a list. Each element is compared with the item at the same position, and the number of elements must match too:

```python
expect(page.get_by_test_id("todo-title")).to_have_text(["buy milk", "walk the dog"])
```

Which one to choose: to_have_text when you know the full text and it matters, to_contain_text when the element also has other text you do not care about, such as a count or a date.


READING VALUES DOES NOT WAIT

Some calls read the page once, immediately, and return what they find. They never wait and never retry:

```python
locator.inner_text()       # the text right now
locator.input_value()      # the field's value right now
locator.count()            # how many match right now
locator.is_visible()       # visible right now? True or False
locator.is_checked()       # ticked right now?
locator.is_enabled()       # enabled right now?
page.title()               # the title right now
```

These are fine for reading a value you need, for example to print it or use it later in the test. They are not safe for checking a result, because the result may not be there yet:

```python
assert locator.inner_text() == "Done"          # checks once, may be too early
expect(locator).to_have_text("Done")            # retries until true or timeout
```

Matching pairs, the reading call and the assertion to use instead:

- inner_text() == ... -> expect(locator).to_have_text(...)
- input_value() == ... -> expect(locator).to_have_value(...)
- count() == ... -> expect(locator).to_have_count(...)
- is_visible() -> expect(locator).to_be_visible()
- not is_visible() -> expect(locator).to_be_hidden()
- is_checked() -> expect(locator).to_be_checked()
- page.title() == ... -> expect(page).to_have_title(...)
- page.url == ... -> expect(page).to_have_url(...)

test_reading_does_not_wait proves this: right after clicking Start, inner_text() returns an empty text, because "Done" only appears 1.5 seconds later. The plain assert reads too early. In the next test, expect waits and sees "Done".


TIMEOUTS

Defaults:

- expect assertions: 5 seconds
- actions (click, fill...) and navigation (goto): 30 seconds

When something is legitimately slow, for example a report that takes 8 seconds to generate, give that one step more time:

```python
expect(report).to_be_visible(timeout=15_000)       # milliseconds: 15 seconds
page.get_by_role("button", name="Export").click(timeout=60_000)
```

The underscore in 15_000 is just a separator that makes big numbers easier to read. 15_000 is the same as 15000.

To change the defaults for a whole test or test run:

```python
expect.set_options(timeout=10_000)       # all expect assertions
page.set_default_timeout(10_000)          # all actions on this page
```

Module 05 shows where to put settings like these so they apply to every test.

Raise a timeout for the one step that needs it. Raising every timeout makes real failures take much longer to show up, and can hide performance problems.


CUSTOM FAILURE MESSAGES

A second argument to expect adds your own message to the failure output:

```python
expect(page.get_by_test_id("todo-count"), "the counter should update after adding an item").to_have_text("1 item left")
```

Useful when the reason behind the check is not obvious from the locator.


WAITING FOR OTHER THINGS

Most of the time, actions and expect are all you need. A few other waits exist for special cases:

```python
page.wait_for_url(re.compile("/dashboard"))        # until the URL matches
page.wait_for_load_state("networkidle")            # until network traffic stops (use sparingly)
locator.wait_for(state="visible")                  # until visible, without asserting anything
```

And one to avoid:

```python
page.wait_for_timeout(3000)          # a fixed 3-second pause
```

wait_for_timeout is a fixed pause, like time.sleep (next section). It is meant for watching a test while debugging, not for real tests.

Waiting for a network response, such as an API call finishing, is covered in Module 07.


WHY NOT TIME.SLEEP()

time.sleep(3) stops the test for exactly 3 seconds, whatever the page is doing.

- If the page was ready after 0.2 seconds, 2.8 seconds are wasted. Across hundreds of steps, that is minutes per run.
- If the page needs 4 seconds today (a slow network, a busy CI machine), 3 seconds is not enough, and the test fails anyway.

So a fixed pause is both slow and still flaky. A condition-based wait (an action or an expect) moves on the moment the page is ready and keeps waiting while it is not, up to the timeout.

The rule: wait for a condition, not for time.


LOCAL TEST PAGES WITH SET_CONTENT

page.set_content(html) loads a page from a piece of HTML written in the test, instead of from a website. The tests use it to show waiting on purpose, without depending on any site.

```python
DELAYED_PAGE = """
<button>Start</button>
<div data-testid="result"></div>
<script>
  document.querySelector("button").onclick = () => {
    setTimeout(() => {
      document.querySelector("[data-testid=result]").textContent = "Done";
    }, DELAY);
  };
</script>
"""
```

- The page has a Start button and an empty result box.
- The script says: when Start is clicked, wait DELAY milliseconds, then write "Done" in the box. setTimeout is the browser's way of running something later.
- open_delayed_page(page, 1500) replaces the word DELAY with 1500, so "Done" appears 1.5 seconds after the click.

DISABLED_BUTTON_PAGE works the same way: the Go button starts disabled, becomes enabled after 1 second, and writes "Clicked" when clicked.

This is also a handy technique of its own: when you want to try out an assertion or a locator, a few lines of HTML in set_content are often quicker than finding a real page that behaves the right way.


THE FILES

- FILES/test_03_assertions.py - 8 tests

Helpers (not tests, because their names do not start with test_):

open_delayed_page(page, delay_ms)
  Loads the delayed page with the given delay.

add_todo(page, text)
  Opens the TodoMVC demo and adds one item.

The tests:

test_page_title_and_url
  Page-level assertions: the title contains "TodoMVC" and the URL contains "todomvc". Regular expressions keep both checks tolerant of small changes.

test_text_assertions
  Adds "buy milk", then checks the item's whole text (to_have_text), part of it (to_contain_text), and the counter text "1 item left".

test_value_and_checked
  Types "draft" and checks the field's value, presses Enter and checks the field is empty again (the app clears it), then checks the new item's checkbox is not ticked, ticks it, and checks it is ticked.

test_negative_assertions
  Adds an item, ticks it, clicks "Clear completed", then checks there are no items left and the "Clear completed" button has gone.

test_expect_waits_for_text
  Clicks Start on the delayed page. "Done" appears 1.5 seconds later, and expect waits for it. Passes in about 1.5 seconds.

test_reading_does_not_wait
  The same page, but reads the text with inner_text() straight after the click. It is still empty, which proves reading calls do not wait.

test_click_waits_for_enabled
  The Go button is disabled for 1 second. click() waits until it is enabled, then clicks.

test_custom_timeout
  "Done" appears after 6 seconds, longer than the 5-second default. timeout=10_000 gives this one assertion 10 seconds, so it passes.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - A plain assert on a value you just read.
assert locator.inner_text() == "Done" reads once, immediately. If the page is a moment late, the test fails although the app works. Use the matching expect assertion.

Trap 2 - Forgetting the expect.
locator.to_have_text("Done") is an error: to_have_text belongs to expect, not to the locator. Write expect(locator).to_have_text("Done").

Trap 3 - Fixed pauses.
time.sleep() and page.wait_for_timeout() are slow and still flaky. Wait for a condition instead.

Trap 4 - Raising every timeout.
expect.set_options(timeout=60_000) "to be safe" makes every real failure take a minute to report and can hide slow pages. Raise the timeout only for the step that needs it.

Trap 5 - to_have_text when you meant to_contain_text.
to_have_text("milk") fails on an element whose text is "buy milk", because it compares the whole text. Use to_contain_text for part of the text.

Trap 6 - Checking that something is gone with is_visible().
assert not locator.is_visible() checks once. If the message is still fading out, it fails. Use expect(locator).to_be_hidden(), which waits until it has gone.

Trap 7 - Asserting too little.
A test that clicks Save and then only checks that the button exists proves almost nothing. Assert on the result a user would see: the success message, the new row, the changed value.

Trap 8 - Waiting for "networkidle" by default.
wait_for_load_state("networkidle") waits until there has been no network traffic for a moment. Pages that poll the server or stream data never get there, so the wait runs into its timeout. Prefer waiting for the element or result you actually need.

Trap 9 - Milliseconds, not seconds.
timeout=10 means 10 milliseconds, not 10 seconds. Write timeout=10_000 for 10 seconds.


HANDS-ON PRACTICE

1. Run the Module 03 tests:

```
pytest FILES/test_03_assertions.py -v
```

   Expect 8 passed. The run takes noticeably longer than Module 02, mostly because test_custom_timeout really waits about 6 seconds for "Done". A plain "pytest" now runs 17 tests: 2 from Module 01, 7 from Module 02 and 8 from Module 03.

2. Watch the waiting tests:

```
pytest FILES/test_03_assertions.py --headed -k "waits or timeout"
```

   You see the Start button clicked, an empty page for a moment, then "Done" appear, and the test finishing right after. -k with "or" runs every test whose name contains either word.

3. See how long each test took:

```
pytest FILES/test_03_assertions.py --durations=0
```

   --durations=0 lists every test with its time, slowest first. test_custom_timeout takes about 6 seconds, test_expect_waits_for_text about 1.5 seconds. That shows expect waits only as long as needed.

If a test fails because the demo site changed:

The four TodoMVC tests rely on the demo site's current title, placeholder, test ids and button names. The site can change after these notes were written. If one of them times out on a locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

The four waiting tests use local pages built with set_content(), so they work without the internet and do not depend on any site. If one of those fails, the cause is in the test file itself, for example a missing or changed line.

Break it on purpose (this step is MEANT to fail):

1. In FILES/test_03_assertions.py, line 112, change
   expect(page.get_by_test_id("result")).to_have_text("Done", timeout=10_000)
   to
   expect(page.get_by_test_id("result")).to_have_text("Done")
   To confirm the line number: grep -n "timeout=10_000" FILES/test_03_assertions.py
2. Run:

```
pytest FILES/test_03_assertions.py -v -k custom_timeout
```

3. The test fails after about 5 seconds. "Done" would have appeared at 6 seconds, but the default timeout gave up first. Read the error: it shows the expected text "Done", the actual value (empty), and that it timed out after 5000 ms.
4. Change line 112 back and run again. It passes after about 6 seconds.


MENTAL MODEL

- Actions wait until the element is ready, then act.
- expect retries until the condition is true, or the timeout runs out.
- Reading calls (inner_text, count, is_visible...) never wait: use them to read, not to check.
- Need more time? Raise the timeout for that one step.
- Never a fixed pause. Wait for a condition, not for time.


FOR YOUR OWN APP LATER

- Slow operations such as reports, exports and searches over large data are the usual places that need a longer timeout. Give that step its own timeout and leave the defaults alone.
- After saving, assert on what the user sees: the confirmation message, the updated row, the new value in the field.
- Loading spinners: wait for the result, or use expect(spinner).to_be_hidden() before checking the result. Do not wait a fixed time for the spinner to go.
- If a test is flaky, look for a plain assert on a value read with inner_text(), count() or is_visible(), or for a fixed pause. Those are the usual causes.


QUIZ (answers below - try before peeking)

1. What does click() wait for before it clicks, and what happens if the element never becomes ready?

2. test_reading_does_not_wait asserts that the result text is empty right after clicking Start, and it passes. What does that show?

3. Which is better, and why?
   assert page.get_by_test_id("result").inner_text() == "Done"
   expect(page.get_by_test_id("result")).to_have_text("Done")

4. A report takes 8 seconds to appear, and expect(report).to_be_visible() fails after 5 seconds. How do you fix it properly?

5. An element's text is "1 item left". Does expect(locator).to_have_text("item") pass? What would you use instead?

6. How do you check that a success message has disappeared, and why not assert not message.is_visible()?

7. A teammate adds page.wait_for_timeout(3000) before an assertion "because the page is slow sometimes". What is wrong with that, and what should they do?

8. DevOps stretch question: tests pass on your Mac but sometimes time out on CI. Someone suggests setting every timeout to 60 seconds. Is that a good idea? (Just guess.)


FALSE POSITIVES AND FALSE NEGATIVES

A test's job is to detect problems, so a failing test means "a problem was detected". Two things can go wrong:

- False positive (a false alarm): the test fails, but the app works. Example: the test checked the text before the page had finished updating.
- False negative (a missed bug): the test passes, but the app is broken. Example: a test clicks Save and only checks that the Save button exists, so it passes even when saving does nothing.

Timing mistakes cause false positives: reading a value once (inner_text(), count(), is_visible()), fixed pauses, or a timeout that is too short for a slow step. Waiting assertions (expect) prevent them.

Weak assertions cause false negatives: checking something that would be true whether or not the feature works. Assert on the result a user would see.


QUIZ (answers below - try before peeking)

1. click() is called on a button that will not be ready for a while. What does click() wait for, and what happens if the button is still not ready after 30 seconds?

2. In test_reading_does_not_wait, line 99 is: assert page.get_by_test_id("result").inner_text() == "". What does inner_text() return at that moment, and why does the test pass?

3. Which line should you use to check the result, and why?
   assert page.get_by_test_id("result").inner_text() == "Done"
   expect(page.get_by_test_id("result")).to_have_text("Done")

4. A report takes 8 seconds to appear, and expect(report).to_be_visible() fails after 5 seconds. Write the fixed line.

5. An element's text is "1 item left". Does expect(locator).to_have_text("item") pass? If not, what do you use instead?

6. How do you check that a success message has disappeared, and why is assert not message.is_visible() a bad way to do it?

7. A teammate adds page.wait_for_timeout(3000) before an assertion "because the page is slow sometimes". What is wrong with that, and what should they write instead?

8. DevOps stretch question: tests pass on your Mac but sometimes time out on CI. Someone suggests setting every timeout to 60 seconds. Why is that a poor first fix, and what should you do instead? (Just guess.)


ANSWERS


1. click() waits until the button is attached, visible, stable, not covered by anything, and enabled, then clicks. If it is still not ready after 30 seconds, click() fails with an error that names the check that was still failing.

Why: these are the actionability checks. Playwright repeats them until all pass, so a slow page is simply waited for. In test_click_waits_for_enabled (line 104), the Go button is disabled for 1 second, and click() waits for it with no extra code.

The error tells you where to look:
- "element is not visible" - it never appeared, or is hidden
- "element is not enabled" - it stayed disabled
- "... intercepts pointer events" - something is covering it, such as an overlay or a popup

If the page is legitimately slower than 30 seconds, the failure is a false positive (the app works, but time ran out). Give that one step more time: click(timeout=60_000).

Common mistakes:
- Thinking click() fails straight away on a slow page. It waits up to the timeout.
- Mixing up the defaults: actions wait up to 30 seconds, expect assertions 5 seconds.

See: ACTIONS WAIT: ACTIONABILITY CHECKS, and FALSE POSITIVES AND FALSE NEGATIVES.


2. inner_text() returns an empty text (""), because it reads the result box once, immediately after the click, and "Done" only appears 1.5 seconds later. The test passes because the box really is empty at that moment.

Why: inner_text() does not wait for any particular text. It returns whatever the element contains right now. The test exists to prove that. The test before it, test_expect_waits_for_text (line 92), uses the same page and the same click, but expect(...).to_have_text("Done") keeps checking until "Done" appears.

The lesson: read with inner_text(), check with expect. If you checked for "Done" with inner_text(), the test would always fail on this page, and fail only sometimes on a real app (a flaky test).

Common mistakes:
- Reading the test as "you should use inner_text()". It shows the opposite: inner_text() is too early for checking a result.
- Thinking the page is broken because the text is empty. The page shows "Done" 1.5 seconds later, as written.

See: READING VALUES DOES NOT WAIT.


3. The expect line. It retries until the text is "Done" (or 5 seconds pass), while the assert reads once, immediately, and fails if "Done" has not appeared yet.

Why: right after the click, the box is still empty.
- assert ... inner_text() == "Done" reads "" once, the comparison is False, and the test fails. It never looks again. That is a false positive: the app works, the test checked too early.
- expect(...).to_have_text("Done") reads "", waits a moment, reads again, and repeats until it sees "Done". It passes as soon as "Done" appears.

expect also gives a better error when it fails: the expected text, the last text it saw, and a log of its attempts.

The same rule applies to every reading call: count() -> to_have_count, is_visible() -> to_be_visible, input_value() -> to_have_value.

Common mistakes:
- "Both check the same thing." They check the same value, but at different times: once versus until true.
- Adding time.sleep() before the assert. It is slower, and can still be too short.

See: READING VALUES DOES NOT WAIT, and Trap 1.


4. expect(report).to_be_visible(timeout=15_000)

Why: timeout= gives this one assertion more time. It still moves on as soon as the report appears: if it shows up after 8 seconds, the assertion passes after 8 seconds, not 15. Every other assertion keeps the 5-second default, so real failures elsewhere are still reported quickly.

This is the same technique as test_custom_timeout, line 112: to_have_text("Done", timeout=10_000).

Pick a number comfortably above the normal time, such as 15 seconds for an 8-second report. A huge value like 120 seconds would hide a report that has become much slower.

Common mistakes:
- Naming the test (test_custom_timeout) instead of the setting it uses. What you copy is timeout=.
- timeout=15. Timeouts are in milliseconds, so that is 15 milliseconds. Write 15_000.
- time.sleep(8) or wait_for_timeout(8000). Fixed pauses: slower, and they fail on a day the report takes 9 seconds.
- expect.set_options(timeout=15_000) for all tests. Makes every other failure slower to report.

See: TIMEOUTS, Trap 4 and Trap 9.


5. No. to_have_text compares the whole text, and "item" is not the whole of "1 item left". Use expect(locator).to_contain_text("item").

Why: to_have_text("item") keeps retrying for 5 seconds, never sees exactly "item", and fails. to_contain_text checks for part of the text, so it passes.

Which to use:
- to_have_text("1 item left") - when the exact text matters
- to_contain_text("item") - when the element also contains text you do not care about
- to_have_text(re.compile(r"\d+ items? left")) - when part of the text changes, such as the number

Common mistakes:
- Expecting to_have_text to match part of the text, because locators do. get_by_text("item") and name="item" match part of the text (Module 02), but the to_have_text assertion compares the whole.

See: TEXT: WHOLE, PART, LISTS AND PATTERNS, and Trap 5.


6. Use expect(message).to_be_hidden(). It keeps checking until the message is hidden or removed, while is_visible() checks only once and fails if the message is still showing at that instant.

Why: success messages usually stay for a few seconds or fade out slowly. assert not message.is_visible() reads once. If the message is still on screen, is_visible() returns True, the assert fails, and it never checks again. That is a false positive. to_be_hidden() waits until the message is gone, up to 5 seconds.

expect(message).not_to_be_visible() means exactly the same as to_be_hidden().

Common mistakes:
- Answering only "check that it is hidden" without the reason. The reason is the point: is_visible() reads once, expect retries.
- expect(message).not_to_be_attached(). Too strict if the app only hides the message instead of removing it.

See: NEGATIVE ASSERTIONS, and Trap 6.


7. A fixed pause always waits the full 3 seconds, so it is slow on normal days and still too short on slow days. Remove it and let the assertion wait, for example expect(page.get_by_text("Saved")).to_be_visible().

Why:
- Slow: if the page is ready after 0.3 seconds, the test still waits 3. Across many tests, that is minutes per run.
- Unreliable: if the page needs 4 seconds, 3 is not enough, and the test fails anyway. The pause only makes failures rarer and harder to reproduce.

The assertion moves on the moment the result appears. If the page can really take longer than 5 seconds, give that assertion more time: to_be_visible(timeout=10_000).

Any expect assertion does the waiting. Use the one that matches what you are checking: to_be_visible for an element appearing, to_have_text for a text.

Common mistakes:
- Making the pause longer "to be safe". Every run gets slower, and it still guarantees nothing.
- Thinking a Playwright function must be fine for tests. wait_for_timeout exists for watching a test while debugging.

See: WHY NOT TIME.SLEEP(), and Trap 3.


8. Because it hides the cause and makes every real failure take a minute to report. Instead, find which step times out and why, fix it, and raise the timeout only for a step that is really slow.

Why it is a poor first fix:
- A broken locator now fails after 60 seconds instead of 5. With a few broken tests, a run takes minutes longer before you learn anything.
- Pages that have become much slower still pass, so performance problems go unnoticed.
- The usual cause of "sometimes times out on CI" is a timing bug in the test: a reading call used as a check, or a fixed pause. Those read once and ignore the timeout, so a bigger timeout does not fix them.

What to do:
1. Read the error: which step timed out, and on which locator. Traces (Module 04) record what the page looked like at every step, even on CI.
2. Replace reading calls used as checks with expect, and remove fixed pauses.
3. If one step really is slow on CI, raise the timeout for that step only.
4. CI machines are often slower than a laptop, so a modest global increase (for example 10 seconds for expect) can be reasonable, after investigating.

Common mistakes:
- Answering only "no". The useful part is why, and what to do instead.

See: TIMEOUTS, Trap 4, and Module 09 for CI.


End of Module 03. Next up: Module 04, debugging (the Inspector, codegen, traces and the Trace Viewer, screenshots and videos).


