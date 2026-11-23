PLAYWRIGHT WITH PYTHON - MODULE 06: COMPLEX INTERACTIONS


GOAL

Handle the four things that are outside the normal page: content inside an iframe, a new tab or popup window, files going in and out of the browser, and the browser's own dialog boxes. Each one needs its own method, and each one catches people out in the same way.

By the end of this module you can:

- reach elements inside an iframe with frame_locator, including nested frames
- work with a popup or new tab, and go back to the first page
- upload files, including files the test creates itself
- wait for a download, read it and save it
- handle alert, confirm and prompt dialogs, and read what they said

Practice: every page in this module is built in the test file with page.set_content(), so these tests need no internet and cannot break when someone else's demo site changes.


WHY THESE FOUR ARE DIFFERENT

Everything so far has been inside one page. These four are not:

- An iframe is a whole separate document embedded in the page. page.get_by_role() searches the outer document only, so it cannot see inside.
- A popup or new tab is a different Page object. Clicking a link that opens one does not change the page your test is holding.
- A file upload or download crosses the line between the browser and your computer's file system.
- A dialog is drawn by the browser itself, not by the page, so it has no HTML and no locator.

Each needs a method that crosses that boundary. Once you know which one, they are all straightforward.


IFRAMES: FRAME_LOCATOR

An iframe (inline frame) embeds another page inside the current one. Payment forms, maps, video players, rich text editors and embedded dashboards are usually iframes.

```python
frame = page.frame_locator("iframe[name='inner']")
frame.get_by_label("Message").fill("hello")
frame.get_by_role("button", name="Save").click()
expect(frame.get_by_text("saved")).to_be_visible()
```

frame_locator takes a locator for the iframe element itself, then everything chained onto it is searched inside that frame. It behaves exactly like a normal locator: lazy, strict, and it waits.

Ways to point at the iframe:

```python
page.frame_locator("iframe[name='inner']")        # by attribute
page.frame_locator("#payment-frame")              # by id
page.frame_locator("iframe")                      # only if there is exactly one
page.get_by_title("Inner frame").content_frame    # from any locator for the iframe
```

Nested frames: chain frame_locator calls, outermost first.

```python
deep = page.frame_locator("iframe[name='outer']").frame_locator("iframe[name='deep']")
```

The outer page cannot see inside. This is the thing to remember: if an element is in a frame, page.get_by_...() finds nothing, however obvious the element looks on screen. test_page_cannot_see_inside_a_frame shows exactly that.

How to tell whether something is in an iframe: right-click it in the browser, choose Inspect, and look upwards in the HTML. If you pass an iframe tag on the way to the top, it is in a frame.

There is also an older API, page.frame(name="inner"), which returns a Frame object. frame_locator is the modern one and waits properly, so prefer it.


POPUPS AND NEW TABS

A link with target="_blank", or JavaScript calling window.open, opens a new tab or window. In Playwright that is a new Page object, and your test keeps hold of the old one.

```python
with page.expect_popup() as popup_info:
    page.get_by_role("link", name="Open popup").click()
popup = popup_info.value

expect(popup.get_by_role("heading", name="Popup page")).to_be_visible()
popup.close()
```

The pattern is: start listening, do the thing that opens the popup, then take the new page from popup_info.value.

The order matters, for the same reason as console messages in Module 04. The popup appears the moment the link is clicked, so the listening has to start first. Clicking before the with block means waiting for a popup that has already opened.

popup is a full Page object with everything you know: goto, get_by_role, click, expect. The original page is still usable, and both exist at the same time:

```python
assert page.context.pages == [page, popup]
```

page.context is the browser context (the private window all these pages share), and .pages lists every open page in it.

Closing: popup.close() closes the popup. You do not have to, because the context is thrown away at the end of the test, but closing makes the test clearer.

Related waits, all used the same way:

```python
with page.expect_navigation():  ...     # the page navigates somewhere
with page.expect_download():    ...     # a download starts
with page.expect_file_chooser(): ...    # the file picker opens
with page.expect_event("dialog"): ...   # any named event
```


FILE UPLOADS

Clicking a file input opens the operating system's file picker, which is not part of the page and cannot be automated. Playwright skips it: you give the files straight to the input element.

```python
page.get_by_label("Upload one").set_input_files("cv.pdf")
page.get_by_label("Upload many").set_input_files(["one.txt", "two.txt"])
page.get_by_label("Upload one").set_input_files([])          # clear the selection
```

This fires the change event, so the page reacts exactly as if a person had chosen the files.

Creating the file in the test, with pytest's tmp_path fixture:

```python
def test_upload_one_file(page: Page, tmp_path):
    cv = tmp_path / "cv.txt"
    cv.write_text("my experience")
    page.get_by_label("Upload one").set_input_files(cv)
```

tmp_path is a fresh empty folder that pytest creates for each test and cleans up afterwards. Ask for it by name in the test's arguments, like page. It is the right way to make test files: nothing is left in your repo, and the test does not depend on a file someone must remember to keep.

Without touching the disk at all:

```python
page.get_by_label("Upload one").set_input_files(
    {"name": "note.txt", "mimeType": "text/plain", "buffer": b"made up in the test"}
)
```

buffer takes raw bytes (the b in front of the text means bytes, not characters). Useful for a quick CSV or text file, and it is the fastest option because nothing is written to disk.

If the page has no file input, and instead opens the picker from a button:

```python
with page.expect_file_chooser() as chooser_info:
    page.get_by_role("button", name="Attach").click()
chooser_info.value.set_files("cv.pdf")
```


DOWNLOADS

A download also leaves the page, so it needs the wait-for-event pattern:

```python
with page.expect_download() as download_info:
    page.get_by_role("link", name="Download report").click()
download = download_info.value

assert download.suggested_filename == "report.txt"
download.save_as(tmp_path / download.suggested_filename)
```

What you get from a Download object:

- suggested_filename - the name the server or the page suggested
- save_as(path) - save it where you want, which is the normal thing to do
- path() - where Playwright put it temporarily
- failure() - None if it worked, or the reason it did not
- cancel() - stop it
- url - where it came from

Playwright saves downloads to a temporary place and deletes them when the browser context closes, so save_as is what keeps a file beyond the test.

Checking the contents is the point of most download tests:

```python
saved = tmp_path / download.suggested_filename
download.save_as(saved)
assert saved.read_text() == "hello from the download"
```

For a CSV or an Excel export, read the saved file and check a few rows. A test that only checks the file exists is weak: an empty or broken file would pass.


BROWSER DIALOGS: ALERT, CONFIRM, PROMPT

These three come from the browser, not the page:

- alert("message") - one OK button
- confirm("message") - OK and Cancel, and the page gets True or False
- prompt("question") - a text box, and the page gets the text or None

They have no HTML, so there is no locator for them. Playwright gives you a Dialog object instead.

By default, Playwright dismisses every dialog automatically. That is the opposite of a browser with a person at it, where everything stops until someone clicks. The reason is practical: an unhandled dialog would block the page forever and every later action would time out.

Automatic dismissal means:

- alert: the message is gone, the test carries on. Nothing to do.
- confirm: the page is told Cancel.
- prompt: the page is told the user cancelled.

To choose what happens, handle the dialog yourself:

```python
page.once("dialog", lambda dialog: dialog.accept())           # click OK, this time only
page.once("dialog", lambda dialog: dialog.dismiss())          # click Cancel
page.once("dialog", lambda dialog: dialog.accept("Alice"))    # type into a prompt, then OK
page.on("dialog", lambda dialog: dialog.accept())             # every dialog from now on
```

Register the handler before the click that triggers the dialog.

once handles the next dialog only. on handles every dialog until you remove it. Prefer once: a handler that accepts everything can hide a second, unexpected dialog.

