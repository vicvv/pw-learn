PLAYWRIGHT WITH PYTHON - MODULE 02: LOCATORS


GOAL

Find elements on a page in a way that keeps working when the page's code changes. Playwright's main locators find elements the way a user sees them: "the button called Login", "the field labelled Email", not "the third div inside .form-wrapper".

Practice site: Playwright's public TodoMVC demo, https://demo.playwright.dev/todomvc/


WHY USER-FACING LOCATORS

A CSS or XPath locator describes how the page is built. Developers change that all the time: a class is renamed, a div is added, a layout is redone. The page looks the same to the user, but the locator breaks.

A user-facing locator describes what the user sees and does. That changes much less often, because changing it changes the app for real users too. So these locators break less, and when they do break, it usually means something a user would notice really changed.

Bonus: get_by_role only finds elements that assistive technology (screen readers) can find. If a button cannot be found by its role and name, a screen reader user probably cannot find it either.


THE LOCATOR METHODS

page.get_by_role("button", name="Login")
  By role (button, link, heading, checkbox, textbox, listitem...) and accessible name. The first choice for almost everything.

page.get_by_label("Email")
  A form field by the text of its label. Best for inputs.

page.get_by_placeholder("What needs to be done?")
  An input by its placeholder text, when it has no label.

page.get_by_text("walk the dog")
  Any element by its visible text. Good for non-interactive text such as messages and items.

page.get_by_alt_text("Company logo")
  An image by its alt text.

page.get_by_title("Close")
  An element by its title attribute (the tooltip).

page.get_by_test_id("todo-item")
  An element by its data-testid attribute. Developers add these only for tests, so nothing else depends on them.

page.locator("css=...") or page.locator("xpath=...")
  CSS or XPath, as in Selenium. Use only when nothing above works.

Name and text matching:

- By default, name= and get_by_text match part of the text and ignore case. "log" matches "Login" and "Log out".
- exact=True requires the whole text, with the same case: get_by_role("button", name="Login", exact=True)
- A regular expression is also allowed: name=re.compile("log ?in", re.IGNORECASE)

The accessible name usually comes from the element's text, its label, its aria-label attribute, or an image's alt text.


WHICH ONE TO USE (PRIORITY ORDER)

1. get_by_role - what users and screen readers see
2. get_by_label - form fields
3. get_by_placeholder, get_by_text, get_by_alt_text, get_by_title
4. get_by_test_id - when there is no good user-facing option, or the text changes often (translations, dynamic text)
5. CSS or XPath - last resort


LOCATORS ARE LAZY

Creating a locator does not search the page:

```python
button = page.get_by_role("button", name="Save")   # nothing happens yet
button.click()                                      # the search happens now
```

The search happens each time you act on the locator or assert on it, and it waits for the element (Module 03). That means a locator never goes stale. In Selenium, an element found before the page re-rendered could raise StaleElementReferenceException. In Playwright, the locator simply finds the element again.

A locator can be stored in a variable and reused many times, even across page changes.


STRICTNESS: ONE ACTION, ONE ELEMENT

Actions such as click(), fill() and check() need exactly one matching element. If the locator matches several, Playwright refuses to guess and fails with:

```
strict mode violation: get_by_test_id("todo-item") resolved to 3 elements
```

This is a safety feature. Selenium's find_element silently took the first match, which could be the wrong one.

Assertions that work on a list are fine with several matches:

```python
expect(page.get_by_test_id("todo-title")).to_have_count(3)
expect(page.get_by_test_id("todo-title")).to_have_text(["buy milk", "walk the dog", "write tests"])
```

The fix for a strict mode violation is to narrow the locator: filter, chain, or pick one with first, nth or last.


FILTER AND CHAIN: NARROWING DOWN

filter() keeps only the matches that meet a condition:

```python
item = page.get_by_test_id("todo-item").filter(has_text="walk the dog")
```

- has_text="..." keeps elements that contain this text
- has_not_text="..." keeps elements that do not
- has=page.get_by_role("button") keeps elements that contain a matching element
- has_not=... the opposite

