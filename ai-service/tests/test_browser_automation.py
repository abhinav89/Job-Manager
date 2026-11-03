"""Credential boundary tests use synthetic data and disposable browser profiles."""
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from cv_tailor import browser
from cv_tailor.browser import BrowserError
from cv_tailor.browser_mcp import ApplicationBrowser, protect, require_allowed


@pytest.fixture
def configured_site(tmp_path, monkeypatch):
    monkeypatch.setenv("CV_TAILOR_HOME", str(tmp_path))
    browser.save_site("example", "chromium", "https://jobs.example/", ["https://ats.example"])
    return browser.site_settings("example")


def test_config_contains_no_credentials_and_mcp_uses_selected_workspace(configured_site, tmp_path):
    config = browser.mcp_config("example")["mcpServers"]["cv-browser-example"]
    assert config["command"] == sys.executable
    assert str(tmp_path) in config["args"]
    assert config["args"][-3:] == ["serve", "--site", "example"]
    assert browser.status()["password_storage"] == "none"
    assert browser.profile_dir("example", configured_site).parent.name == "example"
    assert browser.upload_dir("example") != browser.profile_dir("example", configured_site)
    with pytest.raises(BrowserError):
        browser.site_settings("../example")


def test_gui_generates_console_python_for_mcp(configured_site, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "executable", str(tmp_path / "pythonw.exe"))
    config = browser.mcp_config("example")["mcpServers"]["cv-browser-example"]
    assert config["command"] == str(tmp_path / "python.exe")


def test_opencode_uses_the_same_local_tools(configured_site):
    standard = browser.mcp_config("example")["mcpServers"]["cv-browser-example"]
    config = browser.mcp_config("example", "opencode")["mcp"]["cv-browser-example"]
    assert config["command"] == [standard["command"], *standard["args"]]
    assert config["enabled"] is True
    assert config["type"] == "local"


def test_brave_path_override_is_validated(monkeypatch, tmp_path):
    executable = tmp_path / "brave.exe"
    executable.touch()
    monkeypatch.setenv("CV_TAILOR_BRAVE_PATH", str(executable))
    assert browser.brave_executable() == str(executable.resolve())
    executable.unlink()
    with pytest.raises(BrowserError, match="installed Brave executable"):
        browser.brave_executable()
    assert browser.validate_site("brave", "https://jobs.example/")["browser"] == "brave"


@pytest.mark.parametrize("url", ["https://user:password@jobs.example/", "file:///passwords", "http://jobs.example/", "javascript:alert(1)"])
def test_invalid_urls_are_not_echoed(url):
    with pytest.raises(BrowserError) as caught:
        browser.origin(url)
    assert url not in str(caught.value)


@pytest.mark.parametrize("url", ["https://jobs.example/?token=PRIVATE", "https://jobs.example/#secret", "https://jobs.example:invalid/"])
def test_setup_rejects_token_urls_without_echoing_them(url, configured_site):
    with pytest.raises(BrowserError) as caught:
        browser.save_site("bad", "msedge", url)
    assert "PRIVATE" not in str(caught.value)


def test_site_scope_and_login_urls(configured_site):
    for url in ["https://jobs.example.evil/", "https://jobs.example:444/", "https://other.example/",
                "https://jobs.example/login", "https://jobs.example/form?access_token=PRIVATE"]:
        with pytest.raises(BrowserError) as caught:
            require_allowed(url, configured_site)
        assert "PRIVATE" not in str(caught.value)
    require_allowed("https://ats.example/form?job=123", configured_site)
    assert browser.public_url("https://jobs.example/form?token=PRIVATE#secret") == "https://jobs.example/form"


def test_profile_lock_excludes_another_process_and_releases(configured_site, tmp_path):
    code = "from cv_tailor.browser import profile_lease, site_settings;\nwith profile_lease('example', site_settings('example')): pass"
    with browser.profile_lease("example", configured_site):
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20)
        assert result.returncode != 0
        assert "in use" in result.stderr
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_errors_do_not_export_driver_secrets():
    @protect
    async def broken():
        raise RuntimeError("password=PRIVATE_SECRET https://site/?token=PRIVATE_TOKEN")
    result = asyncio.run(broken())
    assert result["state"] == "action_failed"
    assert "PRIVATE" not in json.dumps(result)


