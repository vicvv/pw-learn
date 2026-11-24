PLAYWRIGHT WITH PYTHON - MODULE 13: VISUAL AND ACCESSIBILITY TESTING


GOAL

Two kinds of problem that ordinary tests never notice.

A functional test checks that the right text and elements are present. It cannot tell you that the layout collapsed, that a button is now white on white, or that the page is unusable with a screen reader. Every assertion so far would pass on a page that is visually broken or impossible to navigate without a mouse.

By the end of this module you can:

- compare a screenshot against an approved reference image, and understand why that is harder than it sounds
- keep visual tests stable, and know what makes them flaky
- use ARIA snapshots to check a page's structure rather than its pixels
- run automated accessibility checks with axe, and read the results
- know what automated accessibility testing does and does not cover
- deal with an application that already has known problems

Practice: tiny local pages built with page.set_content(), one of them deliberately inaccessible.


THREE DIFFERENT CHECKS

These are often lumped together. They answer different questions:

- Visual comparison: does the page look the way it looked when we approved it? Pixel by pixel. Catches layout breakage and styling mistakes, and knows nothing about meaning.
- ARIA snapshot: does the page have the structure we expect, in terms of roles and names? Catches a heading that became a plain div, or a label that disappeared. Ignores appearance entirely.
- Accessibility checks (axe): does the page break any known accessibility rules? Catches missing alt text, unlabelled fields, poor contrast, broken landmarks.

A page can pass all three and still be unusable, and that is the honest framing for this whole module. These are safety nets, not proof.


VISUAL COMPARISON: HOW IT WORKS

The idea is simple:

1. Take a screenshot.
2. Compare it with a stored reference image, often called a baseline or golden image.
3. If they differ by more than an allowed amount, fail, and save an image showing the difference.

The first run has nothing to compare against, so it writes the reference and reports a failure, telling you to review the images. That is deliberate: a reference image is an approval, and it should never be created silently.

Playwright's Python API has no built-in comparison, unlike its JavaScript version. This module uses the community plugin pytest-playwright-visual-snapshot:

```
pip install pytest-playwright-visual-snapshot
```

It provides an assert_snapshot fixture:

```python
def test_visual_page_snapshot(page: Page, assert_snapshot):
    page.set_viewport_size({"width": 400, "height": 300})
    page.set_content(STABLE_PAGE)
    assert_snapshot(page.screenshot())
```

Running it:

```
pytest tests/test_13_visual_a11y.py --update-snapshots      # write or replace the references
pytest tests/test_13_visual_a11y.py                          # compare against them
```

Where the images go: a __snapshots__ folder next to the test file, with one file per test, named after the test, the browser and the operating system:

```
__snapshots__/test_13_visual_a11y/test_visual_page_snapshot/test_visual_page_snapshot[chromium][darwin].png
```

The browser and operating system are in the name because the same page renders differently on each. A reference taken on a Mac will not match a Linux CI runner.

These images are committed, unlike test-results/. They are the approved state, so they belong in the repository and their changes should be reviewed like any other change.


WHY VISUAL TESTS GO WRONG

Visual testing has a reputation for being flaky, and it is deserved. Anything that changes a single pixel fails the comparison.

Fonts. The commonest cause. A font that exists on your Mac but not on the Linux runner is substituted, every piece of text shifts slightly, and the whole page differs. The same font can even render differently between operating systems because of how each smooths text.

Anti-aliasing and scaling. Different graphics hardware and different device scale factors produce slightly different edges.

Anything that moves or changes:

- animations and transitions still running when the screenshot is taken
- a blinking cursor in a focused field
- dates, times, counters, random identifiers
- images loaded from outside, which may be slow or different
- adverts, chat widgets, cookie banners

Content that is not the same twice. A list of recent orders, a "last updated" line, a user's name.

How to make them stable:

