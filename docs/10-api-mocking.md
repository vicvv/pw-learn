PLAYWRIGHT WITH PYTHON - MODULE 10: API TESTING AND NETWORK MOCKING


GOAL

Work with the network, not only the page. Three different jobs:

- Call an API directly, with no browser, to check it or to set up data quickly.
- Intercept what the page requests, and answer it yourself. That is mocking, and it lets you test error screens, empty states and slow responses without changing the app.
- Control the browser's surroundings: the clock, offline mode, permissions and location.

By the end of this module you can:

- send GET and POST requests with Playwright's request context, and check status, body and headers
- intercept requests with page.route, and fulfil, abort or change them
- inspect what the page sent, including the body of a POST
- wait for a specific response after an action
- fix the date and fast-forward time with page.clock
- switch the browser offline, grant permissions and set a location

Practice: tiny local pages built with page.set_content(), plus httpbin.org for the API tests. httpbin.org is a public service that echoes back whatever you send it, which makes it useful for learning HTTP.


THREE WAYS TO USE THE NETWORK IN TESTS

1. API testing: your test is the client. No browser, no page. Fast, and good for checking an API on its own, or for creating test data before a UI test.
2. Mocking: the browser makes its normal requests, but your test answers them. The app does not know the difference.
3. Observing: the browser talks to the real server, and your test watches, waits for a particular response, or checks what was sent.

All three are useful. The common mistake is reaching for mocking when the real thing would do, or for the UI when an API call would be faster.


API TESTING: THE REQUEST CONTEXT

playwright.request.new_context() gives an HTTP client that shares Playwright's networking but has no browser attached. The api_request_context fixture in tests/conftest.py creates one for the whole session:

```python
@pytest.fixture(scope="session")
def api_request_context(playwright):
    context = playwright.request.new_context(
        extra_http_headers={"Accept": "application/json"}
    )
    yield context
    context.dispose()
```

- playwright is the built-in fixture from Module 07.
- extra_http_headers are sent with every request from this context.
- Session scope: one client for the whole run, because creating it is cheap but repeating it is pointless. With -n (Module 09), each worker gets its own.
- dispose() closes it in the teardown.

Making requests:

```python
response = api_request_context.get(f"{API}/get", params={"q": "playwright"})
response = api_request_context.post(f"{API}/post", data={"name": "report"})
response = api_request_context.put(url, data={...})
response = api_request_context.delete(url)
response = api_request_context.get(url, headers={"X-Test-Run": "module-10"})
```

- params adds a query string: /get?q=playwright
- data with a dictionary sends JSON, and sets the Content-Type header to application/json.
- To send form data instead, use form={...}. To send raw bytes or text, use data="...".

Reading the response:

```python
response.ok            # True for status 200 to 299
response.status        # 200, 404, 500...
response.status_text   # "OK", "Not Found"
response.json()        # the body, parsed from JSON
response.text()        # the body as text
response.body()        # the body as bytes
response.headers       # a dictionary of response headers
response.url           # the final address, after any redirects
```

Note that response.ok is a property, not a method: write response.ok, not response.ok().


WHEN TO USE API CALLS INSTEAD OF THE UI

API calls are seconds faster than clicking through a form, and they do not break when the page changes. Use them for:

- Setting up data: create the ten orders a test needs through the API, then check the UI shows them.
- Cleaning up: delete what a test created, in a fixture's teardown.
- Logging in: get a session through the API instead of filling the login form (Module 11).
- Checking the API itself, as its own test.

Do not use them to replace the test's actual subject. A test about the checkout form must use the form, because that is what it is testing. Set everything else up through the API.


MOCKING WITH PAGE.ROUTE

page.route(pattern, handler) intercepts matching requests. The handler decides what happens:

```python
page.route("**/users", lambda route: route.fulfill(status=500, body="server is unwell"))
```

Every matching request now gets that answer, and the real server is never contacted.

The three things a handler can do:

```python
route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
route.abort()                      # the request fails, as if the network dropped
route.continue_()                  # let it through to the real server
```

continue_ has an underscore because continue is a reserved word in Python. It can also change the request on the way through:

