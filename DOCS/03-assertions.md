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


ANSWERS


1. What does click() wait for before it clicks, and what happens if the element never becomes ready?

Answer: click() waits until the element passes all its actionability checks: it is attached to the page, visible, stable, receives events (nothing is covering it), and enabled. Then it clicks. If those checks do not all pass within the action timeout (30 seconds by default), the click fails with an error that says which check was still failing.

What each check protects you from:
- attached and visible - clicking something that has not appeared yet
- stable - clicking a button while it is still sliding into place, so the click lands somewhere else
- receives events - clicking a button that is covered by a loading overlay or a popup, so the click would hit the overlay instead
- enabled - clicking a button that is still disabled, for example until a form is filled in

You saw this in test_click_waits_for_enabled: the Go button is disabled for one second, and click() simply waits for it.

Common wrong answers:
- "click() clicks straight away." It does not. It waits until the element is ready.
- "It waits 5 seconds." 5 seconds is the default for expect assertions. Actions wait up to 30 seconds by default.
- "If the button is disabled, click() fails immediately." It waits for it to become enabled, and only fails if that never happens within the timeout.

See: ACTIONS WAIT: ACTIONABILITY CHECKS.


2. test_reading_does_not_wait asserts that the result text is empty right after clicking Start, and it passes. What does that show?

Answer: it shows that inner_text() reads the page once, at that instant, and does not wait. "Done" only appears 1.5 seconds after the click, so at the moment of reading, the box is still empty.

Why the test exists: it makes the difference between reading and asserting visible. Compare it with the test just before it, test_expect_waits_for_text. Same page, same click, but expect(...).to_have_text("Done") keeps checking until "Done" appears, and passes.

What this means for real tests: if you wrote assert page.get_by_test_id("result").inner_text() == "Done" after the click, it would fail every time on this page, and on real pages it would fail sometimes, depending on how fast the page was. That is a flaky test.

Common wrong answers:
- "The page is broken, the result should be Done." The page is fine. It shows "Done" 1.5 seconds later, exactly as written.
- "inner_text() waits for text to appear." It waits for the element to exist, but not for any particular text. It returns whatever text is there right now, even if that is nothing.

See: READING VALUES DOES NOT WAIT.


3. Which is better, and why?
   assert page.get_by_test_id("result").inner_text() == "Done"
   expect(page.get_by_test_id("result")).to_have_text("Done")

Answer: the expect version. It retries until the text is "Done" or the timeout runs out. The plain assert reads once, immediately, and fails if the text is not there yet.

Step by step, right after an action that makes "Done" appear a moment later:
- The plain assert reads the text: it is still empty. The comparison is False. The test fails at once, and never looks again.
- expect reads the text: still empty. It waits briefly, reads again, and repeats until it sees "Done". The test passes as soon as "Done" appears.

A second advantage: when expect does fail, its error message shows the expected text, the last text it saw, and a log of its attempts. A plain assert only shows the two values at that one moment.

Common wrong answers:
- "They are the same, both check the text." They check the same thing, but at different times: once versus until true.
- "The assert is better because it is faster." It only looks faster. It fails on slower days, and a flaky test costs far more time than the fraction of a second expect might wait.
- "Add time.sleep(2) before the assert." That wastes 2 seconds every run, and on a slow day 2 seconds may still not be enough.

See: READING VALUES DOES NOT WAIT, and Trap 1.


4. A report takes 8 seconds to appear, and expect(report).to_be_visible() fails after 5 seconds. How do you fix it properly?

Answer: give this one assertion a longer timeout:

```python
expect(report).to_be_visible(timeout=15_000)
```

That allows up to 15 seconds for this step only. If the report appears after 8 seconds, the assertion passes after 8 seconds. It does not wait the full 15.

Why this is the right fix: the report is legitimately slow, so this step needs more time. Every other step keeps the normal 5-second limit, so real failures elsewhere are still reported quickly.

Common wrong answers:
- time.sleep(8) before the assertion. Wastes 8 seconds every run, and fails anyway on a day when the report takes 9.
- page.wait_for_timeout(8000). The same problem: it is a fixed pause too.
- expect.set_options(timeout=15_000) for every test. Fixes this test, but makes every other failure take 15 seconds to show up, and can hide other slow pages.
- timeout=15. Timeouts are in milliseconds, so that is 15 milliseconds. Write 15_000.

If the report regularly takes much longer than expected, that may be a performance problem worth reporting, not just a timeout to raise.

See: TIMEOUTS, Trap 4 and Trap 9.