- Compare one element, not the whole page. test_visual_element_snapshot screenshots just the card. Far less surface area, far less to go wrong.
- Fix the viewport size, so the layout is identical every time.
- Fix the clock, so dates do not change (Module 10).
- Use fixed test data, not whatever is in the database today.
- Block or mock anything external: images, adverts, analytics (Module 10).
- Stop animations, by injecting CSS that disables them:

```python
page.add_style_tag(content="*, *::before, *::after { animation: none !important; transition: none !important; }")
```

- Mask the parts that legitimately change:

```python
page.screenshot(mask=[page.get_by_test_id("last-updated")])
```

Masking paints a solid box over those elements before comparing, so their content is ignored.

- Allow a small tolerance:

```python
assert_snapshot(page.screenshot(), threshold=0.2)
```

The threshold is how different two pixels may be before they count as changed. A small value absorbs anti-aliasing noise without hiding real changes. Too large and the test stops catching anything.

Generate the references on the same platform as the one that will run the tests. In practice, that usually means generating them on CI, in the same container the tests run in, and never on a developer's laptop.


WHEN VISUAL TESTING IS WORTH IT

It is worth it for:

- design systems and component libraries, where the component's appearance is the product
- a handful of important pages, where a broken layout would be serious and obvious
- checking a deliberate style change did not affect anything else

It is not worth it for:

- every page of an application that changes often. The maintenance cost exceeds the value, and people start approving differences without looking, which defeats the whole point.
- anything a functional assertion can check. "The error message is red" is better tested by checking the class or the computed style than by comparing a picture.

The honest summary: visual tests catch a real class of bug that nothing else catches, and they cost more upkeep than any other kind of test. Use them deliberately and sparingly.


ARIA SNAPSHOTS

An ARIA snapshot is a text description of the page's structure, as assistive technology sees it: roles, accessible names, and nesting. No pixels, no HTML.

```python
expect(page.locator("body")).to_match_aria_snapshot("""
    - main:
      - heading "Sign up" [level=1]
      - img "Decorative line"
      - text: Email address
      - textbox "Email address"
      - button "Submit"
    """)
```

Each line is a role and its accessible name. Indentation shows nesting: everything indented under main is inside that landmark. Attributes such as [level=1] appear in brackets.

What this catches that a visual test does not: a heading changed to a styled div (it still looks like a heading, so the screenshot is unchanged, but the structure is gone), a label that disappeared, a button that became a clickable div, a landmark that was removed.

What it catches that a functional test does not: everything about structure that no individual assertion happens to check.

It is also much more stable than a screenshot, because it ignores appearance entirely. Restyling the page does not break it; restructuring it does, which is exactly the right sensitivity.

The quickest way to write one is to let it fail. Write the assertion with an empty or approximate snapshot, run it, and the error prints the actual structure, which you can then check and paste in.

Playwright can also store these in separate .aria.yml files, which suits long snapshots better than inline text.


ACCESSIBILITY: WHY IT MATTERS

Roughly one person in six has a disability of some kind. For software, that means people using screen readers, keyboard navigation, screen magnification, voice control, or high-contrast settings.

Beyond the ethics, there is a legal dimension: accessibility requirements apply to public sector bodies and many private ones in the EU (the European Accessibility Act), the UK (the Equality Act), the United States (the ADA and Section 508), and elsewhere. For a company selling software, an accessibility audit is often part of a procurement process, and failing one can lose a contract.

The standard is WCAG, the Web Content Accessibility Guidelines, with levels A, AA and AAA. AA is the usual target.


AXE

axe-core is Deque's accessibility engine: a JavaScript library that is injected into a page and checks it against a large set of rules. It is the engine behind most accessibility testing tools, including the browser extensions.

```
pip install axe-playwright-python
```

```python
from axe_playwright_python.sync_playwright import Axe

axe = Axe()
results = axe.run(page)
assert results.violations_count == 0, results.generate_report()
```