Chaining searches inside another locator:

```python
item.get_by_role("checkbox").check()
```

This reads as "the checkbox inside the walk the dog item". It is how you handle lists and tables: find the row, then the thing inside the row.


FIRST, NTH, LAST

```python
titles = page.get_by_test_id("todo-title")
titles.first       # the first match
titles.nth(1)      # the second match (counting starts at 0)
titles.last        # the last match
titles.count()     # how many match right now (no waiting)
```

Use these sparingly. "The second item" breaks as soon as the order changes. filter(has_text=...) says which item you mean.


CSS AND XPATH WHEN YOU NEED THEM

```python
page.locator("#username")                       # CSS by id
page.locator("button.primary")                  # CSS by tag and class
page.locator("xpath=//table//tr[2]/td[3]")      # XPath
page.locator("css=.row").filter(has_text="Total")
```

page.locator() returns the same kind of locator as the get_by methods: lazy, strict, and it can be filtered and chained. The difference is only in what it depends on.


FINDING A LOCATOR: CODEGEN

Playwright can suggest locators for you:

```
playwright codegen https://demo.playwright.dev/todomvc/
```

A browser opens with an inspector window. Click around the page and codegen writes the matching Python code, using the priority order above. Hover over an element to see the locator it would use. Close the browser to stop.

Use codegen to find locators, then copy the good ones into your tests. Do not keep recorded scripts as tests as they are: they have no assertions and repeat themselves. Module 04 covers codegen and the Inspector in more detail.


FROM SELENIUM TO PLAYWRIGHT

- find_element(By.ID, "x") -> page.locator("#x"), or better a get_by method
- find_elements(...) -> a locator with count(), nth() or all()
- WebDriverWait and expected conditions -> built in, the locator waits by itself
- Select(element).select_by_visible_text("Option 2") -> locator.select_option("Option 2")
- element.is_selected() -> expect(locator).to_be_checked()
- StaleElementReferenceException -> does not happen, locators search again each time
- find_element taking the first of several matches -> a strict mode violation instead


THE FILES

- FILES/test_02_locators.py - 7 tests on the TodoMVC demo
- open_with_items() is a plain helper function that opens the app and adds three items, so every test starts the same way. Each test calls it itself, because each test gets a fresh page (Module 01, Trap 5).


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Partial matching by default.
name="Log" matches "Login" and "Log out". If two elements match, you get a strict mode violation, or the wrong one in a list assertion. Use exact=True when the text is short or common.

Trap 2 - Ignoring a strict mode violation with .first.
Adding .first makes the error go away, but you may now be clicking the wrong element. Narrow the locator with filter or chaining instead, so it says which element you mean.

Trap 3 - The role is not the tag.
A div with a click handler is not a button to get_by_role. A link styled to look like a button is still a link. If get_by_role finds nothing, Inspect the element (or use codegen) to see its real role.

Trap 4 - Text that changes.
get_by_text and name= depend on wording. If the app is translated, or the text includes numbers or dates ("3 items left"), the locator breaks. Use a regular expression, a stable part of the text, or get_by_test_id.

Trap 5 - Copying long CSS or XPath from DevTools.
"Copy selector" in Chrome gives paths like #root > div:nth-child(2) > ul > li:nth-child(3). They break on the next layout change. That is the problem user-facing locators solve.

Trap 6 - Using count() as an assertion.
assert titles.count() == 3 checks once, immediately, possibly before the items have appeared. expect(titles).to_have_count(3) waits and retries.

Trap 7 - Hidden elements.
Most locators also match hidden elements, but actions wait for the element to be visible. If an action times out on an element you can see in the HTML, check whether it is hidden, or whether a different, visible element matches the same locator.


HANDS-ON PRACTICE

1. Run the Module 02 tests:

```
pytest FILES/test_02_locators.py -v
```

   Expect 7 passed. A plain "pytest" now runs 9 tests: 2 from Module 01 and 7 from Module 02.

