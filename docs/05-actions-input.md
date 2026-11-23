PLAYWRIGHT WITH PYTHON - MODULE 05: ACTIONS AND INPUT


GOAL

Do everything a user does on a page: type, press keys, click in every way, hover, tick boxes, choose from dropdowns, drag things and scroll. Module 02 found elements. This module is about what you do with them once you have found them.

By the end of this module you can:

- choose between fill and press_sequentially, and know why fill is usually right
- press keys and keyboard shortcuts, including ones that work on both Mac and Windows
- use every kind of click: double, right, with modifier keys, at a position, and force
- tick checkboxes and radio buttons safely with check and uncheck
- use select dropdowns, including multiple choice
- drag and drop, hover, and scroll
- work out why a click seems to do nothing

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tiny local pages built with page.set_content().


EVERY ACTION WAITS FIRST

Before doing anything, Playwright checks the element is ready for that action, and keeps checking until it is or the timeout runs out (Module 03). For a click that means: attached to the page, visible, stable (not moving), receiving events (not covered by something else) and enabled.

So you never write waiting code around an action. If an action times out, the error says which check failed, for example "element is not enabled" or "intercepts pointer events".

Each action also takes a timeout of its own, in milliseconds:

```python
page.get_by_role("button", name="Export").click(timeout=60_000)
```


TYPING: FILL

fill is the normal way to put text in a field:

```python
page.get_by_label("Name").fill("new text")
page.get_by_label("Name").fill("")          # the same as clear()
page.get_by_label("Name").clear()
```

What fill does: it focuses the field, clears whatever was there, sets the new value in one step, and fires an input event so the page notices the change.

It replaces the contents. There is no need to clear the field first.

fill only works on fields a user could type in: inputs, textareas, and elements marked contenteditable. On anything else it fails with a clear error.


TYPING: PRESS_SEQUENTIALLY

press_sequentially types one character at a time, as a real keyboard would:

```python
page.get_by_label("Search").press_sequentially("playwright")
page.get_by_label("Search").press_sequentially("playwright", delay=100)
```

Each character fires keydown, keypress and keyup events. delay waits that many milliseconds between characters.

Use it only when the page reacts to individual keystrokes, for example:

- a search box that shows suggestions as you type
- a field that formats as you type, such as a phone number or a card number
- a character counter
- a field that only enables the Save button after a keystroke event

For everything else, fill is better: it is much faster, and it does not depend on the page keeping up with each keystroke.

Note that press_sequentially does not clear the field first. Call clear() before it if the field has something in it.


KEYS

```python
locator.press("Enter")
locator.press("Escape")
locator.press("Tab")
locator.press("ArrowDown")
locator.press("Backspace")
locator.press("a")
page.keyboard.press("Enter")          # to whatever has focus, not a specific element
```

Key names are the browser's own names: Enter, Escape, Tab, Backspace, Delete, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, End, PageUp, PageDown, F1 to F12, and single characters such as a or 1.

Shortcuts use + between the keys:

```python
locator.press("Control+a")            # Windows and Linux: select all
locator.press("Meta+a")               # Mac: Meta is the Command key
locator.press("ControlOrMeta+a")      # Control on Windows and Linux, Command on Mac
locator.press("Shift+Tab")
locator.press("Control+Shift+K")
```

ControlOrMeta is the one to use for anything that is Ctrl on Windows and Cmd on Mac. Without it, the same test fails on the other operating system, and on CI.

Modifier names: Control, Meta (Command on Mac, the Windows key on Windows), Shift, Alt (Option on Mac), and ControlOrMeta.

To type whole text through the keyboard, rather than a single key, use press_sequentially or page.keyboard.type("text").


CLICKS

```python
locator.click()                                   # left click
locator.dblclick()                                # double click
locator.click(button="right")                     # right click
locator.click(button="middle")                    # middle click
locator.click(click_count=3)                      # triple click, often selects a line
locator.click(modifiers=["Shift"])                # shift-click
locator.click(modifiers=["ControlOrMeta"])        # ctrl/cmd-click
locator.click(position={"x": 10, "y": 10})        # at a point inside the element
locator.click(force=True)                         # skip the actionability checks
locator.click(no_wait_after=True)                 # do not wait for navigation to settle
```

