PLAYWRIGHT WITH PYTHON - MODULE 14: CAPSTONE


GOAL

Put the whole course together on one application, structured the way a real project would be.

Everything so far has been taught one topic at a time. A real suite does not look like that: it looks like a set of user journeys, with the technique hidden underneath. This module builds that, and then steps back to ask what a good suite consists of.

By the end of this module you can:

- design a suite around journeys rather than around features of the tool
- decide what to test through the UI and what to set up another way
- see how page objects, fixtures, saved sessions, parametrize, markers, mocking and accessibility checks fit together in one file
- judge what belongs in a smoke set
- take the whole thing to a real application

Application: saucedemo.com, a public demo shop. Modules 11 and 14 both use it.


HOW THIS SUITE IS PUT TOGETHER

Look at the test file first, before the explanation. It is short, and almost none of it is about Playwright.

```python
@pytest.mark.smoke
def test_buy_two_items_end_to_end(cart_with_two_items: CartPage):
    checkout = cart_with_two_items.checkout()
    checkout.fill_details("Ada", "Lovelace", "12345").continue_to_overview()
    expect(checkout.total).to_be_visible()
    checkout.finish()
    expect(checkout.confirmation).to_be_visible()
```

Five lines, no locators, no waiting, no login. Everything that is not the subject of the test has been pushed somewhere else:

- Logging in happens once per run, in a session fixture, and arrives as logged_in_page (Module 11).
- Opening the shop happens in the shop fixture.
- Filling the cart happens in the cart_with_two_items fixture.
- Finding elements happens in the page objects (Module 07).
- Waiting happens inside expect and inside every action (Module 03).

What is left in the test is the journey and the assertions. That is the goal: a test should read like a description of what a user does and what should be true afterwards.


THE FIXTURE CHAIN

Four fixtures stack up, each adding one thing:

```
page                 (pytest-playwright: a fresh, isolated context)
  storage_state_path (conftest.py, session: log in once, save the session)
    logged_in_page   (conftest.py: a page built from that session)
      shop           (this file: the product list, open)
        cart_with_two_items  (this file: two items added, cart open)
```

A test asks for whichever level it needs, and pytest builds the chain beneath it (Module 07). test_add_to_cart_updates_the_badge asks for shop, because it is about adding; test_remove_an_item_from_the_cart asks for cart_with_two_items, because the adding is just setup.

Notice where each fixture lives. storage_state_path and logged_in_page are in conftest.py, because any test file might want them. shop and cart_with_two_items are in the test file, because they are specific to this application's tests. That is the rule: shared setup goes in conftest.py, local setup stays local.

The cost of the login is paid once for the whole run, not once per test, and every test still gets its own browser context.


WHAT EACH TEST IS FOR

A suite is not a collection of checks. Each test should have a reason to exist, and a different reason from the others.

test_buy_two_items_end_to_end is the journey that matters most: if this fails, the shop does not work. It is the first test to write for any application, and the first thing to run.

test_add_to_cart_updates_the_badge, test_cart_contains_what_was_added, test_remove_an_item_from_the_cart, test_continue_shopping_returns_to_the_products check the steps around that journey, separately, so a failure points at one thing. The end-to-end test tells you something is broken; these tell you what.

test_checkout_validation is three cases from one function (Module 08), each leaving out a required field. Validation is the classic use of parametrize: same logic, different data, and each case reported separately.

test_a_blocked_account_cannot_log_in checks that the application refuses someone it should refuse. Negative cases are routinely forgotten, and they are where the interesting bugs live.

test_the_page_survives_a_failed_image_request blocks the product images and checks the page still works (Module 10). This is a resilience test: real networks fail, and a page that breaks when one asset does not load is a real bug.

test_the_product_page_has_no_new_accessibility_problems runs axe against a known-issues list (Module 13).

test_the_login_form_is_reachable_by_keyboard checks something no axe rule covers: that a keyboard user can reach the fields in a sensible order.

Eight distinct reasons. If you cannot say what a test is for in one sentence, it probably duplicates another.


CHOOSING THE SMOKE SET

Two tests carry @pytest.mark.smoke: the end-to-end purchase and the cart badge. Those run on every push (Module 12).

