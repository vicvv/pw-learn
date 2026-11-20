PLAYWRIGHT WITH PYTHON - MODULE 02: LOCATORS


GOAL

Find elements on a page in a way that keeps working when the page's code changes. Playwright's main locators find elements the way a user sees them: "the button called Login", "the field labelled Email", not "the third div inside .form-wrapper".

By the end of this module you can:

- choose the right locator method for an element
- read and predict an element's role and accessible name
- narrow a locator down when it matches several elements
- understand strict mode errors and fix them properly
- find locators quickly with codegen and debug them when they fail

Practice site: Playwright's public TodoMVC demo, https://demo.playwright.dev/todomvc/
It is a small to-do list app that Playwright maintains for practice: type an item, press Enter, tick items done, filter by All, Active or Completed.


WHAT A LOCATOR IS

A locator is a description of how to find an element, plus everything you can do with it:

```python
login = page.get_by_role("button", name="Login")   # the description
login.click()                                       # an action
expect(login).to_be_enabled()                       # an assertion
```

You build a locator once, then act on it or assert on it as many times as you like. Every action and assertion searches the page again at that moment (see LOCATORS ARE LAZY).


WHY USER-FACING LOCATORS

There are two ways to describe where an element is.

- By how the page is built: its HTML tags, classes and nesting. CSS selectors and XPath work this way.
- By what the user sees: "a button called Save", "a field labelled Email".

Developers change how a page is built all the time: a class is renamed, a div is added around a button, a layout is redone. The page looks the same to the user, but a locator based on structure breaks.

What the user sees changes much less often, because changing it changes the app for real users too. So user-facing locators break less, and when they do break, it usually means something a user would notice really changed. That is a failure worth knowing about.

Example. The same button, found two ways:

```python
page.locator("div.toolbar > div:nth-child(2) > button.btn-primary")   # how it is built
page.get_by_role("button", name="Save")                                # what the user sees
```

If a developer wraps the button in another div, or renames btn-primary to btn-main, the first locator breaks. The second keeps working as long as there is a button called Save.

Bonus: get_by_role only finds elements that assistive technology (screen readers) can find. If a button cannot be found by its role and name, a screen reader user probably cannot find it either. Your tests then also act as a basic accessibility check.


THE LOCATOR METHODS

page.get_by_role("button", name="Login")
  By role and accessible name. The first choice for almost everything: buttons, links, headings, checkboxes, text fields, list items, table rows and cells.

page.get_by_label("Email")
  A form field by the text of its label. Best for inputs, checkboxes and dropdowns that have a label.

page.get_by_placeholder("What needs to be done?")
  An input by its placeholder text (the grey hint inside an empty field), when it has no label.

page.get_by_text("walk the dog")
  Any element by its visible text. Good for non-interactive text such as messages, list items and paragraphs.

page.get_by_alt_text("Company logo")
  An image by its alt text (the description screen readers read out).

page.get_by_title("Close")
  An element by its title attribute (the tooltip that appears on hover).

page.get_by_test_id("todo-item")
  An element by its data-testid attribute. Developers add these only for tests, so no styling or user-facing text depends on them.

page.locator("css=...") or page.locator("xpath=...")
  By page structure. CSS selectors are the patterns web pages use for styling, such as #username (the element with id "username") or button.primary (a button with the class "primary"). XPath is another pattern language that describes a path through the page's HTML, such as //table//tr[2]. Use these only when nothing above works. Without a prefix, page.locator("...") is treated as CSS, or as XPath if it starts with //.


ROLES YOU WILL USE MOST

Every element has a role: what kind of thing it is for the user. Most come from the HTML tag automatically.

- button - a button tag, or an input of type button or submit
- link - an a tag with an href
- heading - h1 to h6. Use level= to pick one: get_by_role("heading", name="todos", level=1)
- textbox - a text input or a textarea
- checkbox - an input of type checkbox
- radio - an input of type radio
- combobox - a select dropdown, or a custom dropdown built to behave like one
- option - an entry inside a dropdown or list box
- list and listitem - ul or ol, and li
- row, cell, columnheader - table parts
- dialog - a popup dialog
- img - an image
- navigation - a nav section, such as a menu