- A right click usually opens the browser's own context menu. Playwright cannot interact with that menu, because it is part of the operating system, not the page. Pages with their own custom menu built in HTML are fine.
- position is measured from the top left corner of the element. Useful for canvases, maps and sliders.
- force=True skips the checks that make clicks safe. See the trap below before using it.

Scrolling happens automatically: if the element is further down the page, Playwright scrolls it into view before clicking.


HOVER

```python
locator.hover()
```

hover moves the mouse over the element, which is how you open menus that appear on hover, or tooltips. After hovering, the menu item you want is usually a separate locator:

```python
page.get_by_role("button", name="Account").hover()
page.get_by_role("menuitem", name="Settings").click()
```

A hover menu that closes as soon as the mouse moves away can be awkward. If the menu disappears before the click, check whether the app also opens it on click, which is more reliable to test.


CHECKBOXES AND RADIO BUTTONS

```python
locator.check()        # make sure it ends up ticked
locator.uncheck()      # make sure it ends up unticked
locator.set_checked(True)
```

check() and uncheck() look at the current state first. check() on a box that is already ticked does nothing, so the box always ends up ticked.

click() toggles instead. On a box that is already ticked, click() unticks it. That is why check() is safer: the result does not depend on how the test started.

Radio buttons work the same way with check(). Choosing one in a group automatically unselects the others, so there is no uncheck() for radios.

Playwright checks afterwards that the element really is ticked, and fails if it is not, for example because the page ignored the click.


SELECT DROPDOWNS

For real HTML select elements:

```python
size.select_option("m")                       # by value attribute
size.select_option(label="Large")             # by the text the user sees
size.select_option(index=2)                   # by position, counting from 0
size.select_option(["cheese", "olives"])      # several, for a multiple select
size.select_option([])                        # clear the selection
```

select_option returns the list of values it selected, and fires the input and change events the page expects.

Checking the result:

```python
expect(size).to_have_value("l")                             # single select
expect(toppings).to_have_values(["cheese", "olives"])       # multiple select
```

Many modern apps do not use a real select. They build a dropdown out of div elements that only looks like one. select_option fails on those with an error saying the element is not a select. Handle them as normal elements instead: click to open, then click the option.

```python
page.get_by_role("combobox", name="Country").click()
page.get_by_role("option", name="Germany").click()
```

To tell which kind you have: right-click the dropdown in the browser, choose Inspect, and look at the tag. If it is select, use select_option.


DRAG AND DROP

The simple way, when both elements exist on the page:

```python
page.get_by_text("Item 1").drag_to(page.get_by_test_id("drop-zone"))
```

The manual way, for pages that need the mouse to move in steps, such as sliders or canvases:

```python
source = page.get_by_text("Item 1")
target = page.get_by_test_id("drop-zone")
source.hover()
page.mouse.down()
target.hover()
target.hover()          # some pages need a second move before they react
page.mouse.up()
```

page.mouse works in page coordinates, not on elements, so hover() is used to move to the right place first.

Drag and drop is one of the most fragile things to automate, because every library implements it differently. If drag_to does not work, the manual version with extra hover steps usually does.


SCROLLING

Clicks scroll automatically, so you rarely need these:

```python
locator.scroll_into_view_if_needed()
page.mouse.wheel(0, 500)                  # scroll down 500 pixels
page.keyboard.press("End")                # jump to the bottom
```

scroll_into_view_if_needed is useful when you want a screenshot of something further down, or when checking that an element becomes visible only after scrolling (lazy loading).


OTHER USEFUL ACTIONS

```python
locator.focus()
locator.blur()
locator.tap()                            # a touch tap, needs a touch-enabled context (Module 07)
page.get_by_label("CV").set_input_files("cv.pdf")     # file upload, Module 06
```


WHEN A CLICK SEEMS TO DO NOTHING

Work through these in order:

