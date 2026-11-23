"""Module 06 - Complex interactions: iframes, popups, uploads, downloads, dialogs.

Every page here is built in the test with page.set_content(), so these tests
need no internet and cannot break when a demo site changes.
Run from the repo root with the venv active:
    pytest tests/test_06_complex_interactions.py -v
"""
from playwright.sync_api import Page, expect

# An iframe whose content is written inline with a data: URL.
IFRAME_PAGE = """
<h1>Outer page</h1>
<iframe name="inner" title="Inner frame" src="data:text/html,
  <h2>Inner page</h2>
  <label for='msg'>Message</label>
  <input id='msg'>
  <button onclick=&quot;document.querySelector('%23out').textContent = 'saved'&quot;>Save</button>
  <div id='out'></div>
"></iframe>
"""

NESTED_IFRAME_PAGE = """
<iframe name="outer" src="data:text/html,
  <iframe name='deep' src=&quot;data:text/html,<p id='deep-text'>deep content</p>&quot;></iframe>
"></iframe>
"""

# The button opens a blank popup. Chromium blocks links that navigate
# straight to a data: URL, so the test fills the popup in afterwards.
POPUP_PAGE = """
<button onclick="window.open('', '_blank')">Open popup</button>
"""

UPLOAD_PAGE = """
<input type="file" id="single">
<label for="single">Upload one</label>
<input type="file" id="many" multiple>
<label for="many">Upload many</label>
<div data-testid="names"></div>
<script>
  for (const input of document.querySelectorAll("input[type=file]")) {
    input.onchange = () => {
      document.querySelector("[data-testid=names]").textContent =
        Array.from(input.files).map(f => f.name).join(", ");
    };
  }
</script>
"""

DOWNLOAD_PAGE = """
<a id="dl" download="report.txt"
   href="data:text/plain;charset=utf-8,hello%20from%20the%20download">Download report</a>
"""

DIALOG_PAGE = """
<button id="alert" onclick="alert('something happened')">Show alert</button>
<button id="confirm" onclick="document.querySelector('[data-testid=out]').textContent =
  confirm('Are you sure?') ? 'accepted' : 'dismissed'">Show confirm</button>
<button id="prompt" onclick="document.querySelector('[data-testid=out]').textContent =
  prompt('Your name?') || 'nothing'">Show prompt</button>
<div data-testid="out"></div>
"""


# ---------- IFRAMES ----------

def test_frame_locator_finds_elements_inside(page: Page):
    page.set_content(IFRAME_PAGE)
    frame = page.frame_locator("iframe[name='inner']")
    expect(frame.get_by_role("heading", name="Inner page")).to_be_visible()
    frame.get_by_label("Message").fill("hello")
    expect(frame.get_by_label("Message")).to_have_value("hello")


def test_page_cannot_see_inside_a_frame(page: Page):
    page.set_content(IFRAME_PAGE)
    expect(page.get_by_role("heading", name="Outer page")).to_be_visible()
    assert page.get_by_role("heading", name="Inner page").count() == 0


def test_action_inside_a_frame(page: Page):
    page.set_content(IFRAME_PAGE)
    frame = page.frame_locator("iframe[name='inner']")
    frame.get_by_role("button", name="Save").click()
    expect(frame.locator("#out")).to_have_text("saved")


def test_nested_frames(page: Page):
    page.set_content(NESTED_IFRAME_PAGE)
    deep = page.frame_locator("iframe[name='outer']").frame_locator("iframe[name='deep']")
    expect(deep.locator("#deep-text")).to_have_text("deep content")


# ---------- POPUPS AND NEW TABS ----------

def test_popup_opens_in_a_new_page(page: Page):
    page.set_content(POPUP_PAGE)
    with page.expect_popup() as popup_info:
        page.get_by_role("button", name="Open popup").click()
    popup = popup_info.value
    popup.set_content("<h1>Popup page</h1>")
    expect(popup.get_by_role("heading", name="Popup page")).to_be_visible()
    popup.close()
    expect(page.get_by_role("button", name="Open popup")).to_be_visible()


def test_original_page_still_works_after_popup(page: Page):
    page.set_content(POPUP_PAGE)
    with page.expect_popup() as popup_info:
        page.get_by_role("button", name="Open popup").click()
    popup = popup_info.value
    assert page.context.pages == [page, popup]
    popup.close()
    assert page.context.pages == [page]


# ---------- FILE UPLOADS ----------

def test_upload_one_file(page: Page, tmp_path):
    cv = tmp_path / "cv.txt"
    cv.write_text("my experience")
    page.set_content(UPLOAD_PAGE)
    page.get_by_label("Upload one").set_input_files(cv)
    expect(page.get_by_test_id("names")).to_have_text("cv.txt")


def test_upload_several_files(page: Page, tmp_path):
    first = tmp_path / "one.txt"
    second = tmp_path / "two.txt"
    first.write_text("1")
    second.write_text("2")
    page.set_content(UPLOAD_PAGE)
    page.get_by_label("Upload many").set_input_files([first, second])
    expect(page.get_by_test_id("names")).to_have_text("one.txt, two.txt")


def test_upload_from_memory(page: Page):
    page.set_content(UPLOAD_PAGE)
    page.get_by_label("Upload one").set_input_files(
        {"name": "note.txt", "mimeType": "text/plain", "buffer": b"made up in the test"}
    )
    expect(page.get_by_test_id("names")).to_have_text("note.txt")


def test_clear_a_file_input(page: Page, tmp_path):
    cv = tmp_path / "cv.txt"
    cv.write_text("my experience")
    page.set_content(UPLOAD_PAGE)
    upload = page.get_by_label("Upload one")
    upload.set_input_files(cv)
    expect(page.get_by_test_id("names")).to_have_text("cv.txt")
    upload.set_input_files([])
    expect(page.get_by_test_id("names")).to_be_empty()


# ---------- DOWNLOADS ----------

def test_download_a_file(page: Page, tmp_path):
    page.set_content(DOWNLOAD_PAGE)
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Download report").click()
    download = download_info.value
    assert download.suggested_filename == "report.txt"
    saved = tmp_path / download.suggested_filename
    download.save_as(saved)
    assert saved.read_text() == "hello from the download"


# ---------- BROWSER DIALOGS ----------

def test_alert_is_dismissed_automatically(page: Page):
    page.set_content(DIALOG_PAGE)
    page.get_by_role("button", name="Show alert").click()
    expect(page.get_by_role("button", name="Show alert")).to_be_visible()


def test_read_the_dialog_message(page: Page):
    page.set_content(DIALOG_PAGE)
    seen = []

    def handle(dialog):
        seen.append((dialog.type, dialog.message))
        dialog.dismiss()

    page.once("dialog", handle)
    page.get_by_role("button", name="Show alert").click()
    assert seen == [("alert", "something happened")]


def test_accept_a_confirm(page: Page):
    page.set_content(DIALOG_PAGE)
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Show confirm").click()
    expect(page.get_by_test_id("out")).to_have_text("accepted")


def test_dismiss_a_confirm(page: Page):
    page.set_content(DIALOG_PAGE)
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Show confirm").click()
    expect(page.get_by_test_id("out")).to_have_text("dismissed")


def test_answer_a_prompt(page: Page):
    page.set_content(DIALOG_PAGE)
    page.once("dialog", lambda dialog: dialog.accept("Alice"))
    page.get_by_role("button", name="Show prompt").click()
    expect(page.get_by_test_id("out")).to_have_text("Alice")