```python
route.continue_(headers={**route.request.headers, "X-Test": "1"})
route.continue_(url="https://other.example.com/api/users")
route.continue_(method="POST", post_data=json.dumps({"name": "changed"}))
```

Patterns:

```python
page.route("https://api.example.com/users", handler)     # an exact address
page.route("**/users", handler)                           # any address ending in /users
page.route("**/api/**", handler)                          # anything with /api/ in it
page.route(re.compile(r"/users/\d+$"), handler)           # a regular expression
```

** matches any characters, including slashes. A plain string must match the whole address, so "**/users" is usually what you want.

Where to put the route: before the page loads. A route added after the request has been made changes nothing. In these tests, page.route comes before page.set_content for that reason.

Scope:

- page.route applies to one page.
- page.context.route applies to every page in the context, including popups. Useful for blocking analytics everywhere.

Removing a route:

```python
page.unroute("**/users")        # remove the route for this pattern
page.unroute_all()              # remove them all
```

Limiting how many times a route applies:

```python
page.route("**/users", handler, times=1)
```

After one use, the route is removed and later requests go through normally. Useful for testing "fails once, then works".


WHY MOCK

- Error states: 500, 404, a timeout. Hard to produce on a real server, trivial to mock.
- Empty states: an empty list, a new account with no data.
- Edge cases: a thousand rows, very long names, missing fields, odd characters.
- Speed and reliability: no dependency on a slow or unavailable service.
- Third parties: payment providers, map services, analytics. Often you cannot make them fail on demand, and you should not send them test traffic.
- Blocking noise: analytics, ads and tracking scripts slow tests down and add network flakiness. Block them.

What mocking cannot tell you: whether the real API still behaves that way. A mock is your idea of the response, frozen in time. If the API changes a field name, your mocked tests keep passing while the app breaks. So keep some tests against the real thing, and check the real API separately with the request context.


INSPECTING WHAT THE PAGE SENT

route.request gives the request before it goes anywhere:

```python
def handle(route):
    request = route.request
    assert request.method == "POST"
    assert request.post_data_json == {"name": "report"}
    assert request.headers.get("content-type") == "application/json"
    route.fulfill(status=201, body="")
```

- request.method, request.url, request.headers
- request.post_data (text), request.post_data_json (parsed), request.post_data_buffer (bytes)
- Header names are lower-case in Playwright, so use "content-type", not "Content-Type".

This is how you check that the UI sends what it should: the right fields, the right values, the right headers. It catches bugs a screenshot never would.

A handler must always finish the route with fulfill, abort or continue_. A handler that does neither leaves the request hanging, and the page waits until it times out.


WAITING FOR A RESPONSE

To act and then wait for a particular response, use the same pattern as popups and downloads (Module 06):

```python
with page.expect_response("**/items") as response_info:
    page.get_by_role("button", name="Save").click()
response = response_info.value
assert response.status == 201
```

The order matters: listening starts when the with block is entered, and the click inside it triggers the response.

Related:

```python
with page.expect_request("**/items") as request_info: ...
page.expect_response(lambda response: response.url.endswith("/items") and response.status == 201)
```

A matcher function is useful when the address alone is not specific enough.

Watching all traffic, without waiting for anything in particular:

```python
page.on("request", lambda request: print(request.method, request.url))
page.on("response", lambda response: print(response.status, response.url))
page.on("requestfailed", lambda request: print("failed", request.url))
```

Traces (Module 04) record every request and response in the Network tab, which is usually easier than printing.


THE CLOCK

page.clock controls the time the page sees. This needs Playwright 1.45 or later.

Fix the date, so a page that shows today's date always shows the same one:

```python
page.clock.set_fixed_time("2030-01-15T10:00:00Z")
```

Time does not move at all: every call to new Date() returns that moment.

Install a controllable clock, then move time yourself:

```python
page.clock.install(time="2030-01-15T10:00:00Z")
page.clock.fast_forward("00:10")        # ten seconds pass instantly
page.clock.fast_forward(5000)           # or milliseconds
page.clock.run_for("01:00")             # one minute, firing timers as it goes
page.clock.pause_at("2030-01-15T23:59:00Z")
page.clock.resume()
```