5. An element's text is "1 item left". Does expect(locator).to_have_text("item") pass? What would you use instead?

Answer: no. to_have_text with a plain string compares the whole text of the element. "item" is not the whole text, so the assertion keeps retrying and fails after 5 seconds. To check part of the text, use to_contain_text:

```python
expect(locator).to_contain_text("item")          # passes
expect(locator).to_have_text("1 item left")       # also passes: the whole text
```

Which to choose:
- to_have_text when you know the exact text and it matters, for example the counter must say exactly "1 item left".
- to_contain_text when the element contains other text you do not care about, such as a date or a count.
- A regular expression when part of the text changes: to_have_text(re.compile(r"\d+ items? left")) passes for "1 item left" and "3 items left".

Common wrong answers:
- "Yes, it passes, because to_have_text matches part of the text." That is how get_by_text and name= work in locators (Module 02), which makes this easy to mix up. Assertions are different: to_have_text compares the whole text.

See: TEXT: WHOLE, PART, LISTS AND PATTERNS, and Trap 5.


6. How do you check that a success message has disappeared, and why not assert not message.is_visible()?

Answer: use a waiting assertion:

```python
expect(message).to_be_hidden()
# or the same thing:
expect(message).not_to_be_visible()
```

It keeps checking until the message is gone (hidden, or removed from the page), then passes. If it is still showing after the timeout, it fails.

Why not assert not message.is_visible(): is_visible() checks once, right now. Messages often stay for a few seconds or fade out slowly. If the check happens while the message is still fading, is_visible() returns True, the assert fails, and it never checks again. The test is flaky.

Common wrong answers:
- expect(message).not_to_be_attached(). Too strict if the app only hides the message instead of removing it from the page. to_be_hidden() accepts both.
- time.sleep(5), then check. Slow, and still fails if the message takes 6 seconds to go.

See: NEGATIVE ASSERTIONS, and Trap 6.


7. A teammate adds page.wait_for_timeout(3000) before an assertion "because the page is slow sometimes". What is wrong with that, and what should they do?

Answer: wait_for_timeout(3000) is a fixed 3-second pause. It waits the full 3 seconds every time, whatever the page is doing. So it is both slow and still unreliable. They should remove it and let the assertion do the waiting, raising that assertion's timeout if the page really can take longer than 5 seconds.

Why it is slow: on a normal day the page may be ready in half a second, and the pause still waits 3. Across many tests and many runs, that adds up to minutes.

Why it is still unreliable: on a really slow day the page may need 4 seconds. 3 seconds is not enough, and the test fails anyway. The pause only made the failure rarer and harder to reproduce.

What to write instead:

```python
expect(page.get_by_text("Saved")).to_be_visible()                  # waits up to 5 s, only as long as needed
expect(page.get_by_text("Saved")).to_be_visible(timeout=10_000)    # if it can really take longer
```

Common wrong answers:
- "Nothing is wrong, it is a Playwright function, so it must be fine." It exists for watching a test while debugging, not for real tests.
- "Make it 10 seconds to be safe." That makes every run 10 seconds slower and still does not guarantee anything.

See: WAITING FOR OTHER THINGS, WHY NOT TIME.SLEEP(), and Trap 3.


8. DevOps stretch question: tests pass on your Mac but sometimes time out on CI. Someone suggests setting every timeout to 60 seconds. Is that a good idea?

Answer: usually not. It may make some failures go away, but it hides the real cause and makes every genuine failure take a minute to report. First find out why CI is slower or different, then raise only the timeouts that really need it.

Why it is a bad default:
- A broken locator now fails after 60 seconds instead of 5. With several broken tests, a CI run can take many minutes longer before you learn anything.
- Real performance problems disappear: a page that got ten times slower still passes.
- The cause is often not slowness at all, but a timing bug in the test, such as a plain assert on inner_text() or count(). A longer timeout does not fix those, because they do not wait at all.

What to do instead:
- Look at which step times out, and the error message. Module 04 shows traces, which record exactly what the page looked like at each step.
- Check for reading calls used as checks (Trap 1, Trap 6) and fixed pauses (Trap 3).
- If one step is really slow on CI, raise the timeout for that step.
- CI machines are often slower and run several things at once, so a modest global increase (for example 10 seconds for expect) can be reasonable. That is a decision to make after investigating, not a first fix.

See: TIMEOUTS, Trap 4, and Module 09 for CI.


End of Module 03. Next up: Module 04, debugging (the Inspector, codegen, traces and the Trace Viewer, screenshots and videos).