Important: once you register any handler, the automatic dismissal stops. Your handler must call accept() or dismiss(), or the page freezes and the next action times out.

To read the message, record it in the handler and answer in the same handler:

```python
seen = []

def handle(dialog):
    seen.append((dialog.type, dialog.message))
    dialog.dismiss()

page.once("dialog", handle)
page.get_by_role("button", name="Show alert").click()
assert seen == [("alert", "something happened")]

A Dialog has: type (alert, confirm, prompt or beforeunload), message, default_value (for a prompt), accept(text) and dismiss().

Many apps do not use these at all. A "Are you sure?" box built out of HTML is just elements, so find and click its buttons normally. If no dialog event ever arrives, that is what you are looking at.


THE FILES

- tests/test_06_complex_interactions.py - 16 tests

The pages are written as text at the top of the file and loaded with set_content(). The iframe pages use a data: URL, which puts HTML straight into the frame without needing a second file or a server.

Iframes:
- test_frame_locator_finds_elements_inside - reads a heading and fills a field inside the frame
- test_page_cannot_see_inside_a_frame - the outer heading is found, the inner one is not
- test_action_inside_a_frame - clicks a button in the frame and checks what it changed, also in the frame
- test_nested_frames - reaches a frame inside a frame by chaining

Popups:
- test_popup_opens_in_a_new_page - opens it, reads it, closes it
- test_original_page_still_works_after_popup - both pages exist at once, then one again

Uploads:
- test_upload_one_file - a file created with tmp_path
- test_upload_several_files - two files at once
- test_upload_from_memory - no file on disk at all
- test_clear_a_file_input - set_input_files([]) empties the selection

Downloads:
- test_download_a_file - waits for it, checks the suggested name, saves it, reads the contents

Dialogs:
- test_alert_is_dismissed_automatically - no handler, and the test carries on
- test_read_the_dialog_message - reads the type and the message
- test_accept_a_confirm and test_dismiss_a_confirm - the page records which button was used
- test_answer_a_prompt - types a name into the prompt


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Looking for an element that is inside an iframe.
page.get_by_role() searches the outer document only, so it finds nothing and the test times out, even though the element is plainly on screen. Inspect the element and look for an iframe above it.

Trap 2 - Chaining frames in the wrong order.
Nested frames must be chained from the outside in. Starting with the inner frame finds nothing, because that iframe element is not in the outer document.

Trap 3 - Clicking before the with block.
A popup, download or dialog that has already happened cannot be caught. The with page.expect_...() block must contain the click that causes it.

Trap 4 - Carrying on with the old page after a popup opens.
The test still holds the original page. Actions go to the wrong tab, and the locators find nothing. Use the page from popup_info.value.

Trap 5 - Clicking the file input.
That opens the operating system's file picker, which Playwright cannot touch, and the test hangs until it times out. Use set_input_files on the input element.

Trap 6 - Hard-coding a file path for an upload.
"/Users/me/Desktop/cv.pdf" works on your computer and nowhere else, and it puts your username in the repo. Create the file with tmp_path, or use a buffer.

Trap 7 - Forgetting save_as on a download.
Playwright stores the file temporarily and deletes it when the context closes. Without save_as, the file is gone after the test.

Trap 8 - Only checking that a download exists.
An empty or corrupt file still exists. Save it and check the contents.

Trap 9 - A dialog handler that neither accepts nor dismisses.
Registering a handler switches off the automatic dismissal. If the handler does nothing, the dialog stays open, the page is blocked, and every later action times out.

Trap 10 - page.on instead of page.once.
A permanent handler that accepts everything also accepts dialogs you did not expect, including ones that should have failed the test. Use once unless you really mean every dialog.

Trap 11 - Expecting a locator for an alert.
Browser dialogs have no HTML. If you can Inspect the box, it is built from page elements and should be clicked normally. If you cannot, it is a browser dialog and needs the dialog API.


HANDS-ON PRACTICE

1. Run the Module 06 tests:

```
pytest tests/test_06_complex_interactions.py -v
```

   Expect 16 passed. A plain "pytest" now runs 53 tests: 2 from Module 01, 7 from Module 02, 8 from Module 03, 6 from Module 04, 14 from Module 05 and 16 from Module 06.

2. Watch the popup and the dialogs:

```
pytest tests/test_06_complex_interactions.py --headed --slowmo 600 -k "popup or confirm or prompt"
```

   You see the second tab open and close, and the dialog boxes appear and get answered.

3. See the automatic dismissal for yourself. Run the alert test headed and watch closely:

```
pytest tests/test_06_complex_interactions.py --headed --slowmo 1000 -k alert_is_dismissed
```

   The alert appears and vanishes without anyone clicking, because no handler was registered.

These tests use only local pages, so none of them depends on a website. If one fails, the cause is in the test file itself.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_06_complex_interactions.py, find test_frame_locator_finds_elements_inside and change
   frame = page.frame_locator("iframe[name='inner']")
   to
   frame = page
   To find the line: grep -n "def test_frame_locator_finds_elements_inside" tests/test_06_complex_interactions.py
2. Run:

```
pytest tests/test_06_complex_interactions.py -v -k frame_locator_finds
```

3. The test fails after 5 seconds on the heading assertion. The locator now searches the outer page, which does not contain anything from the frame. The error shows it waited for get_by_role("heading", name="Inner page") and found nothing. That is exactly what Trap 1 looks like in practice.
4. Change it back and run again. It passes.


MENTAL MODEL

- Inside a frame: page.frame_locator(...) first, then everything else chained onto it.
- Something that leaves the page (popup, download, dialog): start listening, then do the thing, inside a with block.
- Files in: set_input_files, never a click.
- Files out: expect_download, then save_as, then read it.
- Dialogs: dismissed automatically unless you handle them, and a handler must accept or dismiss.


FOR YOUR OWN APP LATER

- Payment forms, embedded reports and rich text editors are usually iframes. If a locator "cannot find" something you can see, check for one first.
- Export buttons (CSV, PDF, Excel) are worth a real test: download, save and check a couple of values inside the file.
- Import screens take the upload pattern. Create the file in the test with tmp_path, so no sample file has to live in the repo.
- Links that open in a new tab are easy to get wrong in an app. A popup test is a cheap way to catch a broken target.
- Most modern apps use their own HTML dialogs rather than browser ones. Inspect first, then choose the approach.
- A delete confirmation is worth testing both ways: accepted, and dismissed with nothing deleted.


QUIZ (answers below - try before peeking)

1. A Save button is clearly visible on the page, but page.get_by_role("button", name="Save").click() times out. Inspect shows an iframe above the button in the HTML. Write the line that clicks it.

2. A page has an iframe called "outer", and inside that another called "deep". Write the locator that reaches an element in the deep frame.

3. What is wrong with this code, and what happens when it runs?

   page.get_by_role("link", name="Open report").click()
   with page.expect_popup() as popup_info:
       pass

4. After a popup opens, your test keeps using page and every locator times out. Why, and what should it use?

5. Why does a test never click a file input, and what does it do instead?

6. A test needs to upload a CSV file. Give two ways to produce that file without storing one in the repo.

7. A download test ends with assert download.suggested_filename == "report.csv" and nothing else. Why is that a weak test, and what would you add?

8. By default, what does Playwright do when a page shows a confirm dialog, and what does the page receive as the answer?

9. You register page.once("dialog", lambda dialog: print(dialog.message)) and then click a button that shows an alert. The next action in the test times out. Why?

10. DevOps stretch question: a test downloads a file and checks its contents. It passes on your computer but fails on a CI machine. What is the most likely cause? (Just guess.)


ANSWERS


1. page.frame_locator("iframe[...]").get_by_role("button", name="Save").click()

Fill in the iframe's own locator from what Inspect shows, for example page.frame_locator("#payment-frame") or page.frame_locator("iframe[name='inner']").

Why: an iframe is a separate document embedded in the page. page.get_by_role() searches the outer document only, so the button is genuinely not there as far as that locator is concerned, however clearly you can see it. frame_locator crosses into the frame, and everything chained onto it is searched inside.

The clue in the error is a timeout with "waiting for get_by_role(...)" on an element you can see on screen. Whenever that happens, Inspect the element and look upwards in the HTML for an iframe tag.

Common mistakes:
- Adding a longer timeout. The element will never be found in the outer document, so more time changes nothing.
- Using force=True. The element is not covered, it is in a different document.

See: IFRAMES: FRAME_LOCATOR, and Trap 1.


2. page.frame_locator("iframe[name='outer']").frame_locator("iframe[name='deep']").get_by_...

Why: each frame_locator moves one level inwards. The outer iframe element lives in the main document, so it is found with page.frame_locator(). The deep iframe element lives inside the outer frame, so it can only be found from there.

Starting with the deep frame does not work: page.frame_locator("iframe[name='deep']") searches the main document, which has no such element.

Common mistakes:
- Chaining from the inside out, which finds nothing.
- Trying to shortcut with a CSS selector such as "iframe iframe". CSS cannot see across document boundaries either.

See: IFRAMES: FRAME_LOCATOR, and Trap 2.


3. The click happens before the listening starts, so the with block waits for a popup that has already opened and fails after the timeout.

Why: expect_popup starts listening when the with block is entered. A popup that opened a moment earlier was never seen. It is the same ordering rule as console messages in Module 04: listen, act, wait.

The correct form puts the click inside the block:

```python
with page.expect_popup() as popup_info:
    page.get_by_role("link", name="Open report").click()