- axe.run(page) injects the engine, runs every rule, and returns the results.
- violations_count is the number of rules broken.
- generate_report() produces a readable report, and passing it as the assertion message means a failure prints exactly what is wrong.
- results.response["violations"] is the raw list, each with an id, an impact level, a help URL, and the elements affected.

A violation looks like this in the output:

```
Rule Violated:
image-alt - Ensure <img> elements have alternative text
      URL: https://dequeuniversity.com/rules/axe/4.14/image-alt
      Impact Level: critical
      Elements Affected:
      1)    Target: img
            Snippet: <img src="...">
```

The help URL is genuinely useful: Deque's pages explain what the rule means, why it matters, and how to fix it.

Common rules you will meet:

- image-alt: an image with no alternative text
- label: a form field with no label
- color-contrast: text too close in colour to its background
- landmark-one-main: the page has no main landmark
- region: content not inside any landmark
- heading-order: headings skipping a level, such as h1 to h3
- link-name, button-name: a link or button with no accessible name
- html-has-lang: no language set on the html element

Narrowing what it checks:

```python
axe.run(page, options={"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa"]}})
```

Tags select groups of rules: wcag2a, wcag2aa, best-practice and others. The default includes best-practice rules, which is why the two landmark rules fire even on an otherwise clean page.


DEALING WITH AN APPLICATION THAT ALREADY HAS PROBLEMS

Adding axe to an existing application usually produces dozens of violations immediately. Asserting zero would mean a permanently red test, which helps nobody.

The practical approach is a known-issues list: accept today's problems, and fail on anything new.

```python
known = {"image-alt", "label", "color-contrast"}
unexpected = [
    violation["id"]
    for violation in results.response["violations"]
    if violation["id"] not in known
]
assert unexpected == [], f"new accessibility problems: {unexpected}"
```

The suite goes green today, and the moment someone introduces a new kind of problem, it fails. Meanwhile the known list is a backlog to work through, and it should shrink over time. Put a ticket number next to each entry.

A sharper version counts occurrences as well as kinds, so the number of violations can only go down. That is stricter and more work to maintain.


WHAT AUTOMATED CHECKS CANNOT DO

This is the most important part of the module.

Automated tools find roughly 30 to 40 per cent of accessibility problems. Published studies put axe in that range, and Deque says so itself. The rest need a person.

What a tool cannot judge:

- Whether alt text is useful. alt="image1" passes the rule and tells a screen reader user nothing.
- Whether a label makes sense. A field labelled "Field 3" has a label.
- Whether the reading order is logical when the page is linearised.
- Whether a keyboard user can complete a task, and whether focus goes somewhere sensible after opening a dialog.
- Whether error messages are announced.
- Whether the page works with a real screen reader, which is the only test that counts.
- Whether an animation causes problems for someone with vestibular disorders.

So automated checks are a floor, not a ceiling. They catch the mechanical mistakes cheaply and continuously, which frees a human review to look at the things only a human can judge.

Things worth testing that are not axe's job, and that Playwright does well:

- keyboard navigation: press Tab and check focus lands where it should
- focus after an action: a dialog opens, where does focus go?
- that every interactive element can be reached without a mouse

```python
page.keyboard.press("Tab")
expect(page.get_by_role("textbox", name="Email address")).to_be_focused()
```


THE FILES

- tests/test_13_visual_a11y.py - 8 tests
- __snapshots__/ - the reference images, committed
- requirements.txt - now includes pytest-playwright-visual-snapshot and axe-playwright-python

The pages are written in the test file. Both the accessible and inaccessible versions are wrapped in a main element, because without one axe reports landmark-one-main and region on every page, which would drown out the problems the tests are actually about.

ARIA snapshots:
- test_aria_snapshot_of_a_form - the expected structure of the accessible page
- test_aria_snapshot_catches_a_missing_label - the same check fails on the page whose input has no label, wrapped in pytest.raises because the failure is the point