- install must be called before the page loads, because it replaces the page's timing functions.
- fast_forward jumps the clock ahead without running the timers that would have fired in between. Use it to skip a long wait.
- run_for moves through the time and fires each timer on the way. Use it when the page has repeating timers and you want them all to happen, for example a counter that ticks every second.
- With a controllable clock, a one-hour session timeout can be tested in milliseconds.

What it is for:

- a page that shows a date, so screenshots and assertions are stable
- countdowns and timers
- session timeouts and "your session expires in 5 minutes" warnings
- anything that behaves differently at month end, year end or across midnight
- time zone bugs, together with timezone_id in browser_context_args (Module 07)


OFFLINE MODE

```python
page.context.set_offline(True)
page.context.set_offline(False)
```

The browser then behaves as if the network is gone: requests fail, and navigator.onLine becomes false. Good for testing an offline banner, a retry button, or an app that is meant to keep working offline.

It applies to the whole context, so every page in it goes offline together.


PERMISSIONS AND GEOLOCATION

Browsers ask the user before letting a page use the camera, the microphone, notifications or location. There is no way to click that browser prompt from a test, so permissions are granted in advance:

```python
page.context.grant_permissions(["geolocation"])
page.context.grant_permissions(["notifications"], origin="https://example.com")
page.context.clear_permissions()
```

Common permission names: geolocation, notifications, camera, microphone, clipboard-read, clipboard-write.

Setting a location:

```python
page.context.set_geolocation({"latitude": 48.8584, "longitude": 2.2945})
```

Without grant_permissions, the page's request for the location is refused, which is what test_permission_denied_by_default checks. Testing the refused case matters: an app should cope when a user says no.