popup = popup_info.value
```

Common mistakes:
- Thinking the with block somehow looks backwards for recent popups. It does not: events are only caught while something is listening.

See: POPUPS AND NEW TABS, and Trap 3.


4. Because the popup is a different Page object, and page still points at the original tab. The test should use the page from popup_info.value.

Why: opening a new tab does not change the page your test is holding. Playwright does not switch focus the way a person would. Everything you do with page still goes to the first tab, where the popup's content does not exist, so locators time out.

```python
with page.expect_popup() as popup_info:
    page.get_by_role("link", name="Open report").click()
popup = popup_info.value          # the new tab
popup.get_by_role("heading").click()
```

Both pages stay usable, and page.context.pages lists them all. Work with whichever one you mean.

Common mistakes:
- Looking for a "switch to tab" call. There is none, because you already have both page objects.

See: POPUPS AND NEW TABS, and Trap 4.


5. Clicking it opens the operating system's file picker, which is not part of the page and cannot be automated, so the test hangs until it times out. Instead, give the files straight to the input element with set_input_files.

Why: the file picker is a window belonging to macOS or Windows, not HTML. Playwright controls the browser, not the desktop, so there is nothing for it to click. set_input_files sets the input's files directly and fires the change event, so the page reacts exactly as if someone had chosen them.

```python
page.get_by_label("Upload one").set_input_files(cv)
```

If the page has no visible file input and opens the picker from a button, use expect_file_chooser, which catches the request before the operating system window appears.

Common mistakes:
- Typing the path into the input with fill. A file input's value cannot be set as text, for security reasons.

See: FILE UPLOADS, and Trap 5.


6. Create it with tmp_path, or pass it from memory with a buffer.

With tmp_path, pytest's temporary folder:

```python
def test_import(page: Page, tmp_path):
    csv = tmp_path / "people.csv"
    csv.write_text("name,role\nAlice,admin\n")
    page.get_by_label("Import").set_input_files(csv)