Accessibility:
- test_axe_finds_problems - the deliberately broken page reports image-alt and label
- test_axe_passes_on_the_fixed_page - the corrected page has no violations
- test_axe_can_ignore_known_issues - the known-issues pattern

Visual:
- test_visual_page_snapshot - the whole page at a fixed viewport size
- test_visual_element_snapshot - one element only, the stable approach
- test_visual_with_a_tolerance - a threshold for harmless differences

A note on how this module was written: the first version of ACCESSIBLE_PAGE was not accessible. It looked correct, had alt text, a proper label and good contrast, and axe still found two violations: landmark-one-main and region. Neither had occurred to the author. That is the argument for running the tool rather than reviewing by eye, and it is exactly what happens on a real project.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Approving a reference image without looking at it.
--update-snapshots will happily record a broken layout as the new truth. Review the image, every time. This is the main way visual testing quietly stops working.

Trap 2 - References generated on the wrong platform.
A Mac reference will not match a Linux runner: different fonts, different text smoothing. Generate them where the tests run, usually in CI.

Trap 3 - Comparing whole pages by default.
Every change anywhere on the page fails the test. Compare components.

Trap 4 - Forgetting to commit the reference images.
__snapshots__/ belongs in the repository. Without it, CI has nothing to compare against and writes new references instead, so the test never fails.

Trap 5 - Screenshotting something that moves.
Animations, a blinking cursor, a clock. The test fails at random. Disable animations, fix the clock, mask what changes.

Trap 6 - A threshold so large it hides real changes.
A high tolerance makes the test green and useless. Start small, and prefer fixing the instability.

Trap 7 - Asserting zero violations on an existing application.
It will never be green, so it will be ignored or deleted. Use a known-issues list and shrink it.

Trap 8 - Believing a green axe run means the page is accessible.
Automated tools catch 30 to 40 per cent of problems. The rest need a person and a screen reader.

Trap 9 - Running axe without a report in the failure message.
assert results.violations_count == 0 alone tells you nothing. Pass generate_report() as the message.

Trap 10 - Best-practice rules surprising you.
axe's default set includes rules beyond WCAG, such as the landmark ones. Either satisfy them or select rules by tag, but decide deliberately rather than being puzzled.

Trap 11 - Treating an ARIA snapshot as a visual check.
It describes structure, not appearance. A page can match perfectly and look broken.

Trap 12 - Writing ARIA snapshots by hand.
Let the test fail and copy the actual structure from the error, after checking it is what you want.


HANDS-ON PRACTICE

1. Install the plugins:

```
pip install pytest-playwright-visual-snapshot axe-playwright-python
```

2. Create the reference images. This run reports the three visual tests as failures, which is correct:

```
pytest tests/test_13_visual_a11y.py --update-snapshots
```

3. Look at what it wrote, and open one:

```
ls -R __snapshots__
open "__snapshots__/test_13_visual_a11y/test_visual_element_snapshot/test_visual_element_snapshot[chromium][darwin].png"
```

   This is the approval step. The image should show the card exactly as it ought to look.

4. Run the tests properly:

```
pytest tests/test_13_visual_a11y.py -v
```

   Expect 8 passed. A plain "pytest" now runs 143 tests: 141 passed, 1 xfailed and 1 rerun.

5. Read a real accessibility report. Make the fixed page broken by removing the label line from ACCESSIBLE_PAGE, then run:

```
pytest tests/test_13_visual_a11y.py -k axe_passes
```

   The failure prints the full axe report: the rule, its impact, the help URL, and the element. Follow the URL to see Deque's explanation. Put the line back afterwards.

6. See a visual difference. Change the card's border in STABLE_PAGE from 2px to 6px and run:

```
pytest tests/test_13_visual_a11y.py -k visual_element
```

   The test fails, and the plugin writes a difference image showing what changed. Find it with ls test-results, open it, then change the border back.

If something is not installed:

If the error says "fixture 'assert_snapshot' not found", pytest-playwright-visual-snapshot is missing. If the axe tests are skipped, axe-playwright-python is missing. Both are community packages, not part of Playwright.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_13_visual_a11y.py, in ACCESSIBLE_PAGE, remove the alt attribute from the img tag.
2. Run:

```
pytest tests/test_13_visual_a11y.py -k "axe_passes or aria_snapshot_of"
```

3. Both fail, and the difference between them is the lesson. The axe test reports image-alt with an explanation and a help URL. The ARIA snapshot test fails because the image no longer has an accessible name, so it does not match the expected structure. Two tools, two angles, the same real problem.
4. Note what did not fail: the visual tests. The page looks identical, because a missing alt attribute is invisible. That is precisely why accessibility needs its own checks.
5. Put the alt attribute back and run again.


MENTAL MODEL

- Visual: does it look the same as the approved picture? Expensive to maintain, catches layout breakage.
- ARIA snapshot: does it have the same structure, in roles and names? Cheap, stable, catches semantic damage.
- axe: does it break known accessibility rules? Cheap, catches mechanical mistakes, covers about a third of real problems.
- Reference images are approvals: review them, commit them, generate them where the tests run.
- A green accessibility run is a floor, not a certificate.


FOR YOUR OWN APP LATER

- Add axe to a handful of key pages first: the login, the main screen, the busiest form. Record today's violations as a known-issues list and work the list down.
- Run axe on every page a test already visits, as an extra assertion. The cost is a second or two and it needs no new test.
- Keep visual tests for components, not pages, and generate the references in CI so they match.
- Test keyboard navigation explicitly on anything important: a user who cannot reach the Submit button cannot use the application, and no axe rule will tell you.
- Ask whether the organisation has an accessibility standard it must meet. If it does, the target is usually WCAG 2.1 AA, and that decides which axe tags to run.
- Arrange a real screen reader test, even once. VoiceOver is built into macOS. Half an hour with it teaches more than any rule list.
- Visual references in the repository are design decisions. Treat a changed image in a pull request as something to review, not to approve by habit.


QUIZ (answers below - try before peeking)

1. Why does the first run of a visual test fail, and why is that deliberate?

2. The reference image file name contains [chromium][darwin]. Why?

3. A visual test passes locally and fails on CI, on an unchanged page. What is the most likely cause?

4. Name three ways to make a visual test stable when part of the page legitimately changes.

5. What does an ARIA snapshot check that a screenshot comparison does not, and the other way round?

6. An application has 40 axe violations when you first run it. What do you assert?

7. The axe test is green. Is the page accessible?

8. Why does assert results.violations_count == 0, results.generate_report() have a second part?

9. The first ACCESSIBLE_PAGE in this module looked correct and still had two violations. Which, and what general point does that make?

10. A missing alt attribute breaks the axe test and the ARIA snapshot test, but not the visual test. Why not?

11. DevOps stretch question: how would you add visual testing to CI so the reference images actually match? (Just guess.)


ANSWERS


1. Because there is no reference image yet, so there is nothing to compare against. The plugin writes the image and fails, with a message telling you to review it.

Why that is deliberate: a reference image is an approval. It says "this is what the page should look like". If the tool created it silently and passed, the first run of a test on a broken page would quietly enshrine the breakage as correct, and the test would protect that broken state from then on.

Failing forces a human to look at the image before it becomes the truth. The same applies to --update-snapshots later: it is an approval step, not a way to make a red test green.

Common mistakes:
- Treating the first failure as a bug in the setup.
- Running --update-snapshots whenever a visual test fails, without opening the image (Trap 1).

See: VISUAL COMPARISON: HOW IT WORKS.


2. Because the same page renders differently in different browsers and on different operating systems, so each combination needs its own reference.

Why: text rendering differs between engines and between platforms, fonts available differ, and anti-aliasing differs. A reference captured in Chromium on macOS will not match Firefox, and will not match Chromium on Linux either. Keeping them in separate files means a test can run anywhere, comparing against the right reference.

