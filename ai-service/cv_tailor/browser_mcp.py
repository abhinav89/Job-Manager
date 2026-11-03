"""Restricted stdio browser tools: no model-supplied JS, selectors or state export."""
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone
from functools import wraps
import os
from pathlib import Path
import re
import secrets
from urllib.parse import parse_qs, urljoin, urlsplit

from cv_tailor.browser import (BrowserError, launch_context, origin, profile_lease,
                               public_url, site_settings, upload_dir)

DOM = Path(__file__).with_name("browser_dom.js").read_text(encoding="utf-8")
CONTROL_SELECTOR = "input, textarea, select, button, a[href], [role=combobox]"
LOGIN_PATH = re.compile(r"(?:^|/)(?:log-?in|sign-?in|signin|login|oauth|authorize|authentication|password|mfa|2fa|verify)(?:/|$)", re.I)
SECRET_KEY = re.compile(r"password|passwd|secret|token|api.?key|authorization|^code$", re.I)
SAFE_BUTTON = re.compile(r"next|continue|save and continue|save draft|add (?:another )?(?:experience|education|entry)", re.I)
CONSENT = re.compile(r"consent|agree|terms|privacy|certify|authorize|accept", re.I)


def require_allowed(url, config):
    if origin(url) not in config["allowed_origins"]:
        raise BrowserError("This destination is not an allowed site. Add its exact origin in the local wizard if intended.")
    if LOGIN_PATH.search(urlsplit(url).path) or any(SECRET_KEY.search(k) for k in parse_qs(urlsplit(url).query)):
        raise BrowserError("Sign-in or credential URL: use cv-tailor browser login in the local wizard. Never put credentials in chat.")