Developers can also set a role directly with the role attribute, for example role="button" on a div. Then get_by_role("button") finds it.


THE ACCESSIBLE NAME

The name= in get_by_role matches the element's accessible name: the text a screen reader reads out for it. It comes from, in this order of preference:

- an aria-labelledby or aria-label attribute
- a label element connected to the field
- the element's own text
- for images, the alt text
- the title attribute, as a last resort

Examples (the HTML, and the locator that finds it):

```
<button>Save</button>
-> get_by_role("button", name="Save")

<button aria-label="Close dialog">X</button>
-> get_by_role("button", name="Close dialog")     (the label wins over the text "X")

<label for="email">Email</label> <input id="email">
-> get_by_role("textbox", name="Email")  or  get_by_label("Email")

<a href="/help"><img alt="Help"></a>
-> get_by_role("link", name="Help")               (the image's alt text names the link)
```

You do not need to work this out by hand. Codegen (below) and Chrome DevTools show the name. In DevTools: right-click the element -> Inspect -> in the panel on the right, open the Accessibility tab. It shows the role and the computed name.


EXTRA OPTIONS FOR GET_BY_ROLE

Besides name=, get_by_role can filter by state:

```python
page.get_by_role("checkbox", checked=True)              # only ticked checkboxes
page.get_by_role("heading", level=2)                    # only h2 headings
page.get_by_role("button", disabled=True)               # only disabled buttons
page.get_by_role("button", expanded=True)               # an open menu button
page.get_by_role("button", pressed=True)                # a toggle button that is on
page.get_by_role("option", selected=True)               # the chosen option
page.get_by_role("button", name="Save", include_hidden=True)   # also hidden ones
```

By default, get_by_role ignores elements hidden from screen readers. include_hidden=True includes them.


NAME AND TEXT MATCHING