1. Read the error. "intercepts pointer events" means something is covering the element. The error names what. Usually a cookie banner, a modal dialog, a loading overlay or a sticky header.
2. If there is no error at all and the page just did not react, the click probably landed on the wrong element: a wrapper div rather than the button inside it. Try the inner element, or add a position.
3. Check the element is the one a user clicks. Some apps put the click handler on a child element.
4. Deal with whatever is in the way: close the cookie banner first, as a real user would.
5. Only then consider force=True, and read the trap below.
6. If it still fails, record a trace (Module 04) and look at the Before snapshot of the failing step.


WHAT FORCE=TRUE REALLY DOES

force=True skips the actionability checks and clicks at the element's position anyway. It does not make a hidden element visible or a disabled button work. It just removes the safety net.

That is why it is dangerous: the test can now pass while clicking something the user could never click, or while a dialog is covering the page. The bug you were testing for disappears from view.

Legitimate uses are rare: an element the browser believes is hidden but is actually usable, or a known problem in a third-party widget. In those cases, add a comment saying why.

If the real reason is "something is in the way", close that thing instead. If it is "the element is disabled", the test has found a real difference from what you expected.


THE FILES

- tests/test_05_actions_input.py - 14 tests

FORM_PAGE, CLICK_PAGE and LONG_PAGE are small HTML pages written in the test file and loaded with page.set_content(). They have a text field, two dropdowns, a checkbox, two radio buttons, a button that records how it was clicked, and a very tall page with a button at the bottom. Using local pages means these tests never break because someone else's site changed.

open_todos(page, *items)
  A helper that opens the TodoMVC demo and adds the given items.

test_fill_replaces_existing_text
  The field starts with "old text". fill("new text") replaces it, with no clear() first.

test_clear_empties_a_field
  clear() empties the field.

test_press_sequentially_fires_key_events
  The page records every keyup event. Typing "abc" one character at a time produces "a b c", which shows the page saw three separate keystrokes.

test_press_enter_submits
  Typing in the TodoMVC box and pressing Enter adds the item.

test_escape_cancels_edit
  Double-clicking an item opens it for editing. Typing something else and pressing Escape cancels, so the original text stays.

test_keyboard_shortcut_selects_all
  ControlOrMeta+a selects everything in the field, then Backspace deletes it. The same test works on Mac and on Windows.

test_double_click, test_right_click, test_hover
  The page writes "double", "right" or "hovered" depending on how the button was used.

test_click_scrolls_into_view
  The button is 3000 pixels down the page. click() scrolls to it automatically.

test_check_and_uncheck
  Ticks the box, ticks it again (which does nothing), then unticks it.

test_radio_buttons
  Choosing Pro leaves Free unselected.

test_select_option
  Chooses by value, then by visible label.

test_select_multiple_options
  Chooses two options in a multiple select, and checks both with to_have_values.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - press_sequentially everywhere.
It is much slower than fill, because every character is a separate keystroke with its own events. A long form becomes noticeably slow. Use fill unless the page reacts to individual keystrokes.

Trap 2 - press_sequentially on a field that already has text.
Unlike fill, it does not clear first, so the new text is added to the old. Call clear() first.

Trap 3 - click() on a checkbox.
click() toggles. On a box that is already ticked, it unticks it, so the result depends on the starting state. check() and uncheck() always end in the state you asked for.

Trap 4 - Control+a on a Mac.
On a Mac that is not select all, so the test fails there while passing on Windows, or the other way round. Use ControlOrMeta+a.

Trap 5 - force=True to make a failure go away.
It skips the checks that make a click meaningful, so the test can pass while clicking something no user could click. Find out what is in the way instead.

Trap 6 - select_option on a dropdown that is not a select.
Custom dropdowns built from div elements fail with an error about the element not being a select. Click to open, then click the option.

Trap 7 - Expecting to interact with the browser's context menu.
A right click opens the operating system's menu, which Playwright cannot touch. Only menus drawn by the page itself can be tested.

Trap 8 - Adding scrolling code before a click.
Clicks already scroll the element into view. Extra scrolling just makes the test longer and can even move the element away again.