```

From memory, with no file written at all:

```python
page.get_by_label("Import").set_input_files(
    {"name": "people.csv", "mimeType": "text/csv", "buffer": b"name,role\nAlice,admin\n"}
)
```

Why either is better than a committed sample file: the test is self-contained, the data is visible right there in the test, nothing is left in the repo, and there is no file for someone to delete or change by accident. The buffer version is fastest because nothing touches the disk.

A real sample file in the repo is still reasonable when the format is complex and hard to generate, such as a particular Excel or PDF file.

Common mistakes:
- A path from your own computer, which works nowhere else and puts your username in a public repo (Trap 6).

See: FILE UPLOADS.


7. Because a file can have the right name and still be empty or corrupt. Save it and check what is inside.

Why: suggested_filename only tells you what the server called the file. It says nothing about whether the export worked. A broken export that produces a zero-byte report.csv passes that assertion. That is a false negative: the test is green while the feature is broken.

```python
saved = tmp_path / download.suggested_filename
download.save_as(saved)
text = saved.read_text()
assert "Alice" in text
assert len(text.splitlines()) == 4
```

For a real export, check a couple of values you know should be there, and the number of rows. That is what makes the test worth having.

Common mistakes:
- Checking only that the file exists, which is the same weakness.
- Forgetting save_as. Playwright deletes its temporary copy when the context closes, so there is nothing to read afterwards (Trap 7).

See: DOWNLOADS, and Trap 8.


8. Playwright dismisses it automatically, so the page receives False, as if the user had clicked Cancel.

Why: a dialog blocks the page completely. With nobody there to click, an unhandled dialog would freeze the test and every following action would time out. Dismissing is the safe default.

That default often matters more than people expect. A delete confirmation that is dismissed means nothing is deleted, so a test that clicks Delete and then checks the row is gone will fail, correctly, for a reason that is easy to misread.

To choose the answer, register a handler before the click:

```python
page.once("dialog", lambda dialog: dialog.accept())    # OK
page.once("dialog", lambda dialog: dialog.dismiss())   # Cancel
```

Common mistakes:
- Assuming the default is to accept. It is the opposite.
- Expecting to find the dialog with a locator. It has no HTML (Trap 11).

See: BROWSER DIALOGS, and Trap 9.


9. Because registering a handler switches off the automatic dismissal, and this handler only prints the message. It never calls accept() or dismiss(), so the dialog stays open, the page is blocked, and the next action times out.

Why: Playwright assumes that if you registered a handler, you are taking responsibility for answering. Printing is not answering.

The fix is to answer as well as read:

```python
page.once("dialog", lambda dialog: (print(dialog.message), dialog.accept()))
```

Or, more readably, use the wait-for-event pattern, which reads the dialog and still answers it:

```python
with page.expect_event("dialog") as dialog_info:
    page.get_by_role("button", name="Show alert").click()
print(dialog_info.value.message)
```

Common mistakes:
- Blaming the click or the locator. The timeout is on the action after the dialog, because the page is frozen.

See: BROWSER DIALOGS, and Trap 9.


10. The most likely cause is a path or folder that exists on your computer but not on the CI machine, for example save_as("/Users/me/Downloads/report.csv") or a folder the test expects to be there.

Why: a CI machine is a fresh Linux computer with none of your folders, a different user name and a different path style. Anything hard-coded to your own machine fails there. tmp_path avoids this completely, because pytest creates the folder on whatever machine is running.

Other possibilities worth checking, in a trace from the failing run:
- The download never started, because the button or link differs in that browser.
- The file contents differ: a report with a date or a user name in it, which is not the same on CI.
- Line endings, if the test compares text exactly and the file is produced on a different system.

How to investigate: run CI with --tracing retain-on-failure (Module 04), upload test-results as an artifact, and look at the failing step.

Common mistakes:
- Raising timeouts. A missing folder is not a timing problem.

See: FILE UPLOADS, DOWNLOADS, Trap 6, and Module 12 for CI.


End of Module 06. Next up: Module 07, fixtures, the Page Object Model and device emulation.