def test_mcp_exposes_only_restricted_tools(configured_site):
    pytest.importorskip("mcp")
    pytest.importorskip("playwright")
    from cv_tailor.browser_mcp import create_server
    server = create_server("example")
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {
        "browser_open", "browser_inspect", "browser_fill", "browser_select", "browser_check", "browser_upload", "browser_click"}
    schemas = json.dumps([tool.inputSchema for tool in tools])
    for forbidden in ("password", "cookie", "javascript", "selector", "screenshot", "storage_state"):
        assert forbidden not in schemas


FORM = """<!doctype html><h1>Example engineer application</h1><form>
<label>Full name<input name="full_name" value="User existing"></label>
<label>Pitch<textarea maxlength="30"></textarea></label>
<label>Country<select><option value="">Choose</option><option value="ph">Philippines</option></select></label>
<label>Remote<input type="checkbox"></label><label>I agree to terms<input type="checkbox"></label>
<label>Resume<input type="file"></label><input type="hidden" value="HIDDEN_TOKEN">
<input type="password" style="display:none" value="HIDDEN_PASSWORD">
<button type="button">Submit application</button><a href="/step2">Next step</a>
</form>"""


@pytest.fixture
def application_site(tmp_path, monkeypatch):
    if os.getenv("CV_TAILOR_BROWSER_TESTS") != "1":
        pytest.skip("Opt-in real browser tests: CV_TAILOR_BROWSER_TESTS=1")
    pytest.importorskip("playwright")
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append((self.headers.get("Host"), self.path))
            if self.path == "/inside":
                self.send_response(302)
                self.send_header("Location", "/step2")
                self.end_headers()
                return
            if self.path == "/private" and "fixture_session=SYNTHETIC_COOKIE" not in self.headers.get("Cookie", ""):
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "http://localhost:" + str(self.server.server_port) + "/credential")
                self.end_headers()
                return
            html = FORM
            if self.path == "/credential":
                html = '<label>Password<input type="password" value="VISIBLE_PASSWORD"></label><input value="LOGIN_USERNAME">'
            elif self.path == "/otp":
                html = '<label>Verification code<input autocomplete="one-time-code" value="OTP_SECRET"></label>'
            elif self.path == "/email-login":
                html = '<form action="/login"><input autocomplete="username" value="USERNAME_SECRET"></form>'
            elif self.path == "/framed":
                html = FORM + '<iframe src="/credential"></iframe>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("CV_TAILOR_HOME", str(tmp_path))
    base = f"http://127.0.0.1:{server.server_port}"
    selected = os.getenv("CV_TAILOR_TEST_BROWSER", "msedge" if os.name == "nt" else "chromium")
    config = browser.save_site("fixture", selected, base)
    config["requests"] = requests
    yield base, config
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


async def with_browser(config, task):
    from playwright.async_api import async_playwright
    with browser.profile_lease("fixture", config) as path:
        async with async_playwright() as playwright:
            context = await browser.launch_context(playwright, path, config["browser"], headless=True)
            try:
                session = ApplicationBrowser(context, "fixture", config)
                await session.start()
                await task(session)
            finally:
                await context.close()