Trap 9 - Typing into a field without checking the result.
fill sets a value, but the page may reformat it, cut it short or reject it. Follow it with expect(field).to_have_value(...) when the value matters.

Trap 10 - Assuming drag and drop works the same everywhere.
Different drag libraries listen for different events. If drag_to does nothing, use the manual mouse version with extra hover steps.

Trap 11 - clear() is a keyboard action too.
clear() selects the text and deletes it, which fires key events the page can see. A test that counts keystrokes, or a page that reacts to them, will notice. test_press_sequentially_fires_key_events has to reset its log after clear() for exactly this reason. fill() has the same effect: it is not a silent value change.


HANDS-ON PRACTICE

1. Run the Module 05 tests:

```
pytest tests/test_05_actions_input.py -v
```

   Expect 14 passed. A plain "pytest" now runs 37 tests: 2 from Module 01, 7 from Module 02, 8 from Module 03, 6 from Module 04 and 14 from Module 05.

2. Watch the typing difference:

```
pytest tests/test_05_actions_input.py --headed --slowmo 300 -k "fill or sequentially"
```

   fill puts the whole text in at once. press_sequentially types it letter by letter.

3. Compare their speed:

```
pytest tests/test_05_actions_input.py --durations=0 -k "fill or sequentially"
```

   --durations=0 lists how long each test took. With only three characters the difference is small, but it grows with every character.

4. Try the keyboard yourself with codegen. Type in the field, press Tab and Escape, and watch the code it writes:

```
playwright codegen https://demo.playwright.dev/todomvc/
```

If a test fails because the demo site changed:

Three tests use the TodoMVC demo: test_press_enter_submits, test_escape_cancels_edit and the helper open_todos. The site can change after these notes were written. If one of them times out on a locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- In test_escape_cancels_edit, the edit box is found with get_by_role("textbox", name="Edit"). If the demo renames it, double-click an item in codegen and see what locator it suggests for the edit field.

The other eleven tests use local pages built with set_content(), so they work without the internet and cannot break because of a site change. If one of those fails, the cause is in the test file itself.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_05_actions_input.py, find test_check_and_uncheck and change the second
   terms.check()
   to
   terms.click()
   To find the line: grep -n "already checked" tests/test_05_actions_input.py
2. Run:

```
pytest tests/test_05_actions_input.py -v -k check_and_uncheck
```

3. The test fails on the next line, expect(terms).to_be_checked(). click() toggled the box off, because it was already ticked. The error shows it expected the box to be checked and found it unchecked.
4. Change it back to terms.check() and run again. It passes.


MENTAL MODEL

- Every action waits for the element to be ready. You do not write waiting code.
- Text: fill replaces and is fast. press_sequentially types key by key, and is only for pages that react to keystrokes.
- State: check and uncheck end in the state you asked for. click only toggles.
- Shortcuts: ControlOrMeta, so the test works on any operating system.
- Dropdowns: select_option only for real select elements. Otherwise click to open, click the option.
- A click that does nothing: find what is in the way. force=True hides the problem.


FOR YOUR OWN APP LATER

- Search-as-you-type boxes usually need press_sequentially. Normal form fields do not.
- A cookie banner or welcome dialog that covers the page is the most common cause of "intercepts pointer events". Handle it once in a fixture (Module 07) rather than in every test.
- Custom dropdowns, date pickers and multi-select widgets are the parts that most often need their own helper method in a page object (Module 07), because the click-open-then-click-option dance is easy to get wrong.
- Keyboard shortcuts are worth testing if your app advertises them. They are also often the only way to reach features in a data grid.
- If drag and drop is a real feature of your app, write one test for it and keep it simple. It is the most fragile kind of test to maintain.


QUIZ (answers below - try before peeking)

1. A field already contains "old text". You call fill("new text"). What is in the field afterwards, and do you need clear() first?

2. The same field contains "old text" and you call press_sequentially("new text"). What is in the field afterwards?

3. When is press_sequentially worth its extra time, and why not use it everywhere?

4. A checkbox may or may not already be ticked, and your test needs it ticked. Why is check() better than click()?

