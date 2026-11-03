# Local browser setup and private sign-in

CV Tailor's optional application browser works with any MCP-capable AI agent host. The local host selects the tools; the model vendor does not select the browser. Brave, Edge and Chrome use installed browsers. Chromium, Firefox and WebKit use Playwright-managed builds. WebKit is an engine, not an attachment to Safari; arbitrary existing browser tabs are not supported by this adapter. Agents with their own documented browser/computer tools can also use the shared `cv-apply` workflow; private wizard-created profiles stay behind the restricted adapter.

Brave uses Playwright's Chromium engine with its installed executable. It is detected in standard Windows/macOS locations or on PATH; set `CV_TAILOR_BRAVE_PATH` for a nonstandard installation. There is no silent browser fallback. Compatibility depends on Brave's Chromium version; local fixture tests do not establish compatibility with every Brave release or job portal.

## Install and sign in

Use the repository environment:

```powershell
.venv\Scripts\python.exe -m pip install -e "ai-service[automation]"
# Brave, Edge or Chrome must already be installed. For another engine, for example:
.venv\Scripts\python.exe -m playwright install firefox
.venv\Scripts\cv-tailor.exe browser setup
```

On macOS/Linux, use `.venv/bin/python` and `.venv/bin/cv-tailor`. The native wizard requires Python's Tk support (install the OS tkinter package if your Python distribution omits it). No AI API key is required.

In the wizard, choose a site name and browser, and enter a start URL without credentials, query parameters or fragments. Additional allowed sites are exact HTTPS origins such as `https://boards.example.com`, not wildcards. HTTP is accepted only for loopback fixtures. Use **Open browser to sign in**, enter credentials directly on the website, finish any MFA/CAPTCHA, and return to the job page. Then click **Save session and close browser**. The wizard does not read fields, take screenshots, record traces, or collect passwords. Avoid saving passwords in the browser password manager if you do not want them retained there.

An OS file lock prevents the sign-in wizard and application tools from opening the same profile simultaneously. Before renewing a session, disconnect its MCP server in your host, then run:

```text
cv-tailor browser login --site onlinejobs
```

Browser state is kept under `DATA_DIR/browser/profiles/SITE/BROWSER/`, outside the checkout by default. Treat it as sensitive authenticated data. `sites.json` contains only nonsecret configuration and the time the user saved a session; this timestamp does not prove successful authentication. Switching browsers uses a different profile and may require signing in again. Nothing copies your normal browser's cookies, profiles, or debugging-port files.

## Connect the agent

The wizard can copy an MCP configuration snippet. You can also generate it with:

```text
cv-tailor --json browser mcp-config --site onlinejobs
# OpenCode uses a different enclosing configuration:
cv-tailor --json browser mcp-config --site onlinejobs --host opencode
```

Standard output uses the `mcpServers` JSON shape and absolute executable/workspace paths. OpenCode output uses its `mcp` object with a local command array. The wizard offers both formats. Merge the server entry into your chosen host's project MCP settings, preserving other settings. Gemini CLI uses `.gemini/settings.json`; Claude Code uses its project MCP configuration; other hosts should register the same executable and argument list through their documented MCP setup. This server is not tied to Gemini: Claude Code, Codex, OpenCode, Antigravity and other compatible agents can use it. Windows configurations must use `python.exe` for MCP stdio, even when the wizard runs under `pythonw.exe`. Do not install a second unrestricted browser MCP server against the private profile. The repository ignores machine-specific `.gemini/` configuration.

Restart the host's MCP connection and verify that the `cv-browser-SITE` tools are discovered. The server command is `cv-tailor browser serve --site SITE`, using stdio; it starts a visible task browser. It begins on a blank page without inspecting restored tabs. Use `browser_open` with the intended application URL. The server does not expose an HTTP debugging port.

## Application tools

The adapter exposes only `browser_open`, `browser_inspect`, `browser_fill`, `browser_select`, `browser_check`, `browser_upload`, and `browser_click`. Tools use newly observed opaque references instead of arbitrary selectors. Each action checks the current page, frame origins, field identity, existing value and control type. Reinspection invalidates earlier references. Existing answers and attachments require an explicit replacement flag after the workflow obtains the user's approval.

Inspection reports native fields, option labels, limits, readbacks, validation errors and attachment fingerprints. It deliberately does not claim that every custom control or application step has been inventoried. Use the existing `cv-apply` checkpoint workflow, including fresh observations after every step. Custom widgets may require the user to finish that control locally.

Export explicitly selected documents to `DATA_DIR/browser/uploads/SITE/` using the filenames from `forms prepare`. `browser_upload` accepts only a PDF filename within that site's staging directory; it cannot upload browser profiles, arbitrary paths, environment files or cookie stores. File hashes are observed from the actual browser attachment when supported.

The tool surface has no arbitrary JavaScript, screenshots, cookies, storage state, network logs, shell execution or file reads. Credential and verification pages/controls produce a local-sign-in handoff without field observations. Authentication-looking paths and token-bearing URL parameters are blocked. Navigation is restricted to configured origins, including redirects and embedded document requests. Ordinary external CDN subresources remain available so sites can render. Popups are closed; the user must handle unsupported popup workflows locally.

Clearly nonfinal Next, Continue, Save draft and add-entry buttons are supported. Other buttons, including final submission, require local user action. These checks cannot prove the semantics of arbitrary website JavaScript: a site can attach a submission handler to an innocent-looking button or field. The workflow still requires user review and never instructs the agent to submit an application.

## What “local only” guarantees

Passwords are entered in the local browser and are never accepted by the CLI, wizard, MCP tool arguments, application checkpoints, or CV Tailor's database. The browser reuses authenticated state. Website operators still receive their normal login requests, and the AI host/provider may process application observations and answers returned by the tools.

This is a restricted tool interface, **not an OS security boundary**. Browser profiles contain session secrets. An unrestricted shell, desktop-control tool, other process running as your Windows account, or an agent allowed to rewrite this code may access or defeat these restrictions. For a stronger boundary, run the browser service under a separate OS account or isolated machine, expose only its restricted tool interface, and deny the AI host filesystem/process/desktop access to that environment. Do not claim that an ignored file or encrypted same-user credential store makes secrets inaccessible to an unrestricted local agent.

If sign-in expires, save application progress, disconnect MCP and use the local wizard again. Never request credentials in chat, even as a fallback. Do not mark an application Applied until the user confirms submission through the existing `forms confirm-submission` flow.

## Verification

Normal backend tests do not download browsers or visit employer sites. Opt-in browser tests use disposable profiles and a loopback website with synthetic credentials:

```powershell
$env:CV_TAILOR_BROWSER_TESTS = '1'
$env:CV_TAILOR_TEST_BROWSER = 'msedge'
.venv\Scripts\python.exe -m pytest ai-service/tests/test_browser_automation.py
```

Set the browser to `chromium`, `firefox`, or `webkit` after installing its Playwright build. Tests cover native filling/readbacks, existing-value preservation, stale references, upload confinement, redirect restrictions, credential/OTP/frame blocking, session reuse without export, and exclusion between sign-in and MCP processes. These fixture checks do not establish compatibility with every job portal.
