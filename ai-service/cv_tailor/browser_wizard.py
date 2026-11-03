"""Native local wizard. Passwords are entered directly in the browser, never here."""
import argparse
import asyncio
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from cv_tailor.browser import (BROWSERS, BrowserError, launch_context, mcp_config,
                               profile_lease, save_site, site_settings, upload_dir)
from cv_tailor.config import configure


async def sign_in(site, config, finished, events):
    # No agent tools, page evaluation, snapshots, traces, or credential reads here.
    from playwright.async_api import async_playwright
    with profile_lease(site, config) as path:
        async with async_playwright() as playwright:
            context = await launch_context(playwright, path, config["browser"])
            try:
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(config["url"], wait_until="domcontentloaded")
                events.put(("opened", None))
                while not finished.is_set() and context.pages:
                    await asyncio.sleep(0.25)
            finally:
                await context.close()


def run(site=None):
    root = tk.Tk()
    root.title("CV Tailor — local browser sign-in")
    root.geometry("680x640")
    root.minsize(620, 610)
    frame = ttk.Frame(root, padding=22)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Connect a job site", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Enter passwords only in the browser that opens.\nThis wizard never reads or saves your password.",
              wraplength=590).pack(anchor="w", pady=(8, 14))
    configured = site_settings(site) if site else {"browser": "msedge" if os.name == "nt" else "chromium",
                                                 "url": "https://www.onlinejobs.ph/", "allowed_origins": []}
    name = tk.StringVar(value=site or "onlinejobs")
    browser = tk.StringVar(value=configured["browser"])
    url = tk.StringVar(value=configured["url"])
    extra = tk.StringVar(value=", ".join(configured["allowed_origins"]))
    for label, variable in (("Site name", name), ("Start URL", url), ("Additional allowed origins (optional, comma separated)", extra)):
        ttk.Label(frame, text=label).pack(anchor="w")
        ttk.Entry(frame, textvariable=variable).pack(fill="x", pady=(3, 10))
    ttk.Label(frame, text="Browser").pack(anchor="w")
    ttk.Combobox(frame, textvariable=browser, values=BROWSERS, state="readonly").pack(fill="x", pady=(3, 10))
    message = tk.StringVar(value="Sign in, return to the job page, then save and close the browser.")
    ttk.Label(frame, textvariable=message, wraplength=590).pack(anchor="w", pady=8)
    events = queue.Queue()
    finished = threading.Event()
    active = {"running": False, "site": site, "config": None, "save": False}

    def start():
        try:
            config = save_site(name.get().strip(), browser.get(), url.get().strip(),
                               [item.strip() for item in extra.get().split(",") if item.strip()])
        except BrowserError as exc:
            messagebox.showerror("Check site settings", str(exc), parent=root)
            return
        active.update(running=True, site=name.get().strip(), config=config, save=False)
        finished.clear()
        start_button.configure(state="disabled")
        config_button.configure(state="disabled")
        message.set("Opening your local browser. Sign in there; do not put credentials in chat.")

        def worker():
            try:
                asyncio.run(sign_in(active["site"], config, finished, events))
                events.put(("closed", None))
            except Exception:
                # Browser errors can include page content or credential-bearing URLs.
                events.put(("error", None))
        threading.Thread(target=worker, daemon=True).start()

    def finish():
        active["save"] = True
        finish_button.configure(state="disabled")
        message.set("Closing the browser and saving its local session…")
        finished.set()

    def copy_config():
        root.clipboard_clear()
        root.clipboard_append(json.dumps(mcp_config(active["site"] or name.get().strip()), indent=2))
        message.set("MCP configuration copied. Add it to your agent's project MCP settings; restart its MCP connection.")

    def poll():
        while not events.empty():
            event, _ = events.get_nowait()
            if event == "opened":
                finish_button.configure(state="normal")
                message.set("Sign in in the visible browser. Finish MFA/CAPTCHA there, return to the job page, then save.")
            else:
                active["running"] = False
                start_button.configure(state="normal")
                finish_button.configure(state="disabled")
                if event == "closed" and active["save"]:
                    config = active["config"]
                    save_site(active["site"], config["browser"], config["url"], config["allowed_origins"], login_saved=True)
                    upload_dir(active["site"])
                    config_button.configure(state="normal")
                    message.set("Session saved locally. Passwords were not read. Copy the MCP configuration to connect your agent.")
                elif event == "error":
                    message.set("Could not open this browser. Close its MCP session, or install the selected browser with python -m playwright install BROWSER, then retry.")
                else:
                    message.set("Browser closed. A saved browser session does not prove that the site accepted your login.")
        root.after(150, poll)

    start_button = ttk.Button(frame, text="Open browser to sign in", command=start)
    start_button.pack(fill="x", pady=3)
    finish_button = ttk.Button(frame, text="Save session and close browser", command=finish, state="disabled")
    finish_button.pack(fill="x", pady=3)
    config_button = ttk.Button(frame, text="Copy agent MCP configuration", command=copy_config,
                               state="normal" if site else "disabled")
    config_button.pack(fill="x", pady=3)

    def close():
        if active["running"]:
            finished.set()
            message.set("Closing the sign-in browser. Close this wizard once the browser has closed.")
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir")
    parser.add_argument("--site")
    args = parser.parse_args()
    configure(args.data_dir)
    run(args.site)


if __name__ == "__main__":
    main()