What makes a good smoke set:

- It covers the journeys that would make the application useless if broken.
- It runs in a few minutes, so people wait for the result.
- It fails loudly on real breakage and almost never otherwise.

What does not belong: validation cases, edge cases, accessibility checks, anything slow, anything flaky. Those run in the full suite, overnight.

A rough guide is five to ten per cent of the suite. The temptation is to keep adding, and the smoke set stops being fast. Resist it: the full suite still runs every night.


WHAT TO TEST THROUGH THE USER INTERFACE

The most common mistake in a real suite is testing everything through the UI because that is what the tool does.

Through the UI, test the things a user does: the purchase journey, the validation messages, what appears on screen. That is what browser tests are uniquely able to check.

Not through the UI:

- Setting up data. Create it through the API (Module 10) and the test starts where it means to.
- Logging in, except in the login tests themselves (Module 11).
- Business rules with many combinations. Twenty tax calculations are twenty fast API tests or unit tests, not twenty browser journeys.
- Anything already covered by a faster test.

The shape people describe as a testing pyramid comes from this: many fast tests underneath, fewer slow ones on top. This suite follows it in miniature: one full journey, several focused UI tests, and setup done through fixtures rather than clicking.


WHERE THE COURSE'S PIECES ARE USED

Every module appears somewhere in this file or the code behind it:

- 01 Setup: the venv, pinned versions, the src layout, .gitignore
- 02 Locators: get_by_role and get_by_placeholder in the page objects, with CSS attribute selectors where saucedemo uses data-test
- 03 Assertions: expect everywhere, never a reading call used as a check
- 04 Debugging: --tracing retain-on-failure when something fails
- 05 Actions: fill, click, press
- 06 Complex interactions: not needed here, which is itself worth noticing
- 07 Fixtures and page objects: the whole structure of the file
- 08 Data-driven: test_checkout_validation, and the smoke marker
- 09 Parallel: every test independent, so pytest -n works
- 10 API and mocking: the blocked image request
- 11 Authentication: the saved session
- 12 CI: the workflow runs the smoke tests on every push
- 13 Visual and accessibility: the axe check and the keyboard test

Module 06 not appearing is the point. You use what the application needs, not everything you know.


THE FILES

- src/pw_learn/pages/cart_page.py - CartPage and CheckoutPage
- src/pw_learn/pages/__init__.py - exports all five page objects
- tests/test_14_capstone.py - 10 test functions, 12 tests

CheckoutPage lives in cart_page.py rather than its own file because it is three steps of one flow, reached only from the cart. Splitting it would add a file and no clarity. One class per page is a guideline, not a rule.

A note on what the page objects do not contain: no assertions, no test data, no waiting. They expose locators and actions, and the tests decide what should be true (Module 07).


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Testing everything through the user interface.
Browser tests are the slowest and most fragile kind. Use them for what only they can check, and set everything else up through fixtures and the API.

Trap 2 - One enormous end-to-end test.
A test that logs in, searches, adds to the cart, checks out and reviews the order fails somewhere in the middle and tells you very little. Keep one journey test, and separate tests for the steps.

Trap 3 - A smoke set that keeps growing.
Every addition seems reasonable, and eventually the fast job is not fast. Keep it to the journeys that must work.

Trap 4 - Duplicating coverage.
Three tests that all prove the cart badge works are three tests to maintain and no extra information. One reason per test.

Trap 5 - Fixtures that do too much.
A fixture that logs in, adds items, applies a discount and opens the checkout leaves the test unable to check anything about those steps. Build fixtures in layers, and ask for the layer you need.

Trap 6 - Test data that collides.
Two tests using the same product or account fail unpredictably in parallel (Module 09). saucedemo's cart is per-session, so this suite is safe; a real application usually is not.

Trap 7 - Only testing the happy path.
Validation failures, blocked accounts, failed network requests. That is where bugs live, and they are cheap to test.

Trap 8 - Page objects that assert.
The page object then decides what success means for every test using it, and failures point at the wrong place.

Trap 9 - Leaving accessibility until the end of a project.
Retrofitting it is far more expensive than writing it correctly, and a known-issues list from day one keeps the problem from growing.