class ApplicationBrowser:
    def __init__(self, context, site, config):
        self.context, self.site, self.config = context, site, config
        self.page = None
        self.refs = {}
        self.navigation_blocked = False
        self.lock = asyncio.Lock()

    async def start(self):
        # Persistent contexts may restore a login page. Never inspect restored tabs.
        self.page = await self.context.new_page()
        await self.page.goto("about:blank")
        for page in list(self.context.pages):
            if page != self.page:
                await page.close()
        await self.context.route("**/*", self.route)
        self.context.on("page", self.close_popup)

    async def close_popup(self, page):
        if page != self.page:
            await page.close()

    async def route(self, route):
        request = route.request
        if request.is_navigation_request():
            try:
                require_allowed(request.url, self.config)
                # Playwright's route.continue_ follows HTTP redirects without
                # calling the handler again. Fetch exactly one response so the
                # redirect destination is checked before any request reaches it.
                response = await route.fetch(max_redirects=0, timeout=5000)
                try:
                    location = response.headers.get("location")
                    if 300 <= response.status < 400 and location:
                        require_allowed(urljoin(request.url, location), self.config)
                    await route.fulfill(response=response)
                finally:
                    await response.dispose()
            except Exception:
                self.navigation_blocked = True
                # Route callbacks must not log raw errors/URLs outside protect().
                try:
                    await route.abort()
                except Exception:
                    pass
            return
        try:
            await route.continue_()
        except Exception:
            pass

    async def observe(self):
        if self.navigation_blocked:
            raise BrowserError("Navigation was blocked. Open the intended allowed application URL again, or use the local wizard.")
        if not self.page or self.page.is_closed():
            raise BrowserError("Browser closed. Restart its MCP connection.")
        require_allowed(self.page.url, self.config)
        observations = []
        # Inspect all frames before returning anything; a sign-in iframe blocks the page.
        for frame in self.page.frames:
            if frame.url == "about:blank":
                # Empty frames are common; filled blank/srcdoc frames are not inspectable.
                if await frame.locator(CONTROL_SELECTOR).count():
                    raise BrowserError("An unscoped embedded form needs local user review.")
                continue
            require_allowed(frame.url, self.config)
            result = await frame.evaluate(DOM)
            if result["blocked"]:
                raise BrowserError("Credential or verification fields detected. Use the local sign-in wizard; never send credentials in chat.")
            observations.append((frame, result))
        return observations

    async def inspect(self):
        # Failed/changed inspections invalidate every old reference as well.
        self.refs.clear()
        observations = await self.observe()
        fields, headings = [], []
        for frame_index, (frame, result) in enumerate(observations):
            handles = await frame.query_selector_all(CONTROL_SELECTOR)
            headings.extend(result["headings"])
            for field in result["fields"]:
                index = field.pop("index")
                if index >= len(handles):
                    raise BrowserError("The page changed during inspection. Inspect it again.")
                ref = secrets.token_urlsafe(12)
                self.refs[ref] = (handles[index], field)
                fields.append({"ref": ref, "frame": frame_index, **field})
        return {"state": "observed", "form_url": public_url(self.page.url), "headings": headings,
                "observed_at": datetime.now(timezone.utc).isoformat(), "fields": fields,
                "inventory_complete": False,
                "note": "Native controls only. Reconcile custom controls and all steps through cv-apply checkpoints."}

    async def open(self, url):
        require_allowed(url, self.config)
        self.navigation_blocked = False
        self.refs.clear()
        await self.page.goto(url, wait_until="domcontentloaded")
        return await self.inspect()

    async def field(self, ref, kinds):
        await self.observe()
        if ref not in self.refs:
            raise BrowserError("This reference expired. Inspect the current page again.")
        handle, saved = self.refs[ref]
        if saved["kind"] not in kinds:
            raise BrowserError("This action does not support that control. Use local user review for custom widgets.")
        # A framework can reuse an element for a different question after re-rendering.
        # Re-inspect its owning frame and compare the whole observation before acting.
        owner = await handle.owner_frame()
        if not owner or not await handle.evaluate("el => el.isConnected"):
            raise BrowserError("This control changed. Inspect the page again.")
        current = await owner.evaluate(DOM)
        if current["blocked"]:
            raise BrowserError("Sign-in is required in the local wizard.")
        handles = await owner.query_selector_all(CONTROL_SELECTOR)
        for candidate in current["fields"]:
            index = candidate.pop("index")
            if index < len(handles) and await handle.evaluate("(el, other) => el === other", handles[index]):
                if candidate != saved:
                    raise BrowserError("This control or its value changed. Inspect again and preserve user edits.")
                return handle, candidate
        raise BrowserError("This control is no longer available. Inspect again.")

    async def fill(self, ref, value, replace_existing=False):
        handle, field = await self.field(ref, {"text", "textarea", "email", "tel", "url", "number", "date", "search"})
        if field["value"] and field["value"] != value and not replace_existing:
            raise BrowserError("Existing answer preserved. Confirm replacement with the user first.")
        if field["maxlength"] is not None and len(value.encode("utf-16-le")) // 2 > field["maxlength"]:
            raise BrowserError("The proposed answer exceeds the rendered character limit.")
        await handle.fill(value)
        return await self.inspect()

    async def select(self, ref, labels, replace_existing=False):
        handle, field = await self.field(ref, {"select"})
        if not labels or any(label not in field["options"] for label in labels):
            raise BrowserError("Choose exact observed option labels.")
        if field["value"] and field["value"] != labels and not replace_existing:
            raise BrowserError("Existing selection preserved. Confirm replacement with the user first.")
        await handle.select_option(label=labels)
        return await self.inspect()

    async def check(self, ref, checked, replace_existing=False):
        handle, field = await self.field(ref, {"checkbox", "radio"})
        if CONSENT.search(field["label"]):
            raise BrowserError("Consent is handled by the user in the visible browser.")
        if field["value"] and not checked and not replace_existing:
            raise BrowserError("Existing selection preserved. Confirm replacement with the user first.")
        await handle.set_checked(checked)
        return await self.inspect()

    async def upload(self, ref, filename, replace_existing=False):
        handle, field = await self.field(ref, {"file"})
        if field["files"] and not replace_existing:
            raise BrowserError("Existing attachment preserved. Confirm replacement with the user first.")
        root = upload_dir(self.site).resolve()
        path = (root / filename).resolve()
        if path.parent != root or path.suffix.lower() != ".pdf" or not path.is_file():
            raise BrowserError("Export the selected PDF into this site's browser/uploads directory and supply only its filename.")
        if not path.read_bytes().startswith(b"%PDF-"):
            raise BrowserError("Only exported PDF documents can be uploaded.")
        await handle.set_input_files(str(path))
        return await self.inspect()

    async def click(self, ref):
        handle, field = await self.field(ref, {"button", "link"})
        if field["kind"] == "link":
            require_allowed(await handle.evaluate("el => el.href"), self.config)
        elif not SAFE_BUTTON.fullmatch(field["label"]):
            raise BrowserError("This button may submit, sign in or give consent. Use the visible browser for this action.")
        await handle.click(no_wait_after=True)
        await self.page.wait_for_timeout(200)
        return await self.inspect()


