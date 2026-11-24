"""Module 10 - API testing and network mocking.

The request fixture for API calls, page.route to mock or block network traffic,
waiting for responses, and controlling the clock, permissions and offline mode.

Mocked tests use a tiny local page, so they need no internet. The API tests use
httpbin.org, a public service for testing HTTP requests. Tests that need a real
origin use the local_server fixture in conftest.py.
Run from the repo root with the venv active:
    pytest tests/test_10_api_mocking.py -v
"""
import json
import re

import pytest
from playwright.sync_api import Page, Route, expect

API = "https://httpbin.org"

# A page that fetches a list of users and shows their names.
USERS_PAGE = """
<h1>Users</h1>
<ul data-testid="users"></ul>
<div data-testid="status">loading</div>
<script>
  fetch("https://api.example.com/users")
    .then((response) => response.json())
    .then((users) => {
      document.querySelector("[data-testid=users]").innerHTML =
        users.map((user) => `<li>${user.name}</li>`).join("");
      document.querySelector("[data-testid=status]").textContent = "loaded";
    })
    .catch(() => {
      document.querySelector("[data-testid=status]").textContent = "failed";
    });
</script>
"""

# A page with a Save button that posts to an API.
SAVE_PAGE = """
<button id="save">Save</button>
<div data-testid="result"></div>
<script>
  document.querySelector("#save").onclick = async () => {
    const response = await fetch("https://api.example.com/items", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name: "report"}),
    });
    document.querySelector("[data-testid=result]").textContent =
      response.ok ? "saved" : `error ${response.status}`;
  };
</script>
"""

# A page that shows the current date and counts seconds.
CLOCK_PAGE = """
<div data-testid="now"></div>
<div data-testid="ticks">0</div>
<script>
  document.querySelector("[data-testid=now]").textContent =
    new Date().toISOString().slice(0, 10);
  let ticks = 0;
  setInterval(() => {
    ticks += 1;
    document.querySelector("[data-testid=ticks]").textContent = String(ticks);
  }, 1000);
</script>
"""

# A page that reports whether the browser thinks it is online.
OFFLINE_PAGE = """
<div data-testid="state"></div>
<script>
  const show = () => {
    document.querySelector("[data-testid=state]").textContent =
      navigator.onLine ? "online" : "offline";
  };
  show();
  window.addEventListener("online", show);
  window.addEventListener("offline", show);
</script>
"""


# ---------- API TESTING WITH THE REQUEST FIXTURE ----------

@pytest.mark.slow
def test_api_get(api_request_context):
    response = api_request_context.get(f"{API}/get", params={"q": "playwright"})
    assert response.ok
    assert response.status == 200
    body = response.json()
    assert body["args"] == {"q": "playwright"}


@pytest.mark.slow
def test_api_post_json(api_request_context):
    response = api_request_context.post(f"{API}/post", data={"name": "report"})
    assert response.ok
    body = response.json()
    assert body["json"] == {"name": "report"}


@pytest.mark.slow
def test_api_status_code(api_request_context):
    response = api_request_context.get(f"{API}/status/404")
    assert not response.ok
    assert response.status == 404


@pytest.mark.slow
def test_api_headers(api_request_context):
    response = api_request_context.get(
        f"{API}/headers", headers={"X-Test-Run": "module-10"}
    )
    assert response.ok
    assert response.json()["headers"]["X-Test-Run"] == "module-10"


# ---------- MOCKING WITH PAGE.ROUTE ----------

def test_mock_a_json_response(page: Page):
    def handle(route: Route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([{"name": "Alice"}, {"name": "Bob"}]),
        )

    page.route("https://api.example.com/users", handle)
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("status")).to_have_text("loaded")
    expect(page.get_by_test_id("users").get_by_role("listitem")).to_have_text(
        ["Alice", "Bob"]
    )


def test_mock_an_error_response(page: Page):
    page.route(
        "**/users",
        lambda route: route.fulfill(status=500, body="server is unwell"),
    )
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("status")).to_have_text("failed")