def test_live_form_fill_scope_upload_and_stale_references(application_site):
    base, config = application_site
    async def exercise(session):
        observed = await session.open(base + "/form?job=12")
        assert "HIDDEN" not in json.dumps(observed)
        assert observed["form_url"] == base + "/form"
        by_label = {field["label"]: field for field in observed["fields"]}
        with pytest.raises(BrowserError, match="Existing answer"):
            await session.fill(by_label["Full name"]["ref"], "Replacement")
        result = await session.fill(by_label["Pitch"]["ref"], "I build automations.")
        assert next(f for f in result["fields"] if f["label"] == "Pitch")["value"] == "I build automations."
        with pytest.raises(BrowserError, match="expired"):
            await session.fill(by_label["Pitch"]["ref"], "Other")
        by_label = {field["label"]: field for field in result["fields"]}
        with pytest.raises(BrowserError, match="character limit"):
            await session.fill(by_label["Pitch"]["ref"], "😀" * 16, True)
        result = await session.select(by_label["Country"]["ref"], ["Philippines"])
        by_label = {field["label"]: field for field in result["fields"]}
        assert by_label["Country"]["value"] == ["Philippines"]
        with pytest.raises(BrowserError, match="Consent"):
            await session.check(by_label["I agree to terms"]["ref"], True)
        with pytest.raises(BrowserError, match="may submit"):
            await session.click(by_label["Submit application"]["ref"])
        result = await session.check(by_label["Remote"]["ref"], True)
        by_label = {field["label"]: field for field in result["fields"]}
        assert by_label["Remote"]["value"] is True
        with pytest.raises(BrowserError, match="selected PDF"):
            await session.upload(by_label["Resume"]["ref"], "../../profiles/secret.pdf")
        pdf = browser.upload_dir("fixture") / "selected.pdf"
        pdf.write_bytes(b"%PDF-1.4\nfixture")
        result = await session.upload(by_label["Resume"]["ref"], pdf.name)
        uploaded = next(f for f in result["fields"] if f["label"] == "Resume")
        assert uploaded["files"][0]["size"] == pdf.stat().st_size
        assert len(uploaded["files"][0]["sha256"]) == 64
        # A user edit invalidates a previously observed field instead of being overwritten.
        name = next(f for f in result["fields"] if f["label"] == "Full name")
        await session.page.locator('[name="full_name"]').fill("User changed this")
        with pytest.raises(BrowserError, match="value changed"):
            await session.fill(name["ref"], "Replacement", True)
        result = await session.inspect()
        next_step = next(f for f in result["fields"] if f["label"] == "Next step")
        result = await session.click(next_step["ref"])
        assert result["form_url"] == base + "/step2"
        result = await session.open(base + "/inside")
        assert result["form_url"] == base + "/step2"
        with pytest.raises(Exception):
            await session.open(base + "/redirect")
        assert not any(host.startswith("localhost:") for host, _ in config["requests"])
        # A browser error page may retain a denied URL in its address bar;
        # no data or credentials from that destination may be exported.
        denied = await protect(session.inspect)()
        assert denied["state"] in {"needs_user_action", "action_failed"}
        assert "fields" not in denied
    asyncio.run(with_browser(config, exercise))


@pytest.mark.parametrize("page", ["/credential", "/otp", "/email-login", "/framed"])
def test_live_login_and_verification_pages_export_no_observations(application_site, page):
    base, config = application_site
    async def exercise(session):
        result = await protect(session.open)(base + page)
        assert result["state"] == "needs_user_action"
        assert "fields" not in result
        assert not any(marker in json.dumps(result) for marker in ["VISIBLE_PASSWORD", "OTP_SECRET", "LOGIN_USERNAME", "USERNAME_SECRET"])
    asyncio.run(with_browser(config, exercise))


def test_live_persistent_session_reuses_login_without_export(application_site):
    base, config = application_site
    async def seed(session):
        await session.context.add_cookies([{"name": "fixture_session", "value": "SYNTHETIC_COOKIE", "url": base,
                                           "expires": 2147483647, "httpOnly": True}])
    asyncio.run(with_browser(config, seed))
    async def reuse(session):
        result = await session.open(base + "/private")
        assert result["state"] == "observed"
        assert "SYNTHETIC_COOKIE" not in json.dumps(result)
    asyncio.run(with_browser(config, reuse))


def test_host_dom_helper_does_not_treat_passwords_as_application_answers(application_site):
    base, config = application_site
    source = Path(__file__).resolve().parents[2] / ".agents/skills/cv-apply/scripts/inspect-form.mjs"
    script = source.read_text(encoding="utf-8").replace("export async function", "async function", 1)
    async def exercise(session):
        # Test the independent host helper directly against the synthetic fixture.
        await session.page.goto(base + "/credential")
        result = await session.page.evaluate("async () => {" + script + "; return await inspectApplicationForm(); }")
        assert result["login_required"] is True
        assert result["fields"] == []
        assert "VISIBLE_PASSWORD" not in json.dumps(result)
    asyncio.run(with_browser(config, exercise))


def test_real_stdio_mcp_connection_can_discover_and_use_tools(application_site):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    base, _ = application_site
    # Only this fixture server is headless; the installed command stays visible.
    code = ("from functools import partial; import cv_tailor.browser_mcp as b; "
            "b.launch_context = partial(b.launch_context, headless=True); "
            "b.create_server('fixture').run(transport='stdio')")
    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=["-c", code],
                                       env={"CV_TAILOR_HOME": str(browser.browser_root().parent)})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                tools = await client.list_tools()
                assert len(tools.tools) == 7
                result = await client.call_tool("browser_open", {"url": base + "/form"})
                assert not result.isError
                assert "observed" in result.model_dump_json()
                denied = await client.call_tool("browser_open", {"url": base + "/credential"})
                output = denied.model_dump_json()
                assert "needs_user_action" in output
                assert "VISIBLE_PASSWORD" not in output
    asyncio.run(exercise())
