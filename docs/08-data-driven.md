PLAYWRIGHT WITH PYTHON - MODULE 08: DATA-DRIVEN TESTS AND ORGANISATION


GOAL

Run one test with many inputs, keep test data out of the code, and control which tests run where. As a suite grows, three problems appear: the same test copied with different values, data buried inside code, and no way to run "just the quick ones" or "everything except the slow ones". This module solves all three, and adds settings that change between environments.

By the end of this module you can:

- run one test with many inputs using @pytest.mark.parametrize, with readable names for each case
- load test data from CSV and JSON files
- choose good test cases instead of many redundant ones
- label tests with markers and select them from the command line
- skip a test, or mark it as an expected failure, and know which to use
- point the same tests at a different environment with --base-url, environment variables and a .env file

Practice: Playwright's public TodoMVC demo (https://demo.playwright.dev/todomvc/), plus tests that need no browser at all.


WHY DATA-DRIVEN TESTS

Without parametrize, testing three counter values means three nearly identical tests:

```python
def test_counter_one(todo_page): ...
def test_counter_two(todo_page): ...
def test_counter_three(todo_page): ...
```

The logic is copied three times, and a change to it must be made three times. With parametrize, the logic is written once and the data is listed separately:

```python
@pytest.mark.parametrize("count, label", [(1, "1 item left"), (2, "2 items left"), (3, "3 items left")])
def test_counter_label(todo_page, count, label):
    todo_page.add(*[f"item {number}" for number in range(count)])
    expect(todo_page.counter).to_have_text(label)
```

pytest turns that into three separate tests. Each passes or fails on its own, and the report shows exactly which case failed.


PARAMETRIZE: ONE PARAMETER

```python
@pytest.mark.parametrize("text", ["buy milk", "walk the dog", "write tests"])
def test_add_any_text(todo_page, text):
    todo_page.add(text)
    expect(todo_page.titles).to_have_text(text)
```

- The first argument is the parameter's name, as a string.
- The second is a list of values. pytest runs the test once for each.
- The test function takes a parameter with exactly that name, next to any fixtures it needs.
- Each run gets its own fresh fixtures: a new page, a new todo_page. The cases never share state.


PARAMETRIZE: SEVERAL PARAMETERS

Name them in one comma-separated string, and give each case as a tuple, in the same order:

```python
@pytest.mark.parametrize("count, label", [
    (1, "1 item left"),
    (2, "2 items left"),
])
```

Every tuple must have exactly as many values as there are names. A mismatch stops pytest before any test runs, with an error naming the problem.


READABLE NAMES: IDS AND PYTEST.PARAM

pytest builds a name for each case from its values. Short strings and numbers give readable names, but long or odd values do not: a 100-character string becomes a 100-character test name.

Give each case its own name with pytest.param:

```python
@pytest.mark.parametrize("text", [
    pytest.param("buy milk", id="plain"),
    pytest.param("x" * 100, id="long"),
    pytest.param("<b>not bold</b>", id="html-shown-as-text"),
])
```

The name appears in brackets after the test name, together with the browser:

```
test_add_any_text[chromium-plain] PASSED
test_add_any_text[chromium-long] PASSED
```

Names also work with -k: pytest -k long runs only that case.

pytest.param can also mark a single case, for example as an expected failure:

```python
pytest.param("", id="empty", marks=pytest.mark.xfail(reason="empty items are ignored"))
```


STACKING: EVERY COMBINATION

Two parametrize decorators on one test run every combination of their values:

```python
@pytest.mark.parametrize("first", ["milk", "eggs"])
@pytest.mark.parametrize("second", ["bread", "jam"])
def test_every_combination(todo_page, first, second): ...
```

That is 2 x 2 = 4 tests. Useful, but the number grows fast: three decorators of five values each make 125 browser tests. Stack only when every combination really matters.


TEST DATA FROM FILES

When the cases are many, change often, or come from someone who does not write Python, keep them in a file.

CSV (tests/data/todos.csv): one row per case, one column per value. Good for flat, table-like data that is easy to edit in a spreadsheet.

```
case,items,complete,expected_left
one-item-none-done,milk,,1 item left
two-items-one-done,milk|eggs,milk,1 item left
```

Loading it, and turning each row into a case:

```python
DATA = Path(__file__).parent / "data"

def load_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@pytest.mark.parametrize("items, complete, expected_left", [
    pytest.param(split_items(row["items"]), split_items(row["complete"]), row["expected_left"], id=row["case"])
    for row in load_csv("todos.csv")
])
```

