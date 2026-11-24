"""Module 13 - Visual and accessibility testing.

Screenshot comparison, ARIA snapshots, and automated accessibility checks.

The visual tests need pytest-playwright-visual-snapshot, and the axe tests need
axe-playwright-python. The axe fixture skips if the package is missing.

The first visual run writes the reference images into __snapshots__/ and reports
those tests as failures. Run it once with --update-snapshots, then normally:
    pytest tests/test_13_visual_a11y.py --update-snapshots
    pytest tests/test_13_visual_a11y.py -v
"""
import pytest
from playwright.sync_api import Page, expect

# A small page with a few accessibility problems, on purpose.
# Both pages are wrapped in <main>, because axe requires a main landmark
# (landmark-one-main) and wants all content inside one (region).
INACCESSIBLE_PAGE = """
<html lang="en">
<head><title>Sign up</title></head>
<body>
  <main>
    <h1>Sign up</h1>
    <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
    <input type="text" id="email">
    <button style="color: #bbbbbb; background: #ffffff">Submit</button>
  </main>
</body>
</html>
"""

# The same page, with those problems fixed.
ACCESSIBLE_PAGE = """
<html lang="en">
<head><title>Sign up</title></head>
<body>
  <main>
    <h1>Sign up</h1>
    <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Decorative line" />
    <label for="email">Email address</label>
    <input type="text" id="email">
    <button style="color: #000000; background: #ffffff">Submit</button>
  </main>
</body>
</html>
"""

# A stable page for the visual tests: fixed size, no animation, no outside content.
STABLE_PAGE = """
<html>
<head><style>
  body { margin: 0; font-family: Arial, sans-serif; }
  .card { width: 300px; padding: 20px; border: 2px solid #333; }
  h2 { margin: 0 0 10px 0; }
</style></head>
<body>
  <div class="card" data-testid="card">
    <h2>Order summary</h2>
    <p>2 items</p>
    <p>Total: 24.00</p>
  </div>
</body>
</html>
"""


# ---------- ARIA SNAPSHOTS ----------

def test_aria_snapshot_of_a_form(page: Page):
    """An ARIA snapshot describes the page's structure as assistive
    technology sees it: roles and names, not pixels or HTML."""
    page.set_content(ACCESSIBLE_PAGE)
    expect(page.locator("body")).to_match_aria_snapshot(
        """
        - main:
          - heading "Sign up" [level=1]
          - img "Decorative line"
          - text: Email address
          - textbox "Email address"
          - button "Submit"
        """
    )


def test_aria_snapshot_catches_a_missing_label(page: Page):
    """The same snapshot fails on the page whose input has no label."""
    page.set_content(INACCESSIBLE_PAGE)
    with pytest.raises(AssertionError):
        expect(page.locator("body")).to_match_aria_snapshot(
            """
            - main:
              - heading "Sign up" [level=1]
              - textbox "Email address"
            """,
            timeout=1000,
        )


# ---------- ACCESSIBILITY CHECKS WITH AXE ----------

@pytest.fixture
def axe():
    """The axe accessibility engine, or a skip if it is not installed."""
    axe_core = pytest.importorskip(
        "axe_playwright_python.sync_playwright",
        reason="axe-playwright-python is not installed",
    )
    return axe_core.Axe()


def test_axe_finds_problems(page: Page, axe):
    page.set_content(INACCESSIBLE_PAGE)
    results = axe.run(page)
    assert results.violations_count > 0
    ids = {violation["id"] for violation in results.response["violations"]}
    assert "image-alt" in ids          # the image has no alt text
    assert "label" in ids              # the input has no label


def test_axe_passes_on_the_fixed_page(page: Page, axe):
    page.set_content(ACCESSIBLE_PAGE)
    results = axe.run(page)
    assert results.violations_count == 0, results.generate_report()


def test_axe_can_ignore_known_issues(page: Page, axe):
    """Real projects usually have known problems. Check the rest still passes."""
    page.set_content(INACCESSIBLE_PAGE)
    results = axe.run(page)
    known = {"image-alt", "label", "color-contrast"}
    unexpected = [
        violation["id"]
        for violation in results.response["violations"]
        if violation["id"] not in known
    ]
    assert unexpected == [], f"new accessibility problems: {unexpected}"


# ---------- VISUAL COMPARISON ----------

def test_visual_page_snapshot(page: Page, assert_snapshot):
    page.set_viewport_size({"width": 400, "height": 300})
    page.set_content(STABLE_PAGE)
    assert_snapshot(page.screenshot())


def test_visual_element_snapshot(page: Page, assert_snapshot):
    """Comparing one element is far more stable than a whole page."""
    page.set_content(STABLE_PAGE)
    assert_snapshot(page.get_by_test_id("card").screenshot())


def test_visual_with_a_tolerance(page: Page, assert_snapshot):
    """A small threshold absorbs harmless rendering differences."""
    page.set_viewport_size({"width": 400, "height": 300})
    page.set_content(STABLE_PAGE)
    assert_snapshot(page.screenshot(), threshold=0.2)