def protect(function):
    """Do not leak Playwright errors, selectors, entered values or URL tokens."""
    @wraps(function)
    async def wrapped(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except BrowserError as exc:
            return {"state": "needs_user_action", "message": str(exc)}
        except Exception:
            return {"state": "action_failed", "message": "Browser action failed. Inspect again, or finish this step locally. No browser error details were exported."}
    return wrapped


def create_server(site):
    from mcp.server.fastmcp import FastMCP
    from playwright.async_api import async_playwright
    config = site_settings(site)

    @asynccontextmanager
    async def lifespan(server):
        with profile_lease(site, config) as path:
            async with async_playwright() as playwright:
                try:
                    context = await launch_context(playwright, path, config["browser"])
                except Exception:
                    raise BrowserError("Could not launch the selected browser. Install it locally, then restart the MCP connection.") from None
                session = ApplicationBrowser(context, site, config)
                server._cv_browser = session
                try:
                    await session.start()
                    yield {}
                finally:
                    await context.close()

    server = FastMCP(f"cv-browser-{site}", lifespan=lifespan,
                     instructions="Use cv-apply checkpoints. Never request credentials in chat. Sign in through cv-tailor browser login. Final submission belongs to the user.")

    async def call(method, *args):
        session = server._cv_browser
        async with session.lock:
            return await getattr(session, method)(*args)

    @server.tool()
    @protect
    async def browser_open(url: str) -> dict:
        """Open a configured application origin. Sign-in URLs require local user action."""
        return await call("open", url)

    @server.tool()
    @protect
    async def browser_inspect() -> dict:
        """Read native application controls. Password/OTP pages return no observations."""
        return await call("inspect")

    @server.tool()
    @protect
    async def browser_fill(ref: str, value: str, replace_existing: bool = False) -> dict:
        """Fill an observed application field. Replacement requires prior user confirmation."""
        return await call("fill", ref, value, replace_existing)

    @server.tool()
    @protect
    async def browser_select(ref: str, labels: list[str], replace_existing: bool = False) -> dict:
        """Choose exact option labels from an observed native select."""
        return await call("select", ref, labels, replace_existing)

    @server.tool()
    @protect
    async def browser_check(ref: str, checked: bool, replace_existing: bool = False) -> dict:
        """Set an observed checkbox/radio. Consent must be handled locally by the user."""
        return await call("check", ref, checked, replace_existing)

    @server.tool()
    @protect
    async def browser_upload(ref: str, filename: str, replace_existing: bool = False) -> dict:
        """Upload only a selected PDF staged in this site's browser/uploads directory."""
        return await call("upload", ref, filename, replace_existing)

    @server.tool()
    @protect
    async def browser_click(ref: str) -> dict:
        """Follow an allowed link or clearly nonfinal Next/Continue/Save draft button."""
        return await call("click", ref)

    return server


def serve(site):
    # Protocol debugging can print authenticated headers independently of our
    # return values. Never enable it in the credential-bearing server process.
    os.environ.pop("DEBUG", None)
    os.environ.pop("PWDEBUG", None)
    create_server(site).run(transport="stdio")