Geolocation only works on a secure origin (https:// or http://localhost). A page loaded with set_content has no origin, so these tests use the local_server fixture in tests/conftest.py, which serves a small page from localhost. That also avoids depending on an external site, which matters on a network that inspects HTTPS traffic: a browser there can refuse an external address with ERR_CERT_COMMON_NAME_INVALID, because it does not trust the network's certificate.
Also set by the context (Module 07): locale, timezone_id, color_scheme, viewport.


THE FILES

- tests/conftest.py - now also has the api_request_context fixture
- tests/test_10_api_mocking.py - 15 tests

The pages are written in the test file: USERS_PAGE fetches a list of users, SAVE_PAGE posts when a button is clicked, CLOCK_PAGE shows the date and counts seconds, OFFLINE_PAGE reports whether the browser is online.

API tests (marked slow, because they use the internet):
- test_api_get - a GET with a query string, checking status and the echoed arguments
- test_api_post_json - a POST with JSON, checking the server received it
- test_api_status_code - a 404, checking ok is False
- test_api_headers - a custom header, echoed back

Mocking:
- test_mock_a_json_response - two users, invented by the test
- test_mock_an_error_response - a 500, so the page shows "failed"
- test_block_a_request - abort, so the request never happens
- test_inspect_the_request - checks the method, body and content type the page sent
- test_route_only_applies_once - times=1
- test_unroute_restores_normal_traffic - the route is removed, and the request goes to the real (nonexistent) address

Waiting:
- test_wait_for_response - waits for the POST after the click, and checks its status

Clock:
- test_fixed_date - the page always shows 15 January 2030
- test_fast_forward_time - a counter that ticks once a second reaches 10 instantly

Environment:
- test_offline_mode - online, offline, online again
- test_geolocation - the page reads the coordinates the test set
- test_permission_denied_by_default - without permission, the state is not "granted"


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Adding a route after the request was made.
page.route must come before the page loads, or before the action that triggers the request. Afterwards it changes nothing, and the test sees the real response.

Trap 2 - A handler that never finishes the route.
Every handler must call fulfill, abort or continue_. Otherwise the request hangs and the page waits until it times out.

Trap 3 - A pattern that matches nothing.
"users" as a pattern matches only an address that is exactly "users". Use "**/users". Nothing warns you: the route simply never fires, and the test uses the real response.

Trap 4 - Mocking everything.
A suite where every response is mocked no longer tests the app's real behaviour. The mocks drift away from the API, and the tests stay green while the app breaks. Keep some tests against the real thing.

Trap 5 - continue versus continue_.
continue is a Python keyword, so the method is continue_, with a trailing underscore.

Trap 6 - Header names.
Playwright gives header names in lower case. request.headers.get("Content-Type") returns None; use "content-type".

Trap 7 - response.ok as a method.
It is a property. response.ok() raises a TypeError.

Trap 8 - clock.install after the page loaded.
It replaces the page's timing functions, so it must be called before the page loads, or the page keeps the real ones.

Trap 9 - Geolocation without a real origin.
A page from set_content has no origin, and the browser refuses location there. Navigate to a real address first.

Trap 10 - Forgetting that permissions are refused by default.
Without grant_permissions, an app asking for location gets nothing. That is worth testing on purpose, but it surprises people who expected the happy path.

Trap 11 - Sending test traffic to a third party.
Payment providers, mail services and analytics should be mocked. Real requests cost money, pollute someone's data, or get your test account blocked.

Trap 12 - Session-scoped request contexts and parallel runs.
With -n, each worker makes its own. That is fine for read-only calls, but if the context creates data, you get one set per worker (Module 09).

Trap 13 - Depending on an external site for an origin.
On a corporate network that inspects HTTPS traffic, Chromium can refuse a public address with ERR_CERT_COMMON_NAME_INVALID, because the browser does not trust the certificate the network substitutes. Serving a page from localhost avoids the problem, and is faster and more reliable anyway.


HANDS-ON PRACTICE

1. Run the Module 10 tests:

```
pytest tests/test_10_api_mocking.py -v
```

   Expect 15 passed. The four API tests need the internet and are slower than the rest.

2. Run only the mocked tests, which need no internet:

```
pytest tests/test_10_api_mocking.py -v -m "not slow"
```

   Expect 11 passed. Try it with the Wi-Fi off: they still pass.

3. Watch the mocked list appear:

```
pytest tests/test_10_api_mocking.py --headed --slowmo 500 -k mock_a_json
```

   The page shows Alice and Bob, two users that exist nowhere but in the test.

4. Look at the network in a trace:

```
pytest tests/test_10_api_mocking.py -k wait_for_response --tracing on
ls test-results
```

   Open the trace with playwright show-trace and the folder name that ls printed, then click the Network tab. The POST to /items is listed with its status.

5. See time move without waiting:

```
pytest tests/test_10_api_mocking.py --headed --slowmo 500 -k fast_forward
```

   The counter jumps from 0 to 10 at once, although the test takes under a second.

If a test fails:

The API tests depend on httpbin.org, which is a free public service and is sometimes slow or down. If all four fail with timeouts, check https://httpbin.org in a browser. If it is down, run with -m "not slow" and try the API tests later.

The mocked, clock, offline and geolocation tests use local pages or example.com, so they do not depend on a demo app.

If the clock tests fail with an error about page.clock not existing, the Playwright version is older than 1.45. Check with pip show playwright.

Break it on purpose (this step is MEANT to fail):

1. In tests/test_10_api_mocking.py, in test_mock_a_json_response, move the page.route line to after the page.set_content line, so the route is registered too late.
   To find the lines: grep -n "page.route\|page.set_content" tests/test_10_api_mocking.py
2. Run:

```
pytest tests/test_10_api_mocking.py -v -k mock_a_json
```

3. The test fails. The page already asked for the users before the route existed, so the request went to the real api.example.com, which does not answer, and the page shows "failed" instead of "loaded". That is Trap 1.
4. Move the line back and run again. It passes.


MENTAL MODEL

- Three jobs: call the API yourself (request context), answer the page's requests (route), or watch them (expect_response, page.on).
- Routes must exist before the request is made, and every handler must fulfil, abort or continue_.
- Mock what you cannot control or do not own. Keep some tests against the real thing.
- Set data up through the API, and test the UI with the UI.
- The clock, offline mode, permissions and location are context settings, not page content.


FOR YOUR OWN APP LATER

- Error screens are usually untested, because nobody can make the server fail on demand. Mocking a 500 takes two lines and covers a page users do see.
- Block analytics and chat widgets in all tests with context.route. They slow every test down and add network flakiness for no benefit.
- Create test data through the API in a fixture, then test the UI. It is much faster than clicking through setup screens, and it does not break when those screens change.
- Keep a small set of tests with no mocks at all, running against a real test environment, so you notice when the real API changes.
- If your app shows dates, fix the clock in tests that assert on them. Otherwise they fail at midnight, at month end, or for a colleague in another time zone.
- Test the refused case for permissions, not only the granted one. Users do say no.


QUIZ (answers below - try before peeking)

1. When would you use api_request_context instead of clicking through the UI, and when would that be the wrong choice?

2. What are the three things a route handler can do, and what happens if it does none of them?

3. You write page.route("users", handler) and the handler never runs. Why?

4. A test mocks every response, so it never touches the real server. It passes for months while the app is broken in production. How?

5. How do you check that a Save button sends the right JSON body?

6. Why must page.route come before page.set_content in these tests?

7. Your app shows "Today: 14 November 2026" and a test asserts on it. The test fails tomorrow. What do you use, and what is the difference between set_fixed_time and install?

8. A test calls page.context.set_geolocation(...) and the page still cannot read the location. Name two possible reasons.

9. Why is api_request_context session-scoped, and what changes when you run with -n 4?

10. DevOps stretch question: your CI runs the whole suite against a staging server every night, and it fails whenever the payment provider's sandbox is down. Nothing in your app is broken. What would you change? (Just guess.)


ANSWERS


1. Use it for anything that is not the subject of the test: creating data, cleaning up, logging in, or checking the API itself. It is the wrong choice when the UI is what you are testing.

Why: an API call takes milliseconds and does not depend on any page. Creating ten orders through the API, then checking the orders list, tests the list without spending a minute filling forms, and without breaking when the order form changes.

The limit is that an API call proves nothing about the page. A checkout test that posts to /orders and then asserts the order exists has tested the API twice and the checkout form not at all.

Common mistakes:
- Replacing a UI test with an API call because it is faster. The speed comes from skipping the thing under test.

See: WHEN TO USE API CALLS INSTEAD OF THE UI.


2. fulfill (answer it yourself), abort (make it fail) or continue_ (let it through to the real server). If the handler does none of them, the request never completes, the page waits, and the test times out.

Why: route interception pauses the request and hands control to your handler. Nothing happens until the handler decides. There is no default and no timeout of its own, so a handler that only inspects the request and then returns leaves the page waiting for a response that never arrives.

A handler that inspects must still finish:

```python
def handle(route):
    print(route.request.post_data)
    route.continue_()          # or fulfill, or abort
```

Common mistakes:
- Writing continue instead of continue_, which is a syntax error because continue is a Python keyword.

See: MOCKING WITH PAGE.ROUTE, Trap 2 and Trap 5.


3. Because "users" is treated as a whole address to match, and no request has exactly that address. Use "**/users", where ** matches anything before it, including slashes.

Why: a plain string pattern must match the entire URL. The real request is https://api.example.com/users, so the pattern would have to be that whole address, or a glob such as "**/users", or a regular expression.

Nothing warns you when a pattern matches nothing. The route simply never fires, the real request goes out, and the test behaves as if there were no mock at all. If a mock seems to have no effect, check the pattern first, and look at the Network tab of a trace to see the exact address.

Common mistakes:
- Using "*/users", where a single * does not cross slashes.

See: MOCKING WITH PAGE.ROUTE, and Trap 3.


4. Because mocks are a snapshot of what the API used to return. If the real API renames a field, the app breaks, but the mocked tests keep sending the old shape and keep passing.

Why: a mock is written by you, not by the server. Nothing checks that the two still agree. The tests prove the app handles that response, not that the server sends it. The same applies to status codes, required headers and authentication.

How to reduce the risk:
- Keep a small set of tests with no mocks, against a real test environment.
- Check the API separately with the request context, asserting on the fields the UI relies on.
- Where the team uses them, contract tests check that both sides agree on the shape.

Common mistakes:
- Mocking everything because it makes the suite fast and green. Green is not the goal.

See: WHY MOCK, and Trap 4.


5. Intercept the request and read route.request.post_data_json inside the handler:

```python
def handle(route):
    assert route.request.method == "POST"
    assert route.request.post_data_json == {"name": "report"}
    route.fulfill(status=201, body="")

page.route("**/items", handle)
```

Why this matters: the page might look right and still send the wrong thing: a missing field, a number as a string, the wrong date format. Nothing visible on screen shows it. Checking the request body catches a class of bug that screenshots and page assertions never will.

Collect the values in a dictionary and assert after the action, as test_inspect_the_request does, so a failed assertion inside the handler does not leave the route unfinished.

Alternatively, with no mocking: use expect_request, let the request go to the real server, and inspect it.

Common mistakes:
- Using "Content-Type" when reading headers. Playwright gives header names in lower case (Trap 6).

See: INSPECTING WHAT THE PAGE SENT.


6. Because set_content loads the page, and the page's script fetches the users immediately. A route registered afterwards is too late: the request has already gone to the real address.

Why: page.route only affects requests made after it is registered. There is nothing retrospective about it. The same applies to a page loaded with goto: register routes first, then navigate.

This is what the break-it-on-purpose step demonstrates: with the lines swapped, the page shows "failed" instead of "loaded", because the request reached the nonexistent api.example.com.

Common mistakes:
- Registering routes in the middle of a test, after the page is already loaded, and wondering why nothing is mocked.

See: MOCKING WITH PAGE.ROUTE, and Trap 1.


7. Use page.clock. set_fixed_time freezes the clock at one moment, so every call to new Date() returns the same value and time never moves. install sets a starting time and gives you a clock you can move with fast_forward, run_for, pause_at and resume.

Why the difference matters:
- set_fixed_time is enough for a page that only reads the date once, such as "Today: ...". Simple, and nothing can tick.
- install is for anything that depends on time passing: countdowns, timers, session timeouts, polling. A one-hour timeout can be tested in milliseconds with fast_forward("01:00").

install must be called before the page loads, because it replaces the page's timing functions.

Common mistakes:
- Using a fixed time for a countdown test, then wondering why the counter never moves. With time frozen, it cannot.

See: THE CLOCK, and Trap 8.


8. The permission was not granted (grant_permissions(["geolocation"]) is needed first), or the page has no real origin, because it was loaded with set_content instead of navigating to an address.

Why:
- Browsers refuse location by default. Setting coordinates does not grant permission: it only decides what the answer will be once permission exists.
- Geolocation is only allowed on a secure origin (https:// or http://localhost). A set_content page has no origin at all, so the browser refuses regardless of permissions. That is why test_geolocation navigates to example.com first.

A third possibility in real apps: the permission was granted for a different origin, because grant_permissions can take an origin argument.

Common mistakes:
- Expecting a browser permission prompt to appear so the test can click it. There is no way to click it; grant it in advance.

See: PERMISSIONS AND GEOLOCATION, Trap 9 and Trap 10.


9. Because creating the client is pointless to repeat: it holds no per-test state, and one client serves every test in the run. With -n 4, each of the four workers creates its own, because each worker is a separate session.

Why that is usually fine: the fixture only sends requests. Four clients sending read-only requests is harmless.

When it is not fine: if the fixture created data (a test account, a set of orders), you would get four copies, one per worker. And a teardown that deletes everything could delete data another worker is still using. Those are the Module 09 problems: unique data per worker, or a lock.

Common mistakes:
- Assuming session scope means once per run. With xdist it is once per worker.

See: API TESTING: THE REQUEST CONTEXT, Trap 12, and Module 09.


10. Mock the payment provider in the nightly suite, so the tests no longer depend on someone else's sandbox, and check the real integration separately in a small, clearly marked set of tests.

Why: a failing build should mean your app is broken. A build that fails because a third party is down teaches the team to ignore failures, which is worse than having no tests. The payment sandbox is outside your control, is often slower than production, and may rate-limit you.

What that looks like in practice:
- Mock the provider's endpoints with context.route for the normal suite, including the failure cases (declined card, timeout), which are hard to produce for real.
- Keep a handful of real integration tests, marked (for example @pytest.mark.external), that run less often and whose failures are reported separately.
- Run them with pytest -m "not external" in the nightly job, and -m external in their own job.

Common mistakes:
- Adding retries so the flaky third-party failures pass eventually (Module 09). That hides real failures too.

See: WHY MOCK, Trap 11, and Module 08 for markers.


End of Module 10. Next up: Module 11, authentication and saved login state.