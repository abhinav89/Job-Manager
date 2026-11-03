---
name: cv-browser
description: Set up browser-independent application tools and local-only job-site sign-in. Use for browser setup, saved login sessions, or connecting any MCP-capable AI agent to cv-apply.
---

# cv-browser

Never request passwords, MFA codes, recovery codes, cookies or sign-in tokens in chat, files, command arguments or environment variables. Do not read browser profiles or use general browser tools to extract session state. The user types credentials directly into the visible sign-in browser.

Run `cv-tailor browser status`. If automation dependencies are missing, install `python -m pip install -e "ai-service[automation]"` using this repository's environment. Brave, Edge and Chrome use the installed browser; Chromium, Firefox and WebKit use Playwright builds installed with `python -m playwright install BROWSER`. Brave is discovered in standard Windows/macOS locations or on PATH; `CV_TAILOR_BRAVE_PATH` can specify its executable. Never silently substitute another browser when Brave is missing.

Run `cv-tailor browser setup` to open the native local wizard. It records only a site name, browser, token-free start URL and exact allowed origins. The user signs in, completes MFA/CAPTCHA, returns to the job page, and clicks **Save session and close browser**. For a configured site, use `cv-tailor browser login --site SITE`. The wizard and MCP server require exclusive ownership of that site's profile: disconnect its MCP server before signing in again.

Run `cv-tailor browser mcp-config --site SITE` for a nonsecret standard MCP JSON snippet, or use `--host opencode` for OpenCode's format. The wizard offers both formats. The tools are model/vendor independent: Gemini, Claude Code, Codex, OpenCode, Antigravity and other local agents can register the same stdio server through their supported MCP configuration. Merge into the requested host's **project** settings, preserving existing servers; never modify another agent's global configuration. Standard JSON uses `mcpServers`; hosts with other formats need the same executable and argument list adapted to their documented configuration. Windows MCP must run `python.exe`, not `pythonw.exe`, even when the wizard itself runs without a console. The server is `cv-tailor browser serve --site SITE`; restart the connection after configuration. Do not report it connected until that host discovers its tools.

For applications, follow [cv-apply](../cv-apply/SKILL.md). Prefer the restricted `cv-browser-SITE` tools for sessions created here. Export explicitly selected PDFs into `DATA_DIR/browser/uploads/SITE/` using their exact manifest filenames. Supply only that filename to `browser_upload`. Browser references expire after each observation; save semantic checkpoint identities separately. Native controls, exact option labels and file readbacks are supported; custom widgets may require local user action. There is no arbitrary JavaScript, screenshot, file-read, cookie, storage, network-log or password tool.

If a tool reports sign-in or a verification field, checkpoint application answers and open the local wizard. Never switch to unrestricted tools to inspect that sign-in session. Final consent and submission remain with the user. A user-saved session is not proof of authentication; verify the application page when tools resume.

The restrictions apply to this MCP interface. Browser profiles contain sensitive authenticated state. They are not isolated from other processes with the same OS permissions, unrestricted shells, or unrelated desktop-control tools. Do not promise that local storage makes credentials inaccessible to every AI tool. See [the browser setup documentation](../../../docs/browser_setup.md) for the actual boundary.