- csv.DictReader turns each row into a dictionary keyed by the column names in the first line, so row["items"] is that row's items column.
- Every value from a CSV is text. "3" is a string, not the number 3. Convert it with int() if you need a number.
- A list inside one cell needs a separator. Here it is |, split by split_items(). An empty cell gives an empty list.
- newline="" and encoding="utf-8" are what Python's documentation recommends for CSV files, so line endings and accented characters are read correctly on every system.

JSON (tests/data/filters.json): good for data with structure, such as lists inside each case.

```json
[
  {"id": "active-hides-completed", "items": ["milk", "eggs", "bread"], "complete": ["eggs"], "filter": "Active", "expected": ["milk", "bread"]}
]
```

```python
@pytest.mark.parametrize("case", [pytest.param(entry, id=entry["id"]) for entry in load_json("filters.json")])
def test_filters_from_json(todo_page, case):
    todo_page.add(*case["items"])
```

JSON keeps lists, numbers and true/false as real Python values, so there is no splitting or converting.

Where the files are found: Path(__file__).parent is the folder the test file is in, so DATA always points at tests/data/, whatever folder you run pytest from. A plain "data/todos.csv" would depend on the current folder and break when run from somewhere else.

When the data is read: the list inside parametrize is built while pytest collects the tests, before any test runs. A missing or broken data file stops the whole collection with an error, which is good: it fails loudly and immediately.


CHOOSING GOOD CASES

More cases are not automatically better. Each one costs time, especially in a browser. Pick cases that would each catch a different bug:

- one typical value (equivalence class): any normal text behaves the same, so one is enough
- boundaries: zero, one, many; the shortest and longest allowed
- special characters: accents, symbols, HTML-like text that must be shown, not run
- known tricky values: an empty field, only spaces, a very long word

The counter test checks 1 (singular "item"), 2 and 3 (plural "items"), and the CSV adds 0. That covers singular, plural and zero. Testing 4, 5 and 6 as well would find nothing new.


MARKERS: LABELLING TESTS

A marker is a label on a test:

```python
@pytest.mark.smoke
def test_counter_label(...): ...

@pytest.mark.slow
def test_filters_from_json(...): ...
```

Select by marker with -m:

```
pytest -m smoke                  # only smoke tests
pytest -m "not slow"             # everything except slow tests
pytest -m "smoke or slow"
pytest -m "smoke and not slow"
```

Register every marker in pytest.ini, with a short description:

```
markers =
    smoke: quick checks of the most important features
    slow: tests that take longer than usual
```

--strict-markers in addopts turns an unregistered marker into an error. Without it, a typo such as @pytest.mark.smok is silently accepted, the test is never selected by -m smoke, and nobody notices. pytest --markers lists every registered marker.

Marking a whole file, with a line near the top after the imports:

```python
pytestmark = pytest.mark.slow
```

Markers combine with parametrize: a marker on a parametrized test applies to every case.

Typical markers: smoke (a few minutes, run on every push), slow, regression, and one per feature area, such as checkout or login.


SKIP AND SKIPIF

A skipped test is not run at all, and is reported as skipped with its reason.

Always skip:

```python
@pytest.mark.skip(reason="the export page is being redesigned")
```

Skip when a condition is true, decided when the tests are collected:

```python
@pytest.mark.skipif(sys.platform == "win32", reason="checks a Unix-style path")
```

Skip from inside the test, when the reason is only known while it runs:

```python
def test_skip_at_runtime(page, browser_name):
    if browser_name == "webkit":
        pytest.skip("not checked in WebKit")
```

Use skip for "this test does not apply here": a different operating system, a missing setting, a browser that does not support a feature. Every skip needs a reason, so the report explains itself.


XFAIL: EXPECTED FAILURES

xfail means "this test is expected to fail, because of a known problem":

```python
@pytest.mark.xfail(strict=True, reason="known gap: empty items are ignored")
def test_empty_item_is_added(todo_page):
    todo_page.new_todo.press("Enter")
    expect(todo_page.items).to_have_count(1, timeout=1000)
```

The test still runs. The results:

- It fails, as expected: reported as xfailed (x), and the run stays green.
- It passes unexpectedly: reported as XPASS. With strict=True that counts as a failure, which is what you want: it tells you the bug is fixed, so remove the marker.

Use strict=True. Without it, an unexpected pass is only a note in the report, so the marker can stay long after the bug is fixed and the test never protects anything.