HANDS-ON PRACTICE

1. Run the capstone suite:

```
pytest tests/test_14_capstone.py -v
```

   Expect 12 passed. A plain "pytest" now runs 155 tests: 153 passed, 1 xfailed and 1 rerun.

2. Run only the smoke tests, as CI does on every push:

```
pytest tests/test_14_capstone.py -m smoke -v
```

   Two tests, a few seconds.

3. Watch the main journey:

```
pytest tests/test_14_capstone.py --headed --slowmo 400 -k end_to_end
```

   The browser starts already logged in, because of the saved session, then goes through the checkout.

4. Run the whole suite in parallel, which only works because every test is independent:

```
pytest -n auto -q
```

5. Time the saved session. Comment out the storage_state argument in the logged_in_page fixture in conftest.py so each test logs in through the form, and compare:

```
time pytest tests/test_14_capstone.py -q
```

   Put it back afterwards. The difference on twelve tests is small; on two hundred it is the difference between a suite people run and one they do not.

Break it on purpose (this step is MEANT to fail):

1. In src/pw_learn/pages/cart_page.py, change the checkout button's locator from
   page.locator('[data-test="checkout"]')
   to
   page.locator('[data-test="check-out"]')
2. Run:

```
pytest tests/test_14_capstone.py -v -x
```

3. The first test that checks out fails after 30 seconds, waiting for a button that does not exist. -x stops there rather than letting four tests each wait.
4. Notice the scale: one wrong line in one page object breaks the main journey and all three validation cases. Without page objects that locator would be repeated in four places, and the fix would be four edits.
5. Put it back and run again.


MENTAL MODEL

- A suite is a set of journeys, not a set of checks.
- Setup belongs in fixtures, locators in page objects, assertions in tests.
- One reason per test, and name the reason.
- Through the UI: what a user does. Everything else: the fastest route available.
- Smoke on every push, everything overnight.
- Use what the application needs, not everything the tool offers.


FOR YOUR OWN APP LATER

- Start with one test: the single journey that matters most. Get it running in CI. Everything else is easier after that.
- Write the page objects as you need them, not in advance. A page object for a page no test uses is wasted work.
- Add the negative cases early. They are quick to write and they find more bugs than the happy path.
- Agree the smoke set with the team, and review it occasionally. It drifts.
- Add an accessibility check to the pages tests already visit, with a known-issues list, before the list gets long.
- When a test is hard to write, that is often the application telling you something: missing test ids, no API to set up data, a flow that cannot be reached directly. Those are worth raising.


THE COURSE IN ONE PAGE

What you have built: 155 tests across 14 modules, a package layout, page objects, shared fixtures, data-driven cases, a saved login, mocking, a CI workflow with reports and artifacts, and visual and accessibility checks.

The ideas worth keeping, if everything else fades:

1. Locators are lazy and strict. They find nothing until used, and complain if they match several things (02).
2. expect retries; reading calls do not. Almost every flaky test comes from ignoring this (03).
3. Never write a fixed pause. Every action and assertion already waits (03, 05).
4. When something fails, record a trace and look at it, rather than guessing (04).
5. Every test must be independent: it passes alone, in any order, in parallel (09).
6. Setup belongs in fixtures; locators belong in page objects; assertions belong in tests (07).
7. Test data comes from outside the code, and so do credentials (08, 11).
8. Mock what you do not own, and keep some tests against the real thing (10).
9. A rerun hides a failure. Fix the cause (09).
10. Automated accessibility checks cover about a third of the problem. They are a floor, not a certificate (13).

What to do next:

- Pick a real application, ideally one you know, and write one journey test for it.
- Put it in CI on the first day, not the last.
- Come back to the quizzes. They are the part of these notes designed to be reread.
- The areas this course did not cover: component testing, performance testing, contract testing between services, and test management tooling. Each is a separate discipline.


QUIZ (answers below - try before peeking)

1. test_buy_two_items_end_to_end has five lines and no login, no locators and no waiting. Where did each of those go?

2. Why is shop defined in the test file while logged_in_page is in conftest.py?

3. Why does the suite have both an end-to-end purchase test and separate tests for adding, removing and listing cart items?