2. Watch them:

```
pytest FILES/test_02_locators.py --headed --slowmo 500
```

3. Try codegen. Add an item, tick it, click "Completed", and watch the code it writes:

```
playwright codegen https://demo.playwright.dev/todomvc/
```

If a test fails because the demo site changed:

The tests rely on the demo site's current labels and test ids. They were written from Playwright's own TodoMVC examples, but the site can change after these notes were written. If a test times out on its first locator:

- Open the site with playwright codegen https://demo.playwright.dev/todomvc/ and hover over the element. Codegen shows the locator it would use today.
- Compare it with the locator in the test, and update the test to match.
- If asking for help, include the full error output: the line that failed and the locator in the error message.

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

3. The test fails with "strict mode violation" on line 42: the locator now matches all 3 items, so there are 3 checkboxes, and Playwright refuses to guess which one to check.
4. Change line 41 back and run again. It passes.


MENTAL MODEL

- Describe the element the way a user would: role and name first.
- Locators are lazy: they search when used, and they never go stale.
- One action needs exactly one element. Several matches = narrow it down.
- Narrow with filter and chaining, not with position.
- CSS and XPath are the last resort.


FOR YOUR OWN APP LATER

- Ask your developers to add data-testid attributes to important elements that have no clear role or label, such as table cells, icons and custom widgets. It costs them little and makes tests much more stable.
- If many elements cannot be found by role, that may also be an accessibility problem worth reporting.
- For tables: find the row with filter(has_text=...), then chain to the cell or button inside it.
- If your app uses a different attribute for tests (for example data-test or data-qa), Playwright can be told to use it with playwright.selectors.set_test_id_attribute("data-test").


QUIZ (answers below - try before peeking)

1. Why does get_by_role("button", name="Save") usually survive a redesign better than page.locator("div.toolbar > button.btn-primary")?

2. A test fails with "strict mode violation: ... resolved to 4 elements". What does it mean, and what is the better fix than adding .first?

3. You write page.get_by_role("button", name="Log"). The page has "Login" and "Log out" buttons. What happens, and how do you fix it?

4. What does it mean that locators are lazy, and which Selenium error does that prevent?

5. What is wrong with assert page.get_by_test_id("todo-item").count() == 3?

6. In a table of users, how do you click the Delete button in the row for "Alice"?

7. DevOps stretch question: CI runs the same tests against a staging build that is shown in German. Tests using get_by_role(..., name="Save") fail, but tests using get_by_test_id pass. Why, and what are your options? (Just guess.)


ANSWERS

1. The role and name describe what the user sees, which rarely changes. The CSS path describes how the page is built (classes, nesting), which developers change often without changing anything for the user.

2. The locator matches 4 elements, and an action needs exactly one, so Playwright refuses to guess. Better fix: narrow the locator so it says which element you mean, with filter(has_text=...), filter(has=...) or chaining inside a parent. .first hides the problem and may act on the wrong element.

3. name matches part of the text, ignoring case, so both buttons match. An action then fails with a strict mode violation. Fix: name="Login", exact=True (or the full name of the button you want).

4. Creating a locator does not search the page. It searches each time you use it, so it always finds the current element. That prevents Selenium's StaleElementReferenceException.

5. count() checks once, immediately, possibly before the items appear, so the test is flaky. Use expect(page.get_by_test_id("todo-item")).to_have_count(3), which waits and retries.

6. page.get_by_role("row").filter(has_text="Alice").get_by_role("button", name="Delete").click()
   Find the row by its text, then the button inside that row.

7. The accessible name is translated ("Speichern" instead of "Save"), so text-based locators no longer match. data-testid is not translated, so those tests pass. Options: run the tests against one known language, use get_by_test_id for elements whose text changes, or load the expected texts from the same translation files the app uses.

RUN IT

```
pytest FILES/test_01_setup.py -v
```


End of Module 02. Next up: Module 03, assertions and auto-waiting (how expect retries, timeouts, and why time.sleep() is never needed).