The practical consequence is that references generated on your Mac are useless to a Linux CI runner, which is the subject of question 3.

Common mistakes:
- Assuming one reference per test is enough.

See: VISUAL COMPARISON: HOW IT WORKS, and Trap 2.


3. The reference was generated on a different platform. CI runs Linux, with different fonts and different text rendering, so the pixels differ even though nothing about the page changed.

Why fonts specifically: a font available on macOS may not exist on a bare Linux runner, so the browser substitutes another. Every line of text then has slightly different widths, which shifts the layout, and the comparison fails everywhere at once. Even the same font renders differently because macOS and Linux smooth text differently.

The fix is to generate the references in the same environment that runs the tests: on CI, or in the Docker image CI uses, and commit those. Some teams run visual tests only in a container, for exactly this reason.

Other possibilities, if the platform already matches: a different viewport size, a slower machine capturing the screenshot mid-animation, or content that differs between environments.

Common mistakes:
- Raising the threshold until CI goes green. That hides real changes too (Trap 6).

See: WHY VISUAL TESTS GO WRONG, and Trap 2.


4. Any three of: mask the changing elements, compare a smaller element instead of the page, fix the clock, use fixed test data, disable animations, block external content, or allow a small threshold.

Masking is the most direct when one part changes:

```python
page.screenshot(mask=[page.get_by_test_id("last-updated")])
```

Playwright paints a solid box over those elements before comparing, so whatever they contain is ignored while everything around them is still checked.

Comparing an element rather than the page is the most effective in general, because it removes most of the surface area where something could differ.

Disabling animations:

```python
page.add_style_tag(content="*, *::before, *::after { animation: none !important; transition: none !important; }")
```

Fixing the clock is Module 10: page.clock.set_fixed_time(...) so a date on the page never changes.

Common mistakes:
- Reaching for a large threshold first. It is the least precise option: it weakens the whole image rather than excluding the part that legitimately varies.

See: WHY VISUAL TESTS GO WRONG.


5. An ARIA snapshot checks structure: roles, accessible names and nesting. A screenshot checks appearance. Each is blind to the other.

Examples of the difference:

- A heading restyled as a div with large bold text: the screenshot is identical, and the ARIA snapshot fails, because the heading role is gone. Screen reader users lose the ability to navigate by heading.
- A button's colour changed: the screenshot fails, and the ARIA snapshot is unchanged, because the role and name are the same.

That is why both exist. The ARIA snapshot is also much more stable, since restyling does not affect it, which makes it cheap to keep.

Common mistakes:
- Expecting an ARIA snapshot to catch a layout problem (Trap 11).

See: ARIA SNAPSHOTS, and THREE DIFFERENT CHECKS.


6. Not zero. Record the 40 as a known-issues list and assert that nothing new appears:

```python
known = {"image-alt", "label", "color-contrast"}
unexpected = [v["id"] for v in results.response["violations"] if v["id"] not in known]
assert unexpected == [], f"new accessibility problems: {unexpected}"
```

Why: a test that can never pass gets ignored, then disabled, then deleted. Asserting zero on an application with existing problems guarantees that outcome. The known-issues list makes the suite green today while catching the next new problem immediately, which is the thing a test can actually do.

The list is also a backlog. Put a ticket number against each entry, and remove entries as they are fixed, so the test gets stricter over time rather than being a permanent excuse.

A stronger variant records counts as well as kinds, so the number of violations can only decrease.

Common mistakes:
- Fixing the 40 problems first and adding the test afterwards. The test comes first, so number 41 never arrives.

See: DEALING WITH AN APPLICATION THAT ALREADY HAS PROBLEMS, and Trap 7.


7. No. It means the page passes the rules a tool can check automatically, which is roughly 30 to 40 per cent of real accessibility problems.