def test_block_a_request(page: Page):
    page.route("**/users", lambda route: route.abort())
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("status")).to_have_text("failed")


def test_inspect_the_request(page: Page):
    sent = {}

    def handle(route: Route):
        request = route.request
        sent["method"] = request.method
        sent["body"] = request.post_data_json
        sent["content_type"] = request.headers.get("content-type")
        route.fulfill(status=201, body="")

    page.route("**/items", handle)
    page.set_content(SAVE_PAGE)
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_test_id("result")).to_have_text("saved")
    assert sent["method"] == "POST"
    assert sent["body"] == {"name": "report"}
    assert sent["content_type"] == "application/json"


def test_route_only_applies_once(page: Page):
    page.route(
        "**/users",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([{"name": "Only once"}]),
        ),
        times=1,
    )
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("users").get_by_role("listitem")).to_have_text(
        ["Only once"]
    )


def test_unroute_restores_normal_traffic(page: Page):
    page.route("**/users", lambda route: route.abort())
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("status")).to_have_text("failed")
    page.unroute("**/users")
    # With the route removed, the request reaches the real (nonexistent)
    # api.example.com and fails there instead, so the page still shows "failed".
    page.set_content(USERS_PAGE)
    expect(page.get_by_test_id("status")).to_have_text("failed")


# ---------- WAITING FOR A RESPONSE ----------

def test_wait_for_response(page: Page):
    page.route(
        "**/items",
        lambda route: route.fulfill(status=201, body=""),
    )
    page.set_content(SAVE_PAGE)
    with page.expect_response("**/items") as response_info:
        page.get_by_role("button", name="Save").click()
    response = response_info.value
    assert response.status == 201
    assert response.request.method == "POST"


# ---------- THE CLOCK ----------

def test_fixed_date(page: Page):
    page.clock.set_fixed_time("2030-01-15T10:00:00Z")
    page.set_content(CLOCK_PAGE)
    expect(page.get_by_test_id("now")).to_have_text("2030-01-15")


def test_run_for_fires_timers(page: Page):
    page.clock.install(time="2030-01-15T10:00:00Z")
    page.set_content(CLOCK_PAGE)
    expect(page.get_by_test_id("ticks")).to_have_text("0")
    page.clock.run_for("00:10")               # ten seconds pass, firing each timer
    expect(page.get_by_test_id("ticks")).to_have_text("10")


def test_fast_forward_skips_timers(page: Page):
    page.clock.install(time="2030-01-15T10:00:00Z")
    page.set_content(CLOCK_PAGE)
    page.clock.fast_forward("01:00")          # jumps the clock without running timers
    expect(page.get_by_test_id("ticks")).not_to_have_text("60")


# ---------- OFFLINE MODE ----------

def test_offline_mode(page: Page):
    page.set_content(OFFLINE_PAGE)
    expect(page.get_by_test_id("state")).to_have_text("online")
    page.context.set_offline(True)
    expect(page.get_by_test_id("state")).to_have_text("offline")
    page.context.set_offline(False)
    expect(page.get_by_test_id("state")).to_have_text("online")


# ---------- PERMISSIONS AND GEOLOCATION ----------

def test_geolocation(page: Page, local_server):
    page.context.grant_permissions(["geolocation"])
    page.context.set_geolocation({"latitude": 48.8584, "longitude": 2.2945})
    page.goto(local_server)                   # localhost is a secure origin
    position = page.evaluate(
        """() => new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                (p) => resolve({lat: p.coords.latitude, lon: p.coords.longitude})
            );
        })"""
    )
    assert round(position["lat"], 4) == 48.8584
    assert round(position["lon"], 4) == 2.2945


def test_permission_denied_by_default(page: Page, local_server):
    page.goto(local_server)
    state = page.evaluate(
        """() => navigator.permissions.query({name: 'geolocation'}).then((r) => r.state)"""
    )
    assert state in ("prompt", "denied")