timeout=1000 keeps the expected failure fast: one second instead of the five-second default.

Skip versus xfail:

- skip: the test does not apply here, so it is not run.
- xfail: the test applies, but a known bug makes it fail. It runs, and you find out when the bug is fixed.


SEEING SKIPS AND XFAILS

By default, pytest shows them only as letters: s for skipped, x for xfailed, X for xpassed. To see the reasons:

```
pytest -rs          # reasons for skips
pytest -rxX         # reasons for xfail and xpass
pytest -ra          # a short summary of everything that did not simply pass
```


SETTINGS PER ENVIRONMENT

The same tests usually need to run against different copies of the app: your own computer, a shared test server, a staging site before release. What changes is the address, and sometimes accounts or feature flags. Never copy tests per environment. Make the settings come from outside the code.

Base URL. pytest-playwright has a --base-url option. pytest.ini sets it for every run:

```
addopts = --strict-markers --base-url https://demo.playwright.dev
```

With a base URL, page.goto() accepts addresses that start with /:

```python
page.goto("/todomvc/")         # becomes https://demo.playwright.dev/todomvc/
```

Point the same tests at another server from the command line. A value given on the command line wins over addopts:

```
pytest --base-url https://staging.example.com
```

The base_url fixture gives the value to any test that asks for it. Full addresses (starting with https://) ignore the base URL, so the earlier modules' tests are unaffected.


Environment variables. src/pw_learn/settings.py reads values from the environment, with a default:

```python
def todo_url() -> str:
    return os.environ.get("TODO_URL", DEFAULT_TODO_URL)
```

Set one for a single run:

```
TODO_URL=https://staging.example.com/todomvc/ pytest
```

On Windows (PowerShell): $env:TODO_URL = "https://staging.example.com/todomvc/" on its own line, then pytest.


The .env file. Typing variables before every command is tedious, so the values can live in a file called .env in the repo root:

```
TODO_URL=https://staging.example.com/todomvc/
```

tests/conftest.py reads it before any test runs:

```python
settings.load_env_file(Path(__file__).parent.parent / ".env")
```

- Path(__file__).parent.parent is the repo root: conftest.py is in tests/, and its parent is the root.
- If there is no .env file, nothing happens and the defaults apply.
- A variable already set in the terminal or by CI wins over the file. That is os.environ.setdefault: it only sets a value that is not set yet.

.env is in .gitignore and must never be committed, because it often holds passwords and tokens. .env.example is committed instead: it lists the setting names with harmless values, so anyone cloning the repo knows what to put in their own .env.

The usual library for this is python-dotenv (pip install python-dotenv, then load_dotenv()). This course uses a few lines of its own in settings.py, so there is one dependency fewer and you can see exactly what happens.


Testing code that reads the environment: monkeypatch

```python
def test_setting_from_environment(monkeypatch):
    monkeypatch.setenv("TODO_URL", "https://staging.example.com/todomvc/")
    assert settings.todo_url() == "https://staging.example.com/todomvc/"
```

monkeypatch is a built-in pytest fixture that changes things for one test and puts them back afterwards. setenv sets a variable, delenv removes one (raising=False means "no error if it was not set"). After the test, the environment is exactly as it was, so no other test is affected.


THE FILES

- pytest.ini - registers the smoke and slow markers, adds --strict-markers, and sets the base URL
- src/pw_learn/settings.py - todo_url(), read_env_file(), load_env_file()
- tests/conftest.py - now also loads .env before the tests run
- tests/data/todos.csv - 5 counter cases
- tests/data/filters.json - 3 filter cases
- .env.example - the setting names, committed as a template
- tests/test_08_data_driven.py - 13 test functions, 26 tests once parametrized

The tests:

- test_add_any_text (4 cases, smoke) - plain text, accents, a long text, and HTML-like text that must appear as text
- test_counter_label (3 cases, smoke) - singular and plural counter labels
- test_every_combination (4 cases) - two stacked parametrize decorators
- test_counter_from_csv (5 cases) - cases from the CSV file, named by its case column
- test_filters_from_json (3 cases, slow) - cases from the JSON file
- test_skip_on_some_systems - skipped on Windows by skipif
- test_skip_at_runtime - skipped on WebKit from inside the test
- test_empty_item_is_added - an expected failure (strict xfail)
- test_relative_url_uses_base_url - page.goto("/todomvc/") with the base URL
- test_setting_has_a_default, test_setting_from_environment, test_read_env_file - settings, no browser

The last three, and test_skip_on_some_systems, do not use page, so they run once in total and have no [chromium] in their names, even with several --browser options.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - The parameter name does not match.
@pytest.mark.parametrize("text", ...) needs a function argument called exactly text. A different name stops pytest with an error that the function uses no argument "text".

Trap 2 - The wrong number of values.
With "count, label", every case needs exactly two values. pytest stops before running anything.

Trap 3 - A single parameter given a tuple without a comma.
("buy milk") is just a string in brackets, not a tuple. For one parameter, give plain values: ["buy milk", "walk the dog"].

Trap 4 - Unreadable test names.
Long values make long names that are hard to read in the report and to select with -k. Use pytest.param(..., id="short-name").

Trap 5 - Stacking too much.
Each extra decorator multiplies the number of tests. Browser tests are slow, so a large grid can add many minutes.

Trap 6 - Numbers from a CSV are text.
"3" from a CSV is a string. Comparing it with 3 is always False. Convert with int().

Trap 7 - A data path relative to the current folder.
open("tests/data/todos.csv") only works when pytest is run from the repo root. Build the path from Path(__file__).parent.

Trap 8 - An unregistered marker.
Without --strict-markers, @pytest.mark.smok (a typo) is accepted silently and the test is never selected. Keep --strict-markers and register every marker.

Trap 9 - xfail without strict=True.
When the bug is fixed, the test passes and is only reported as XPASS, so the marker stays forever and the test protects nothing. Use strict=True.

Trap 10 - Using skip for a known bug.
A skipped test never runs, so you never find out when the bug is fixed. Known bugs are xfail.

Trap 11 - Committing .env.
It usually holds passwords and tokens. Keep it in .gitignore, and commit .env.example with harmless values instead.

Trap 12 - Changing os.environ directly in a test.
The change leaks into every test that runs after it. Use monkeypatch, which undoes it.

Trap 13 - Partial text matching in data.
complete("milk") uses filter(has_text=...), which matches any item containing "milk". Data with overlapping words, such as "milk" and "oat milk", picks the wrong item or several. Keep test data distinct.


HANDS-ON PRACTICE

1. Create the folder for the data files, then create the files listed above:

```
mkdir -p tests/data
```

2. Run the Module 08 tests:

```
pytest tests/test_08_data_driven.py -v
```

   Expect 25 passed and 1 xfailed. The xfailed one is test_empty_item_is_added, which is meant to fail. A plain "pytest" now collects 89 tests: 88 passed and 1 xfailed.

3. Look at the case names in the output, for example test_counter_from_csv[chromium-two-items-one-done]. Run one case on its own:

```
pytest tests/test_08_data_driven.py -v -k two-items-one-done
```

4. Select by marker:

```
pytest -m smoke -v
pytest -m "not slow" -q
```

   -m smoke runs 7 tests. "not slow" runs everything except the 3 JSON cases.

5. See the reasons for skips and expected failures:

```
pytest tests/test_08_data_driven.py -rsxX
```

   On a Mac nothing is skipped (the skips only apply to Windows and WebKit), and the xfail reason is listed. Then run with WebKit too and see the runtime skip:

```
pytest tests/test_08_data_driven.py -rs -k skip_at_runtime --browser chromium --browser webkit
```

6. Try a .env file:

```
cp .env.example .env
git status
```

   .env does not appear in git status, because it is in .gitignore. .env.example does, because it is meant to be committed.

7. Point the base URL somewhere else and watch the base URL test fail, as it should:

```
pytest tests/test_08_data_driven.py -k relative_url --base-url https://example.com
```

   The command-line value wins over pytest.ini, so the test now sees https://example.com.

If a test fails because the demo site changed:

The TodoMVC tests go through the TodoPage page object, so a changed locator is fixed in one place: src/pw_learn/pages/todo_page.py. Open the site with playwright codegen https://demo.playwright.dev/todomvc/, hover over the element, and update the locator.

If test_empty_item_is_added is reported as failed with XPASS(strict), the demo now adds empty items. The xfail marker did its job: it told you the behaviour changed. Remove the marker, or the test, to match the new behaviour.

The settings tests and test_skip_on_some_systems need no browser and no internet.

Break it on purpose (this step is MEANT to fail):

1. In tests/data/todos.csv, change the expected text on the two-items-one-done row from
   1 item left
   to
   2 items left
   To find the row: grep -n "two-items-one-done" tests/data/todos.csv
2. Run:

```
pytest tests/test_08_data_driven.py -v -k from_csv
```

3. Exactly one case fails: test_counter_from_csv[chromium-two-items-one-done]. The other four pass. The case name tells you which data row is wrong, without reading any code. The error shows "2 items left" expected and "1 item left" received.
4. Change the row back and run again. 5 passed.


MENTAL MODEL

- parametrize: logic once, data listed separately, one test per case.
- pytest.param(..., id=...): a readable name per case.
- Data files: CSV for flat tables, JSON for structured data, both found with Path(__file__).parent.
- Markers: labels, registered in pytest.ini, selected with -m.
- skip: does not apply here, not run. xfail with strict=True: a known bug, run, and you are told when it is fixed.
- Settings come from outside the code: --base-url, environment variables, .env. Never commit .env.


FOR YOUR OWN APP LATER

- Form validation is the classic data-driven test: one test, many invalid inputs, each with the error message it should show.
- Keep a small smoke set (a handful of the most important flows) that runs in a few minutes on every push, and the full suite nightly or before release.
- Ask testers or business analysts to maintain the CSV of cases. They can add a case without touching Python.
- Set every environment's address with --base-url or an environment variable, so the same suite runs against local, test and staging copies of the app.
- Put account names and passwords for each environment in .env locally and in CI secrets (Module 12), never in the code or in a committed file.
- Record known bugs as strict xfail with the ticket number in the reason, so the test turns red the day the fix lands and reminds you to update it.


QUIZ (answers below - try before peeking)

1. How many tests does this create, and what does each receive?
   @pytest.mark.parametrize("count, label", [(1, "1 item left"), (2, "2 items left"), (3, "3 items left")])

2. Why is pytest.param("x" * 100, id="long") better than just "x" * 100 in the list?

3. A test has two stacked parametrize decorators with 3 and 4 values. How many tests does it create?

4. A CSV column expected_count holds 3, and the test compares it with expect(...).to_have_count(row["expected_count"]). What goes wrong, and how do you fix it?

5. Why does the test file build its data path with Path(__file__).parent instead of writing "tests/data/todos.csv"?

6. A test is marked @pytest.mark.smok (a typo). What happens with and without --strict-markers?

7. A known bug makes a test fail. Should you use skip or xfail, and why strict=True?

8. pytest.ini sets --base-url https://demo.playwright.dev. What does page.goto("/todomvc/") open, and how do you point the same tests at https://staging.example.com without changing any file?

9. Why is .env in .gitignore while .env.example is committed?

10. Why does test_setting_from_environment use monkeypatch.setenv instead of os.environ["TODO_URL"] = ...?

11. DevOps stretch question: you want a quick smoke run on every push and the full suite every night, from the same tests. How? (Just guess.)


ANSWERS


1. Three tests. The first receives count=1 and label="1 item left", the second count=2 and "2 items left", the third count=3 and "3 items left".

Why: parametrize turns one function into one test per tuple. The names in the string ("count, label") are matched in order to the values in each tuple, and to the function's arguments with the same names. Each of the three runs separately, with its own fresh page and todo_page, and passes or fails on its own. With two browsers, each of the three runs once per browser: six results.

Common mistakes:
- Thinking it is one test that loops over the values. Then the first failure would hide the rest. Separate tests mean every case is reported.

See: PARAMETRIZE: SEVERAL PARAMETERS.


2. Because the test gets a short, readable name: test_add_any_text[chromium-long] instead of a name containing a hundred x characters.

Why: pytest builds each case's name from its values. Short strings and numbers give good names, but long, empty or unusual values make names that are unreadable in the report and impossible to type after -k. The id says what the case is about, which is more useful than the value anyway. pytest.param can also attach a marker to just that case.

Common mistakes:
- Thinking id changes what the test receives. The test still gets the full value. Only the name changes.

See: READABLE NAMES: IDS AND PYTEST.PARAM, and Trap 4.


3. 12 tests: every combination of the two lists, 3 x 4.

Why: each stacked decorator multiplies the cases by its number of values. That is the point of stacking, and also its danger: a third decorator of 5 values would make 60 browser tests. Stack only when every combination genuinely needs checking.

Common mistakes:
- Answering 7, as if the lists were added. Stacking multiplies.

See: STACKING: EVERY COMBINATION, and Trap 5.


4. Every value from a CSV is text, so row["expected_count"] is the string "3", not the number 3. Convert it: to_have_count(int(row["expected_count"])).

Why: csv.DictReader does not guess types. Everything in a cell comes back as a string. A string where a number is expected either raises an error or, in a plain comparison such as "3" == 3, is simply False, which can make a test fail in a confusing way. Convert when you read the row. JSON does not have this problem: numbers in JSON come back as numbers.

Common mistakes:
- Assuming a cell that looks like a number is one.

See: TEST DATA FROM FILES, and Trap 6.


5. Because Path(__file__).parent always points at the folder the test file is in, whatever folder pytest is run from. "tests/data/todos.csv" only works when pytest runs from the repo root.

Why: a plain relative path is looked up from the current folder of the terminal. Run pytest from tests/, or let an editor run it from somewhere else, and the file is not found. __file__ is the test file's own path, so .parent / "data" is always tests/data/.

Common mistakes:
- Using a full path from your own computer, which works nowhere else and puts your username in the repo.

See: TEST DATA FROM FILES, and Trap 7.


6. With --strict-markers, pytest stops with an error saying the marker smok is not registered. Without it, the typo is accepted silently, and the test is simply never selected by -m smoke.

Why: without the strict option, any marker name is allowed, so a misspelling creates a new, unused label. Nothing fails, so nobody notices that a smoke test has fallen out of the smoke run. --strict-markers turns that silent mistake into an immediate, obvious error.

Common mistakes:
- Removing --strict-markers to make the error go away. Fix the spelling, or register the marker in pytest.ini.

See: MARKERS: LABELLING TESTS, and Trap 8.


7. xfail, because the test still applies and still runs, so you find out when the bug is fixed. strict=True makes an unexpected pass count as a failure, so the fix cannot go unnoticed.

Why: skip means the test is not run at all. For a known bug, that hides the day the bug is fixed, and the test stays switched off forever. xfail runs the test and expects it to fail: while the bug exists, the run stays green. With strict=True, when the bug is fixed and the test passes, pytest reports it as a failure (XPASS strict), which tells you to remove the marker. Without strict, it is only a note, and the marker usually stays.

Common mistakes:
- Using skip because it is quicker. A skipped test protects nothing.
- Leaving out the reason. Put the ticket number in it, so anyone can look the bug up.

See: XFAIL: EXPECTED FAILURES, Trap 9 and Trap 10.


8. It opens https://demo.playwright.dev/todomvc/. To use staging instead, run pytest --base-url https://staging.example.com.

Why: with a base URL, page.goto() adds any address starting with / to it. A value given on the command line wins over the one in pytest.ini's addopts, so the same tests run against another server with no file changed. Addresses that start with https:// are full addresses and ignore the base URL.

Common mistakes:
- Copying the tests for each environment, or editing pytest.ini before every run.
- Writing full addresses everywhere, which makes the base URL useless.

See: SETTINGS PER ENVIRONMENT.


9. Because .env holds your real settings, often including passwords and tokens, while .env.example holds only the setting names with harmless values, as a template for others.

Why: anything committed stays in Git's history for good, and in a public repo anyone can read it. A secret committed once must be changed, because deleting the file later does not remove it from history. .env.example tells someone cloning the repo which settings exist: they copy it to .env and fill in their own values.

Common mistakes:
- Putting real values in .env.example "just for now".

See: SETTINGS PER ENVIRONMENT, and Trap 11.


10. Because monkeypatch puts the environment back after the test. A direct change to os.environ stays for the rest of the run and affects every test after it.

Why: os.environ is shared by the whole test run. If one test sets TODO_URL to a staging address and never removes it, a later test that relies on the default now uses staging, and fails for no obvious reason, depending on the order the tests ran in. monkeypatch.setenv and delenv record the original value and restore it when the test ends, even if it fails.

Common mistakes:
- Removing the variable by hand at the end of the test. A failure halfway skips that line.

See: SETTINGS PER ENVIRONMENT, and Trap 12.


11. Use markers. Run pytest -m smoke on every push, and plain pytest (everything) on a nightly schedule.

Why: the tests are the same, only the selection changes. In GitHub Actions, one workflow runs on push with -m smoke, so the feedback comes in a few minutes. A second workflow, triggered by a schedule (a cron expression such as "0 2 * * *" for 2 a.m. every night), runs the whole suite, including slow tests. Module 12 sets this up.

```yaml
on:
  push:
  schedule:
    - cron: "0 2 * * *"
```

Common mistakes:
- Keeping a separate copy of the smoke tests. Markers exist so that one set of tests can be selected in different ways.

See: MARKERS: LABELLING TESTS, and Module 12 for CI.


End of Module 08. Next up: Module 09, parallel runs, retries and flaky tests.