5. Your test does locator.press("Control+a") to select all. It passes on a colleague's Windows machine but fails on your Mac. What is wrong, and what do you write instead?

6. A click fails with an error saying another element "intercepts pointer events". What does that mean, and why is force=True a poor fix?

7. select_option fails with an error saying the element is not a select. What kind of dropdown is it, and how do you choose an option?

8. An element is 2000 pixels below the top of the page. Do you need to scroll before clicking it?

9. DevOps stretch question: a test using press("Control+a") passes on every developer's Windows laptop but fails on the CI machines, which run Linux. The app is fine. What is going on? (Just guess.)


ANSWERS


1. The field contains "new text", and no, you do not need clear().

Why: fill replaces the whole value. It focuses the field, clears it, sets the new value in one step, and fires an input event so the page notices the change. That is what makes it the normal choice for typing: one call, no leftovers, and much faster than typing character by character.

fill("") is the same as clear(), so clearing a field needs only one call either way.

Common mistakes:
- Calling clear() before every fill. It is harmless but pointless.
- Using fill on something that is not a text field. It fails with a clear error, because only inputs, textareas and contenteditable elements accept typing.

See: TYPING: FILL.


2. The field contains "old textnew text". press_sequentially does not clear the field, it types into it from the cursor position.

Why: press_sequentially simulates a person at a keyboard. A person typing into a field that already has text adds to it. Each character fires keydown, keypress and keyup, exactly as a real keystroke would, which is the whole point of the method.

The fix is to clear first:

```python
field.clear()
field.press_sequentially("new text")
```

That is how test_press_sequentially_fires_key_events does it: clear(), then type "abc".

Common mistakes:
- Expecting it to behave like fill. The two differ in exactly this way, which is why Trap 2 exists.

See: TYPING: PRESS_SEQUENTIALLY, and Trap 2.


3. It is worth it when the page reacts to each keystroke. Everywhere else fill is better, because press_sequentially is much slower.

Why it is slower: every character is a separate round trip with three events (keydown, keypress, keyup). Ten characters means thirty events instead of one fill. On a form with several fields, that adds seconds to each test.

When you need it:
- a search box that shows suggestions as you type
- a field that formats while you type: a phone number, a card number, a date
- a character counter
- a Save button that only becomes enabled after a keystroke event
- any field where fill sets the value but the page does not notice

A good rule: start with fill. If the page does not react the way a user would see, switch that one field to press_sequentially.

Common mistakes:
- Using it everywhere "to be realistic". The realism costs time and gains nothing on a normal field.
- Adding delay=100 by default. Only add a delay if the page needs time between keystrokes.

See: TYPING: PRESS_SEQUENTIALLY, and Trap 1.


4. Because check() looks at the current state first and only clicks if the box is not already ticked. click() just toggles, so if the box was already ticked, click() unticks it.

Why that matters: a test should not depend on how the page happened to start. If the app remembers the setting, or an earlier step ticked it, click() produces the opposite of what you wanted, and the test fails somewhere later in a confusing way.

check() always ends in the ticked state, however it started. uncheck() always ends unticked. Playwright also verifies afterwards that the box really is in that state, and fails if the page ignored the click.

You can see this in the break-it-on-purpose step: replacing the second check() with click() unticks the box and the next assertion fails.

Common mistakes:
- Writing an if statement first: if not box.is_checked(): box.click(). That works, but check() already does it, and is_checked() reads the page once without waiting (Module 03).

See: CHECKBOXES AND RADIO BUTTONS, and Trap 3.


5. Control is not the select-all key on a Mac: Command is. Write locator.press("ControlOrMeta+a").

Why: Playwright sends exactly the key you name. "Control+a" sends Ctrl+A on every operating system. On Windows and Linux that is select all. On a Mac, select all is Cmd+A, so Ctrl+A does something else or nothing, and the test fails.

ControlOrMeta means "Control on Windows and Linux, Command on Mac". Playwright chooses the right one for the machine the test runs on, so the same test works everywhere.

Modifier names: Control, Meta (Command on Mac), Shift, Alt (Option on Mac), ControlOrMeta.