- By default, name= and get_by_text match part of the text and ignore upper and lower case. Extra spaces are ignored too. "log" matches "Login" and "Log out".
- exact=True requires the whole text, with the same case: get_by_role("button", name="Login", exact=True)
- A regular expression (a text pattern, from Python's re module) is also allowed, for flexible matching:

```python
import re
page.get_by_role("button", name=re.compile("log ?in", re.IGNORECASE))   # "Login" or "Log in"
page.get_by_test_id("todo-count").filter(has_text=re.compile(r"\d+ items? left"))
```

In the patterns above, " ?" means "an optional space", \d+ means "one or more digits", and "s?" means "an optional s".

Use exact=True when the text is short or common (Save, OK, Log), because partial matching is more likely to find several elements.


WHICH ONE TO USE (PRIORITY ORDER)

1. get_by_role - what users and screen readers see
2. get_by_label - form fields
3. get_by_placeholder, get_by_text, get_by_alt_text, get_by_title
4. get_by_test_id - when there is no good user-facing option, or the text changes often (translations, numbers, dates)
5. CSS or XPath - last resort

This is the same order codegen uses when it suggests a locator.


LOCATORS ARE LAZY

Creating a locator does not search the page:

```python
button = page.get_by_role("button", name="Save")   # nothing happens yet
button.click()                                      # the search happens now
```

The search happens each time you act on the locator or assert on it, and it waits for the element to be ready (Module 03).

Why that matters: modern web pages redraw parts of themselves all the time. When you add a to-do item, the app may throw away the whole list and draw a new one. If a tool held on to the exact element it found earlier, that element would now be "stale": it no longer exists on the page, even though an identical-looking one is there. Using it would fail.

A Playwright locator never goes stale, because it does not hold on to an element. It holds the description, and finds the current element each time.

So a locator can be stored in a variable and reused many times, even across page changes. In the test file, open_with_items() stores the input field in new_todo and uses it three times, while the page redraws after every item.


STRICTNESS: ONE ACTION, ONE ELEMENT

Actions such as click(), fill() and check() need exactly one matching element. If the locator matches several, Playwright refuses to guess and fails with:

```
strict mode violation: get_by_test_id("todo-item") resolved to 3 elements
```

Why refusing is the right thing: imagine a list with three items, each with its own Delete button, and a test that should delete "walk the dog". If the locator matches all three Delete buttons and the tool simply clicked the first one, it would delete "buy milk" instead. The test would carry on, and might even pass, while doing the wrong thing. A strict mode violation stops the test at the exact line where the locator is too vague, so you can fix it.

The error message lists each element it found, with a suggested locator for each. That list often tells you exactly how to narrow it down.

Assertions that work on a list are fine with several matches:

```python
expect(page.get_by_test_id("todo-title")).to_have_count(3)
expect(page.get_by_test_id("todo-title")).to_have_text(["buy milk", "walk the dog", "write tests"])
```

to_have_text with a list checks every match, in order.

The fix for a strict mode violation is to narrow the locator: filter, chain, or (only if position really is the point) pick one with first, nth or last.


FILTER: KEEP ONLY SOME MATCHES

filter() takes a locator that matches several elements and keeps only the ones that meet a condition:

```python
item = page.get_by_test_id("todo-item").filter(has_text="walk the dog")
```

- has_text="..." keeps elements that contain this text somewhere inside them (partial, case-insensitive). A regular expression also works.
- has_not_text="..." keeps elements that do not contain it.
- has=page.get_by_role("button") keeps elements that contain an element matching that locator.
- has_not=... keeps elements that do not contain one.

The locator passed to has= is searched inside each element, so it is written as if from the inside:

```python
# list items that contain a ticked checkbox
page.get_by_role("listitem").filter(has=page.get_by_role("checkbox", checked=True))
```

Filters can be stacked:

```python
page.get_by_role("row").filter(has_text="Alice").filter(has_text="Admin")
```


CHAIN: SEARCH INSIDE ANOTHER ELEMENT

Calling a locator method on a locator searches only inside the elements it matched:

```python
item = page.get_by_test_id("todo-item").filter(has_text="walk the dog")
item.get_by_role("checkbox").check()
```

This reads as "the checkbox inside the walk the dog item". Without the chain, page.get_by_role("checkbox") would match the checkbox of every item, plus the "Mark all as complete" checkbox.

Find the container first, then the thing inside it. This is how you handle lists, tables and repeated cards:

```python
row = page.get_by_role("row").filter(has_text="Alice")
row.get_by_role("button", name="Delete").click()
```


COMBINING LOCATORS: AND, OR

```python
# an element that matches both: a button that is also titled "Subscribe"
page.get_by_role("button").and_(page.get_by_title("Subscribe"))

# whichever appears: a "New" button, or a dialog asking to confirm first
page.get_by_role("button", name="New").or_(page.get_by_text("Confirm security settings"))
```

The underscore is there because "and" and "or" are reserved words in Python. These are handy but rarely needed. filter and chaining cover most cases.


FIRST, NTH, LAST, COUNT, ALL

```python
titles = page.get_by_test_id("todo-title")
titles.first       # the first match
titles.nth(1)      # the second match (counting starts at 0)
titles.last        # the last match
titles.count()     # how many match right now (no waiting)
titles.all()       # a list of locators, one per match, for looping
```

Looping over all matches:

```python
for title in page.get_by_test_id("todo-title").all():
    print(title.inner_text())
```

all() does not wait for the elements to appear. Wait first, for example with expect(...).to_have_count(3), then loop.

Use first, nth and last sparingly. "The second item" breaks as soon as the order changes. filter(has_text=...) says which item you mean. Position is fine when position really is what you are testing, as in test_first_nth_last.


COMMON ACTIONS ON A LOCATOR

What you can do once you have found an element. Each action waits for the element to be ready first (Module 03).

```python
locator.click()                      # click it
locator.dblclick()                   # double-click
locator.fill("buy milk")             # replace the field's contents with this text
locator.clear()                      # empty a field
locator.press("Enter")               # press a key (Enter, Tab, Escape, ArrowDown...)
locator.check()                      # tick a checkbox or radio (does nothing if already ticked)
locator.uncheck()                    # untick a checkbox
locator.select_option("Option 2")    # choose from a select dropdown, by label or value
locator.hover()                      # move the mouse over it
locator.inner_text()                 # read its visible text
locator.input_value()                # read what is typed in a field
locator.get_attribute("href")        # read an attribute
```

fill() clears the field before typing, so the new text replaces the old.

check() is safer than click() for checkboxes: click() toggles, so on a box that is already ticked it would untick it. check() makes sure it ends up ticked.

Prefer assertions to reading values yourself. expect(locator).to_have_text("...") waits and retries. assert locator.inner_text() == "..." reads once, immediately, and can be too early (Module 03).


CSS AND XPATH WHEN YOU NEED THEM

```python
page.locator("#username")                       # CSS by id
page.locator("button.primary")                  # CSS by tag and class
page.locator("[data-qa='submit']")              # CSS by attribute
page.locator("xpath=//table//tr[2]/td[3]")      # XPath
page.locator("css=.row").filter(has_text="Total")
```

page.locator() returns the same kind of locator as the get_by methods: lazy, strict, and it can be filtered and chained. The difference is only in what it depends on: page structure instead of what the user sees.

Good reasons to use CSS: an element with no role, label or text (a decorative icon, a chart), or an attribute your app uses for testing that is not data-testid.


FINDING A LOCATOR: CODEGEN

Playwright can suggest locators for you:

```
playwright codegen https://demo.playwright.dev/todomvc/
```

Two windows open: a browser with the page, and the Playwright Inspector with the code.

- Hover over any element: a box shows the locator codegen would use for it.
- Click, type and tick things: codegen writes the matching Python code in the Inspector.
- The "Pick locator" button (a target icon) lets you click an element and copy its locator without recording an action.
- Close the browser window to stop.

Codegen follows the priority order above, so its suggestions are usually good. Still read each one: it sometimes picks text that changes, or a long CSS path when the element has no good name.

Use codegen to find locators, then copy the good ones into your tests. Do not keep recorded scripts as tests as they are: they have no assertions and repeat themselves. Module 04 covers codegen and the Inspector in more detail.


DEBUGGING A LOCATOR

When a locator does not find what you expect:

1. Read the error. A timeout names the locator it was waiting for. A strict mode violation lists every element it found.
2. Pause the test and try locators live. Put this line in the test where you want to stop:

```python
page.pause()
```

   Run that test with --headed. The browser and the Inspector open and the test waits. In the Inspector, type a locator in the locator box to see what it highlights on the page. Click Resume to continue. Remove page.pause() afterwards.

3. Highlight a locator on the page from the test:

```python
page.get_by_test_id("todo-item").highlight()
```

   With --headed, the matching elements are outlined for a moment.

4. Count the matches:

```python
print(page.get_by_test_id("todo-item").count())
```

   Run with -s to see the print output (pytest hides it otherwise). 0 means nothing matches. More than 1 means it needs narrowing.

5. Check the role and name in Chrome DevTools: Inspect -> Accessibility tab.


THE FILES

- FILES/test_02_locators.py - 7 tests on the TodoMVC demo

What each part does:

open_with_items(page)
  A plain helper function (not a test, because its name does not start with test_). It opens the app and adds the three ITEMS by filling the input and pressing Enter. Every test that needs items calls it itself, because each test gets a fresh page (Module 01, Trap 5).

test_heading_by_role
  Finds the "todos" heading by role and name, and checks it is visible.

test_items_by_test_id
  Finds all item titles by data-testid. to_have_text with a list checks there are exactly three, with these texts, in this order.

test_item_by_text
  Finds one item by its visible text.

test_filter_and_chain
  Narrows all items down to the "walk the dog" one with filter(has_text=...), then chains to the checkbox inside it and ticks it. Checks that item now has the "completed" class, and that the counter says "2 items left".

test_first_nth_last
  Checks the count, then picks items by position with first, nth(1) and last.

test_filter_links_by_role
  Ticks the first item, then clicks the "Active" and "Completed" filter links by role, and checks which items are shown each time.

test_mark_all_by_label
  Ticks "Mark all as complete" by its label, then checks the "Clear completed" button appears.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Partial matching by default.
name="Log" matches "Login" and "Log out". If two elements match, you get a strict mode violation, or the wrong one in a list assertion. Use exact=True when the text is short or common.

Trap 2 - Ignoring a strict mode violation with .first.
Adding .first makes the error go away, but you may now be clicking the wrong element, and the test may pass for the wrong reason. Narrow the locator with filter or chaining instead, so it says which element you mean.

Trap 3 - The role is not the tag.
A div with a click handler is not a button to get_by_role. A link styled to look like a button is still a link. If get_by_role finds nothing, check the real role in codegen or in DevTools (Accessibility tab).

Trap 4 - Text that changes.
get_by_text and name= depend on wording. If the app is translated, or the text includes numbers or dates ("3 items left"), the locator breaks. Use a regular expression, a stable part of the text, or get_by_test_id.

Trap 5 - Copying long CSS or XPath from DevTools.
"Copy selector" in Chrome gives paths like #root > div:nth-child(2) > ul > li:nth-child(3). They break on the next layout change. That is the problem user-facing locators solve.

Trap 6 - Using count() as an assertion.
assert titles.count() == 3 checks once, immediately, possibly before the items have appeared. expect(titles).to_have_count(3) waits and retries.

Trap 7 - Hidden elements.
Most locators also match hidden elements, but actions wait for the element to be visible. If an action times out on an element you can see in the HTML, check whether it is hidden, or whether a different, visible element matches the same locator.

Trap 8 - Looping over all() too early.
all() returns whatever matches at that moment, without waiting. Right after adding items, it may return fewer than expected. Wait with expect(...).to_have_count(...) first.

Trap 9 - Forgetting a page.pause().
A test with page.pause() waits forever for you. Fine while debugging with --headed, but a forgotten one makes the test hang, and on CI the job runs until it times out.

Trap 10 - Chaining from page instead of from the container.
page.get_by_role("checkbox") searches the whole page. item.get_by_role("checkbox") searches only inside item. Calling the method on the wrong object is an easy slip that leads straight to a strict mode violation.

Trap 11 - click() on a checkbox.
click() toggles. On a box that is already ticked, it unticks it. Use check() and uncheck(), which only change the box if needed.


HANDS-ON PRACTICE

1. Check that the demo site loads in your browser: https://demo.playwright.dev/todomvc/

2. Run the Module 02 tests:

```
pytest FILES/test_02_locators.py -v
```

   Expect 7 passed. A plain "pytest" now runs 9 tests: 2 from Module 01 and 7 from Module 02.

3. Watch them:

```
pytest FILES/test_02_locators.py --headed --slowmo 500
```

   You see each test open the app, add three items, and tick or filter them.

4. Try codegen. Add an item, tick it, click "Completed", and watch the code it writes. Hover over elements to see the locators it suggests:

```
playwright codegen https://demo.playwright.dev/todomvc/
```

5. Try page.pause(). Add page.pause() as the last line of test_filter_and_chain, then run:

```
pytest FILES/test_02_locators.py --headed -k filter_and_chain
```

   In the Inspector, type get_by_test_id("todo-item") in the locator box: all three items light up. Then try get_by_test_id("todo-item").filter(has_text="walk"): only one does. Click Resume, then remove the page.pause() line.

If a test fails because the demo site changed:

The tests rely on the demo site's current labels and test ids. They were written from Playwright's own TodoMVC examples, but the site can change after these notes were written. If a test times out on its first locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

If every test fails at its first step, open the site in your browser. If it does not load, the site is down: wait and try again later.

Break it on purpose (this step is MEANT to fail):

1. In FILES/test_02_locators.py, line 41, change
   item = page.get_by_test_id("todo-item").filter(has_text="walk the dog")
   to
   item = page.get_by_test_id("todo-item")
   To confirm the line number: grep -n 'has_text="walk the dog"' FILES/test_02_locators.py
2. Run:

```
pytest FILES/test_02_locators.py -v -k filter_and_chain
```

3. The test fails with "strict mode violation" on line 42: the locator now matches all 3 items, so there are 3 checkboxes, and Playwright refuses to guess which one to check. Read the list of elements in the error: each one comes with a suggested locator.
4. Change line 41 back and run again. It passes.


MENTAL MODEL

- Describe the element the way a user would: role and name first.
- Locators are lazy: they search when used, and they never go stale.
- One action needs exactly one element. Several matches = narrow it down.
- Narrow with filter and chaining, not with position.
- Find the container first, then the thing inside it.
- CSS and XPath are the last resort.
- Stuck? Read the error, then page.pause() and try locators live.


FOR YOUR OWN APP LATER

- Ask your developers to add data-testid attributes to important elements that have no clear role or label, such as table cells, icons and custom widgets. It costs them little and makes tests much more stable.
- If many elements cannot be found by role, that may also be an accessibility problem worth reporting.
- For tables: find the row with filter(has_text=...), then chain to the cell or button inside it.
- If your app uses a different attribute for tests (for example data-test or data-qa), Playwright can be told to use it, so get_by_test_id still works: playwright.selectors.set_test_id_attribute("data-test")
- Custom dropdowns built from div elements usually have the combobox and option roles. Try get_by_role("combobox") and get_by_role("option", name="...") before falling back to CSS.


QUIZ (answers below - try before peeking)

1. Why does get_by_role("button", name="Save") usually survive a redesign better than page.locator("div.toolbar > button.btn-primary")?

2. A test fails with "strict mode violation: ... resolved to 4 elements". What does it mean, and what is the better fix than adding .first?

3. You write page.get_by_role("button", name="Log"). The page has "Login" and "Log out" buttons. What happens, and how do you fix it?

4. What does it mean that locators are lazy, and what problem does that prevent when the page redraws itself?

5. What is wrong with assert page.get_by_test_id("todo-item").count() == 3?

6. In a table of users, how do you click the Delete button in the row for "Alice"?

7. A button shows only an X icon, but its HTML has aria-label="Close dialog". Which locator finds it by role?

8. DevOps stretch question: CI runs the same tests against a staging build that is shown in German. Tests using get_by_role(..., name="Save") fail, but tests using get_by_test_id pass. Why, and what are your options? (Just guess.)


ANSWERS


1. Why does get_by_role("button", name="Save") usually survive a redesign better than page.locator("div.toolbar > button.btn-primary")?

Answer: because it depends on what the user sees, not on how the page is built.

Look at what each locator needs in order to keep working.

page.locator("div.toolbar > button.btn-primary") needs all of these to stay true:
- there is a div with the class "toolbar"
- the button sits directly inside it (that is what > means)
- the button has the class "btn-primary"

Developers change these things constantly, for reasons that have nothing to do with the button: a new design system renames btn-primary to btn-main, a wrapper div is added for spacing, the toolbar is moved into a header. After any of those, the button looks and works exactly the same for users, but the locator finds nothing and the test fails. That failure tells you nothing useful about the app.

get_by_role("button", name="Save") needs only one thing: there is a button called Save. That only changes if the app really changes for users, for example the button is renamed to "Save changes" or removed. When this locator fails, it points at something a user would notice.

Common wrong answers:
- "Because get_by_role is faster." Speed is not the point. Both are fast. The difference is how often they break for no good reason.
- "Because CSS cannot find buttons." It can. The problem is not that CSS fails to find the button today, it is that it depends on details that change tomorrow.

See: WHY USER-FACING LOCATORS, and Trap 5 (copying long CSS from DevTools).


2. A test fails with "strict mode violation: ... resolved to 4 elements". What does it mean, and what is the better fix than adding .first?

Answer: the locator matched 4 elements, but the action needs exactly one, so Playwright stopped instead of guessing. The better fix is to narrow the locator so it describes the one element you mean.

Why Playwright stops: actions such as click(), fill() and check() act on one element. With 4 matches, any choice would be a guess, and a wrong guess makes the test do the wrong thing silently. Picture 4 Delete buttons in a list: clicking "the first one" might delete the wrong item, and the test could still pass.

Why .first is usually the wrong fix: it makes the error disappear, but it does not make the locator correct. It says "whichever one happens to be first", so:
- if the order changes, the test acts on a different element
- if the element you wanted was never first, the test was wrong from the start, and now nothing tells you

The better fixes say which element you mean:

```python
# filter by text inside it
page.get_by_test_id("todo-item").filter(has_text="walk the dog")

# filter by something it contains
page.get_by_role("listitem").filter(has=page.get_by_role("checkbox", checked=True))

# search inside a container
page.get_by_role("row").filter(has_text="Alice").get_by_role("button", name="Delete")

# require the exact name
page.get_by_role("button", name="Save", exact=True)
```

Tip: the error message lists all 4 elements with a suggested locator for each. That list often shows the difference between them, which tells you what to filter on.

When .first is fine: when position really is what you are testing, for example "the newest item appears at the top".

See: STRICTNESS, FILTER, CHAIN, and Trap 2.


3. You write page.get_by_role("button", name="Log"). The page has "Login" and "Log out" buttons. What happens, and how do you fix it?

Answer: both buttons match, so an action on this locator fails with a strict mode violation. Fix it by giving the full name with exact=True.

Why both match: name= matches part of the accessible name by default, and ignores upper and lower case. "Log" is part of "Login" and part of "Log out", so the locator resolves to 2 elements. A click() then stops with "strict mode violation ... resolved to 2 elements".

The fix:

```python
page.get_by_role("button", name="Login", exact=True)
page.get_by_role("button", name="Log out", exact=True)
```

exact=True means the whole name must match, with the same case. "Login" no longer matches "Log out", and the other way round.

Common wrong answers:
- "It clicks the first one." It does not. Playwright never guesses for an action, it stops.
- "It finds nothing, because neither button is called exactly Log." Matching is partial by default, so both are found.
- "Use .first." That would click whichever button happens to come first, which may be the wrong one (see question 2).

Partial matching is useful most of the time, because it tolerates small changes such as extra spaces or a trailing icon label. Switch to exact=True for short or common words such as Log, Save, OK, Edit, Delete, where partial matching easily finds more than one element.

See: NAME AND TEXT MATCHING, and Trap 1.


4. What does it mean that locators are lazy, and what problem does that prevent when the page redraws itself?

Answer: creating a locator does not search the page. It only stores a description. The search happens each time you act on it or assert on it. That means the locator always finds the element that is on the page right now, so it never points at an element that has disappeared.

What happens step by step:

```python
new_todo = page.get_by_placeholder("What needs to be done?")   # 1. only a description, no search
new_todo.fill("buy milk")                                        # 2. search now, then fill
new_todo.press("Enter")                                          # 3. search again, then press
```

The problem it prevents: modern web apps redraw parts of the page constantly. When you add a to-do item, the app may remove the whole list and draw a new one. If a tool remembered the exact element it found in step 1, that element would be gone after the redraw. It would be "stale": it no longer exists, even though an identical-looking element is now in its place. Using it would fail.

A lazy locator has no such problem: at step 3 it searches again and finds the new element.

Common wrong answers:
- "Lazy means it waits a long time." Waiting is a separate feature (Module 03). Lazy means it searches when used, not when created.
- "Lazy means it caches the element to be faster." It is the opposite. It does not keep the element at all, which is exactly why it never goes stale.

Practical result: you can store a locator in a variable at the top of a test and use it all the way through, even after many page changes.

See: LOCATORS ARE LAZY.


5. What is wrong with assert page.get_by_test_id("todo-item").count() == 3?

Answer: count() checks once, at that exact moment, without waiting. If the items are not all on the page yet, it returns a smaller number and the test fails, even though the app is fine. The test is flaky: it passes or fails depending on timing. Use expect(...).to_have_count(3), which waits and retries.

What happens with each version, right after adding three items:

```python
assert page.get_by_test_id("todo-item").count() == 3
```
The app may still be drawing the third item. count() returns 2, the assert fails at once, and nothing is retried.

```python
expect(page.get_by_test_id("todo-item")).to_have_count(3)
```
If the count is 2, expect checks again, and again, until it is 3 or the timeout (5 seconds by default) runs out. As soon as the third item appears, the assertion passes.

On your fast Mac the plain assert may pass every time, which is what makes it dangerous: it then fails on a slower CI machine, or one day in ten, and nobody can reproduce it.

Common wrong answers:
- "Nothing is wrong, count() returns the right number." It returns the number at that instant, which is not always the final number.
- "Add time.sleep(1) before it." That makes the test slower, and it can still be too short. expect waits exactly as long as needed and no longer.

The same applies to any value you read yourself and then assert on: inner_text(), input_value(), is_visible(). Use the matching expect assertion instead (to_have_text, to_have_value, to_be_visible).

See: Trap 6, and Module 03.


6. In a table of users, how do you click the Delete button in the row for "Alice"?

Answer: find the row first, then the button inside that row.

```python
page.get_by_role("row").filter(has_text="Alice").get_by_role("button", name="Delete").click()
```

Read it left to right:
- page.get_by_role("row") - every row in the table
- .filter(has_text="Alice") - only the row that contains "Alice"
- .get_by_role("button", name="Delete") - the Delete button inside that row only
- .click() - click it

Common wrong answers:
- page.get_by_role("button", name="Delete").click() - every row has a Delete button, so this matches all of them and fails with a strict mode violation.
- page.get_by_role("button", name="Delete").first.click() - no error, but it deletes the first user, who may not be Alice. The test could pass while doing the wrong thing.
- page.get_by_text("Alice").get_by_role("button", name="Delete") - get_by_text finds the cell that contains "Alice", and the button is not inside that cell, so this finds nothing.
- page.get_by_role("button", name="Delete").nth(2) - depends on Alice being the third row. Add a user or change the sorting and it deletes someone else.

Also watch the filter text. has_text matches part of the text, so "Alice" would also match a row for "Alice Johnson". If that is possible, filter on something unique, such as an email address, or use a regular expression.

This "container, then the thing inside it" pattern works for any repeated structure: table rows, list items, cards, menu entries.

See: FILTER, CHAIN, and Trap 10.


7. A button shows only an X icon, but its HTML has aria-label="Close dialog". Which locator finds it by role?

Answer: page.get_by_role("button", name="Close dialog")

Why: the accessible name, the name screen readers read out, comes from aria-label first. When a button has an aria-label, that label is its name, and the visible content (here the X) is not used for the name.

Common wrong answers:
- get_by_role("button", name="X") - X is what you see, but it is not the accessible name, so this finds nothing.
- get_by_text("X") - may find the icon or nothing, and even if it finds something it is not a reliable way to identify the button.
- get_by_label("Close dialog") - this is meant for form fields with labels. Use get_by_role("button", name=...) for buttons.

How to check the name of any element without guessing:
- Codegen: hover over the element and it shows the locator it would use, including the name.
- Chrome DevTools: right-click -> Inspect -> Accessibility tab -> "Name".

This is also why the aria-label matters for users: without it, a screen reader would read the button as just "button" (or "X"), and a blind user would not know what it does.

See: THE ACCESSIBLE NAME.


8. DevOps stretch question: CI runs the same tests against a staging build that is shown in German. Tests using get_by_role(..., name="Save") fail, but tests using get_by_test_id pass. Why, and what are your options?

Answer: the accessible name is translated, so text-based locators look for "Save" while the page says "Speichern". data-testid attributes are not translated, so those locators still match.

Why: name= matches the text users see. Translating the app changes exactly that text. data-testid is an attribute in the HTML that users never see, so translators never touch it.

```
English: <button data-testid="save-button">Save</button>
German:  <button data-testid="save-button">Speichern</button>
```

get_by_role("button", name="Save") finds the English button only. get_by_test_id("save-button") finds both.

Options:
- Run the UI tests in one known language. Most apps let you choose the language with a setting or a browser option, and Playwright can set the browser's language: browser.new_context(locale="en-US"). This is the simplest option.
- Use get_by_test_id for elements whose text changes between languages, and keep get_by_role for everything else.
- Load the expected texts from the same translation files the app uses, so the test looks for "Speichern" when the app runs in German. More work, but it also checks that translations exist.

Common wrong answers:
- "Switch every locator to CSS." That gives up the advantages of user-facing locators for all tests, to solve a problem that only affects text.
- "The German build is broken." The build is fine. The tests assumed one language.

See: Trap 4 (text that changes), and Module 09 for CI.


End of Module 02. Next up: Module 03, assertions and auto-waiting (how expect retries, timeouts, and why time.sleep() is never needed).