4. Only two tests are marked smoke. What makes a test belong in that set?

5. A colleague suggests testing twenty tax calculations by going through the checkout twenty times. What would you suggest instead?

6. test_the_page_survives_a_failed_image_request blocks the product images. What kind of bug is that looking for?

7. The accessibility test allows four known violation IDs. Why not assert zero?

8. Module 06, complex interactions, is not used anywhere in this suite. Is that a gap?

9. In the break-it-on-purpose step, one wrong locator fails four tests. What would have happened without page objects, and what does that say about where locators belong?

10. DevOps stretch question: you join a team with no automated tests and a six-month-old application. What do you do in the first week? (Just guess.)


ANSWERS


1. The login went into a session-scoped fixture, so it happens once per run and arrives as logged_in_page. The locators went into the page objects, CartPage and CheckoutPage. The waiting is inside expect and inside every Playwright action, so it never needs writing at all.

Why that matters beyond tidiness: each of those moves has a separate payoff. The login moved for speed, and because a hundred tests should not depend on the login form. The locators moved so that a change in the application is one edit instead of many. The waiting was never yours to write: expect retries until the page catches up, and every action waits for the element to be ready (Module 03).

What is left in the test is the part that is specific to this test: the journey, and what should be true at the end.

Common mistakes:
- Thinking the test is short because it is incomplete. It checks exactly what it claims to.

See: HOW THIS SUITE IS PUT TOGETHER.


2. Because logged_in_page is useful to any test file in the project, and shop is specific to this application's tests.

Why that distinction: conftest.py makes its fixtures available to every test in the folder without an import (Module 07). That is valuable for shared setup and clutter for anything local. A fixture only one file uses is easier to understand next to the tests that use it, where a reader can see it immediately.

The practical rule: start a fixture in the test file. Move it to conftest.py when a second file needs it.

Common mistakes:
- Putting everything in conftest.py, which becomes a long file of fixtures most tests never use.

See: THE FIXTURE CHAIN, and Module 07.


3. Because they answer different questions. The end-to-end test tells you the shop works. The focused tests tell you which part is broken when it does not.

Why both are needed: a journey test is the only thing that proves the steps work together, which is exactly where integration bugs live. But when it fails, it fails somewhere in the middle of five actions, and the error points at one step without telling you whether the cause is there or earlier.

The focused tests are the diagnosis. If the badge test and the cart contents test both pass while the journey fails, the problem is in the checkout. That narrowing is worth the extra tests.

The reverse arrangement, only focused tests, is worse: every piece can work while the journey is broken, for example if the cart does not survive navigation.

Common mistakes:
- Keeping only the end-to-end test because it covers everything. Coverage is not the same as diagnosis.
- Writing one enormous journey test covering every feature (Trap 2).

See: WHAT EACH TEST IS FOR.


4. It covers a journey that would make the application useless if broken, it runs in seconds, and it does not fail for any other reason.

Why those three: the smoke set runs on every push, so its job is to answer one question quickly, which is whether this change broke something fundamental. Anything that does not serve that question costs time without adding information.

What that excludes: validation cases, edge cases, accessibility checks, slow tests, and anything flaky. A flaky test in the smoke set is particularly damaging, because it trains people to ignore a red build (Module 12).

Roughly five to ten per cent of the suite. It grows if nobody watches it.

Common mistakes:
- Marking tests smoke because they are important. Important and fast are different. The full suite runs nightly, so an important slow test is not neglected.

See: CHOOSING THE SMOKE SET, and Trap 3.


5. Test the calculation directly, through the API or as unit tests, and keep one or two browser tests to prove the result reaches the screen correctly.

Why: twenty browser journeys might take five minutes and break whenever the checkout page changes. Twenty API calls take a second or two and only break when the calculation changes, which is what they are about. The browser adds nothing to nineteen of those cases, because the calculation does not happen there.

The one or two UI tests still matter: they prove the number is displayed, formatted and placed correctly. That is the part only a browser test can check.

This is the testing pyramid in practice: push each check to the fastest level that can answer it honestly.

Common mistakes:
- Using the browser for everything because the suite is a browser suite (Trap 1).
- Dropping the UI test entirely, and missing a formatting bug.