Common mistakes:
- Writing two tests, one per operating system. ControlOrMeta avoids that.
- Using Meta+a instead. That fixes the Mac and breaks Windows.

See: KEYS, and Trap 4.


6. It means another element is on top of yours at that spot, so a real click would hit that element instead. force=True is a poor fix because it skips the check rather than solving the problem.

Why the check exists: Playwright works out where the click would land and what is at that point. If it is not your element, the click would not do what the test says it does. The error names the element that is in the way, which is usually a cookie banner, a modal dialog, a loading overlay or a sticky header.

Why force=True is poor: it clicks anyway, ignoring the obstacle. The test may pass while the user is actually blocked by a dialog, so the test is no longer telling the truth about the app. It also hides real bugs, such as an overlay that never closes.

What to do instead:
1. Read the error to see what is covering the element.
2. Deal with it as a user would: close the cookie banner, dismiss the dialog, wait for the overlay to disappear with expect(overlay).to_be_hidden().
3. If it happens in many tests, handle it once in a fixture (Module 07).

Common mistakes:
- Thinking force=True makes a hidden or disabled element work. It does not. It only skips the checks.

See: WHEN A CLICK SEEMS TO DO NOTHING, WHAT FORCE=TRUE REALLY DOES, and Trap 5.


7. It is a custom dropdown built from other elements, usually div and li, that only looks like a dropdown. Click it to open, then click the option:

```python
page.get_by_role("combobox", name="Country").click()
page.get_by_role("option", name="Germany").click()
```

Why: select_option only works on a real HTML select element, because it sets the selection directly and fires the events a select fires. A custom dropdown has none of that: it is ordinary elements with JavaScript behind them, so it has to be used the way a user uses it.

How to tell which kind you have: right-click the dropdown, choose Inspect, and look at the tag. select means select_option. Anything else means click and click.

Well-built custom dropdowns still have the combobox and option roles, so get_by_role works. If they do not, fall back to get_by_text or get_by_test_id.

Common mistakes:
- Assuming anything that looks like a dropdown is a select. Most modern component libraries do not use one.
- Forgetting to open it first. The options often do not exist in the page until the dropdown is opened.

See: SELECT DROPDOWNS, and Trap 6.


8. No. click() scrolls the element into view automatically before clicking.

Why: scrolling is part of the actionability checks. Playwright brings the element into the visible area, waits until it stops moving, then clicks. test_click_scrolls_into_view shows this: the button is 3000 pixels down and the test just clicks it.

Adding your own scrolling is not only unnecessary, it can cause problems: a page that loads content as you scroll may move the element after you scrolled, and your careful scroll position is then wrong anyway.

When you do want scroll_into_view_if_needed():
- to take a screenshot of something further down the page
- to check that content loads only when scrolled to (lazy loading)

Common mistakes:
- Copying scrolling code out of habit, then wondering why the click lands in the wrong place.

See: SCROLLING, and Trap 8.


9. The CI machines run Linux, where select all is Ctrl+A, the same as Windows. So "Control+a" should work there too, and the real cause is usually something else: Playwright on Linux runs the browser with no desktop, and some shortcuts are handled by the browser or window manager rather than the page.

The reliable answer is the same either way: use ControlOrMeta+a so the key is correct on every system, and if the shortcut still does not work on CI, do not rely on a browser-level shortcut at all. Achieve the same thing through the page:

```python
field.fill("")                       # clear it directly
field.press("ControlOrMeta+a")       # or select all, then type over it
```

How to investigate: run the CI job with --tracing retain-on-failure (Module 04) and look at the Before snapshot of the failing step. If the field still has its old text, the shortcut never reached the page.

This is the general lesson for CI: a test that depends on how the operating system handles a key is more fragile than one that only uses the page. Prefer the page-level action when you have a choice.

Common mistakes:
- Assuming Linux behaves like a Mac. It uses Ctrl, like Windows.

See: KEYS, Trap 4, and Module 12 for CI.


End of Module 05. Next up: Module 06, complex interactions (iframes, new tabs and popups, file uploads and downloads, and browser dialogs).