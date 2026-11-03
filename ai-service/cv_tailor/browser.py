"""Local browser configuration and exclusive, human-owned sign-in sessions.

No password, cookie, storage-state, or credential input/output API belongs here.
Profiles are sensitive local browser data, not an isolation boundary from the OS user.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

from cv_tailor.config import data_dir

BROWSERS = ("msedge", "chrome", "chromium", "firefox", "webkit")


class BrowserError(ValueError):
    pass


def origin(url):
    """Require an explicit web origin; never echo potentially sensitive input."""
    try:
        value = urlsplit(url)
        if (value.scheme not in {"https", "http"} or not value.hostname
                or value.username is not None or value.password is not None):
            raise ValueError
        host = value.hostname.lower()
        if value.scheme == "http" and host not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError
        port = value.port
        host = f"[{host}]" if ":" in host else host
        port_text = f":{port}" if port and port != {"https": 443, "http": 80}[value.scheme] else ""
        return f"{value.scheme}://{host}{port_text}"
    except (ValueError, TypeError):
        raise BrowserError("Use an HTTPS URL without embedded credentials (HTTP is allowed only on loopback).") from None


def public_url(url):
    value = urlsplit(url)
    return origin(url) + (value.path or "/")


def browser_root():
    return data_dir() / "browser"


def settings():
    path = browser_root() / "sites.json"
    if not path.exists():
        return {}
    try:
        sites = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(sites, dict):
            raise ValueError
        return sites
    except (ValueError, OSError):
        raise BrowserError("Browser settings could not be read. Reconfigure the site in the local wizard.") from None


def site_settings(site):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", site):
        raise BrowserError("Site names use lowercase letters, digits and hyphens, starting with a letter.")
    value = settings().get(site)
    if not value:
        raise BrowserError("Configure this site with cv-tailor browser setup first.")
    # Validate saved configuration as well as wizard input.
    return validate_site(value["browser"], value["url"], value.get("allowed_origins", [])) | {
        "login_saved_at": value.get("login_saved_at")}


def validate_site(browser, url, allowed_origins=()):
    if browser not in BROWSERS:
        raise BrowserError("Choose Edge, Chrome, Chromium, Firefox or WebKit.")
    base = origin(url)
    value = urlsplit(url)
    if value.query or value.fragment:
        raise BrowserError("Use a start URL without query parameters or fragments; never paste a sign-in token.")
    allowed = {base}
    for item in allowed_origins:
        parsed = urlsplit(item)
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise BrowserError("Additional allowed sites must be exact origins, without paths or tokens.")
        allowed.add(origin(item))
    return {"browser": browser, "url": public_url(url), "allowed_origins": sorted(allowed)}


def save_site(site, browser, url, allowed_origins=(), *, login_saved=False):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", site):
        raise BrowserError("Site names use lowercase letters, digits and hyphens, starting with a letter.")
    value = validate_site(browser, url, allowed_origins)
    sites = settings()
    previous = sites.get(site, {})
    if all(previous.get(key) == value[key] for key in value):
        value["login_saved_at"] = previous.get("login_saved_at")
    if login_saved:
        value["login_saved_at"] = datetime.now(timezone.utc).isoformat()
    root = browser_root()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / "sites.json"
    # Atomic replacement, no passwords or browser state in this metadata.
    temporary = root / f"sites-{os.getpid()}.tmp"
    temporary.write_text(json.dumps(sites | {site: value}, indent=2), encoding="utf-8")
    temporary.replace(path)
    return value


def profile_dir(site, config):
    return browser_root() / "profiles" / site / config["browser"]


def upload_dir(site):
    site_settings(site)
    path = browser_root() / "uploads" / site
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


@contextmanager
def profile_lease(site, config):
    """An OS lock releases on exit/crash; sign-in and MCP never share a profile."""
    path = profile_dir(site, config)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (path.parent / f"{config['browser']}.lock").open("a+b") as handle:
        handle.seek(0)
        handle.write(b"\0")
        handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise BrowserError("This site's browser is in use. Close its MCP client or finish local sign-in first.") from None
        try:
            yield path
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


async def launch_context(playwright, path, browser, *, headless=False):
    engine = "chromium" if browser in {"msedge", "chrome"} else browser
    options = {"headless": headless, "accept_downloads": False, "service_workers": "block"}
    if browser in {"msedge", "chrome"}:
        options["channel"] = browser
    context = await getattr(playwright, engine).launch_persistent_context(str(path), **options)
    context.set_default_timeout(5000)
    return context


def status():
    return {"available": importlib.util.find_spec("playwright") is not None,
            "mcp_available": importlib.util.find_spec("mcp") is not None,
            "sites": [{"site": name, **site_settings(name)} for name in settings()],
            "credential_entry": "local_browser_only", "password_storage": "none",
            "boundary": "Restricted tools; not isolation from other processes running as the same OS user."}


def mcp_config(site):
    site_settings(site)
    return {"mcpServers": {f"cv-browser-{site}": {
        "command": sys.executable,
        "args": ["-m", "cv_tailor", "--data-dir", str(data_dir()), "browser", "serve", "--site", site]}}}


def open_wizard(site=None):
    if importlib.util.find_spec("playwright") is None:
        raise BrowserError('Install browser automation first: python -m pip install -e "ai-service[automation]"')
    if site:
        site_settings(site)
    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    if os.name == "nt" and pythonw.exists():
        executable = pythonw
    args = [str(executable), "-m", "cv_tailor.browser_wizard", "--data-dir", str(data_dir())]
    if site:
        args.extend(["--site", site])
    subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return {"state": "wizard_started", "credential_entry": "Only in the visible browser, never in chat."}