See: WHAT TO TEST THROUGH THE USER INTERFACE, and Module 10.


6. A page that breaks when one of its assets fails to load. The test blocks the images and checks the product list is still there and still has six items.

Why that is a real class of bug: in production, requests fail. A slow connection, a content delivery network with a problem, an ad blocker, a corporate proxy. If a missing image leaves the page half-rendered or throws a script error that stops the rest of the page working, users see a broken shop and nobody will have tested for it.

Mocking makes this trivial to check (Module 10): route the requests, abort them, and assert the page still functions. Producing the same situation with a real server is difficult.

The same pattern applies more widely: a failed API call should show an error message rather than an empty page, and a 500 should not lose what the user typed.

Common mistakes:
- Only testing with everything working. The failure modes are where users suffer.

See: WHAT EACH TEST IS FOR, and Trap 7.


7. Because saucedemo already has those problems, and a test that can never pass gets ignored, then disabled, then deleted. The known-issues list keeps the test green today while failing the moment a new kind of problem appears.

Why this is the right trade-off: the value of an accessibility test on an existing application is not that it proves accessibility. It is that it stops things getting worse. Asserting zero on a page with four existing violations gives you a permanently red test, which protects nothing.

The list is also a backlog. Each entry should have a ticket, and the list should shrink. A version that records counts as well as kinds is stricter still.

Common mistakes:
- Fixing everything first and adding the test later. The test comes first, so problem number five never arrives (Module 13).

See: Module 13, and Trap 9.


8. No. Module 06 covers iframes, popups, uploads, downloads and browser dialogs, and saucedemo has none of them. Using a technique the application does not need would add code and test nothing.

Why this is worth saying explicitly: a common instinct after learning a tool is to demonstrate everything it does. A test suite is not a demonstration. Every test and every abstraction has a maintenance cost, and the only justification is that it checks something the application does.

When an application does have those features, the module is there. A payment form in an iframe, a CSV export, a file upload: each needs its own test, and none of them can be written without knowing the technique.

Common mistakes:
- Adding a page object, a fixture or an abstraction because it seems professional. Add it when a second test needs it.

See: WHERE THE COURSE'S PIECES ARE USED.


9. Without page objects, that locator would appear in all four tests, so the fix would be four edits instead of one, and it would be easy to miss one. It says locators belong in exactly one place per element.

Why this is the strongest argument for the pattern: everything else about page objects is a matter of taste, but this is arithmetic. An application's markup changes often. Each change should cost one edit, not one edit per test that touches that element.

The failure also shows why -x is useful here. Each test waits the full 30-second action timeout for a button that will never exist, so four tests cost two minutes. Stopping at the first failure gives the same information in a quarter of the time.

Common mistakes:
- Writing page objects but still putting locators in tests "just this once". That one grows.

See: the break-it-on-purpose step, and Module 07.


10. Write one end-to-end test for the most important journey, get it running in CI, and only then expand.

Why that order: a single test running automatically is worth more than a plan for fifty. It proves the whole chain works, which is where the unexpected problems are: environments, credentials, test data, CI access, network restrictions, flaky infrastructure. Every one of those is easier to solve for one test than for fifty.

A reasonable first week:

- Day 1 to 2: learn the application. Ask what breaks most often, and what would be most serious. That tells you which journey to automate first.
- Day 2 to 3: set up the project, run one test locally against a test environment.
- Day 3 to 4: get it running in CI on every push, with traces on failure. This is the step teams postpone and regret.
- Day 5: add two or three more tests around that journey, and write down what you learned about the application's testability: missing test ids, no API for setup, data that cannot be reset.

What not to do: spend the week designing a framework, or writing fifty tests that have never run anywhere but your laptop.

Questions worth asking early: is there a test environment, can its data be reset, is there an API, does CI have network access to it, and who looks at a red build.

Common mistakes:
- Building the framework before the first test. The framework that emerges from real tests is better than the one designed in advance.

See: FOR YOUR OWN APP LATER, and Module 12.


End of Module 14, and of the course. Appendix A is a one-page reference of the commands and patterns; Appendix B is a troubleshooting guide for the errors you are most likely to meet.