What a green run does not tell you: whether the alt text is meaningful, whether labels make sense, whether the reading order is logical, whether a keyboard user can finish a task, whether focus goes somewhere sensible when a dialog opens, whether errors are announced, or whether any of it works with a real screen reader.

alt="image1" passes image-alt. A field labelled "Field 3" passes label. Both are useless to the person the rule exists for.

So the value of automated checks is that they catch mechanical mistakes cheaply, on every run, for ever, which frees human review to look at the things only a human can judge. They are a floor, not a certificate.

Common mistakes:
- Reporting "accessibility: passing" on the strength of an axe run. That is a claim the tool cannot support.

See: WHAT AUTOMATED CHECKS CANNOT DO, and Trap 8.


8. Because the second argument is the message printed when the assertion fails, so the failure shows the full axe report instead of just "2 != 0".

Why it matters: without it, the output tells you how many rules were broken and nothing about which. With it, you get the rule name, the impact level, the Deque help URL explaining the problem and how to fix it, and the exact elements affected. That is the difference between a failure you can act on and one you have to investigate from scratch.

```python
assert results.violations_count == 0, results.generate_report()
```

This matters most on CI, where you cannot rerun it interactively: the log has to contain everything you need.

Common mistakes:
- Printing the report instead. With -n (Module 09) output from workers is swallowed, and in a failure report the assertion message is what survives.

See: AXE, and Trap 9.


9. landmark-one-main and region: the page had no main element, so it had no main landmark and its content was not inside any landmark.

The general point: the author checked the obvious things, alt text, a label, contrast, and believed the page was accessible. The tool found two real problems that had not occurred to them. Neither is visible, neither affects how the page looks, and both affect how someone navigating by landmarks experiences it.

That is what axe is for. It encodes a large body of accessibility knowledge that no individual holds in their head, and applies it consistently to every page, every time.

It is also why both pages in the module are wrapped in main: without it, every page triggers these two rules, which drowns out the problems the tests are meant to demonstrate. On a real application, those rules are worth satisfying rather than silencing, because landmarks are genuinely how screen reader users navigate.

Common mistakes:
- Assuming your own review is thorough enough. This module is a worked example of it not being.

See: THE FILES, and Trap 10.


10. Because an alt attribute is invisible. It is read by screen readers and never displayed, so removing it changes nothing about the pixels.

Why this is the clearest argument in the module: the visual test is working perfectly and correctly reports no change, because there is no visual change. The page is nonetheless broken for anyone who cannot see it, and only the accessibility checks notice.

It generalises: every accessibility problem that lives in the markup rather than the rendering is invisible to visual testing. Missing labels, wrong roles, incorrect heading levels, missing landmarks, inaccessible names. None of them change a single pixel.

Common mistakes:
- Assuming a screenshot covers "how the page looks to users". It covers how it looks to users who look.

See: the break-it-on-purpose step, and THREE DIFFERENT CHECKS.


11. Generate the reference images on CI, in the same environment the tests run in, and commit them. The usual approach is a container: run the tests in Playwright's official Docker image both when creating the references and when comparing.

Why: the platform must match, or every comparison fails for reasons that have nothing to do with the page (question 3). Pinning the environment with a container goes further than just "generate on Linux": it pins the exact font set and browser build, so the rendering is identical run after run.

A workable arrangement:

- Run visual tests only in the container, locally and on CI, so everyone sees the same pixels.
- When a change is intended, run the update inside the container and commit the new images.
- Review changed images in the pull request. GitHub shows image diffs side by side, which makes the approval a real one.
- Upload the difference images as artifacts on failure (Module 12), so a CI failure can be understood without reproducing it.

Some teams avoid the problem entirely by using a hosted service that renders the comparison on its own infrastructure and provides an approval interface.

Common mistakes:
- Committing references from a laptop and then adding a large threshold so CI passes. That is two mistakes reinforcing each other (Traps 2 and 6).

See: WHY VISUAL TESTS GO WRONG, Trap 2, and Module 12.
