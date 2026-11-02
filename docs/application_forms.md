# Application form assistance

`cv-apply` runs through a browser-capable local agent. It combines the saved profile, a tracked job and explicit document selections with the agent's supported browser/computer tools. There is no new browser daemon, provider API requirement or database migration. The dashboard copies a handoff prompt and renders saved form checkpoints in the application conversation.

## Commands

```text
cv-tailor --json context export --task application_form --application 42
cv-tailor --json forms prepare --application 42 --resume 17 --cover-letter 18
cv-tailor --json schema application_form
cv-tailor --json drafts import --kind application_form --application 42 --input form.json --request-id form-start
cv-tailor --json drafts revise --kind application_form --application 42 --parent 19 --input form.json --request-id form-step-two
cv-tailor --json forms check 20
```

`forms prepare` returns context and a `snapshot` template. Fill and save that snapshot object, not the whole prepare response. Resume and cover-letter flags name **draft IDs**, not application IDs. Omitting a document flag does not automatically select a different document. Each manifest identifies the exact PDF bytes and source; export to its declared filename with `drafts export ID --format pdf --output ABSOLUTE_PATH`. Selected PDFs are cached outside slow write operations so later exports reuse the same bytes. Cover letters also support PDF export.

Checkpoints use the existing draft store and application conversation. Revise the latest checkpoint with its session ID and a new request ID; retain previous versions. An identical retry uses the same request ID and returns the original result. Reusing an ID for different data or revising an older checkpoint after a newer one exists reports a conflict. Personal evidence stays application-scoped and does not change the profile.

After the user explicitly confirms that they submitted:

```text
cv-tailor --json forms confirm-submission 20 --revision 3 --on 2026-11-02 --user-confirmed --request-id actual-submission
```

This atomically records a confirmation checkpoint and changes the tracker status/date. It does not send a form. Read the current application revision immediately beforehand. The date is the user's actual submission date, including submissions confirmed later. Repeat the same request ID for an identical retry. Manual edits after the last observation may differ from the saved values; confirmation does not pretend otherwise.

## Field contract and validation

Use the generated schema as the full contract. Every field has a semantic key including step, section, repeated entry and question; a control type; required status; exact options; optional rendered limit; original, proposed and observed values; observation status/time; a personal-evidence source; and any portal errors. Observations with known values require timezone-aware timestamps. Checkbox values are booleans; radio answers are exact option-label strings. A required checkbox must be checked; optional boolean answers can be false.

HTML `maxlength` is counted in UTF-16 code units, including astral Unicode characters as two units. Word counts use whitespace separation as a local check; the portal's displayed counter remains authoritative. Unknown limits produce a warning. Invalid options, over-limit answers, absent evidence, unapproved changes to existing values, unresolved sensitive answers, mismatched readbacks, incomplete inventories, unreadable controls and portal validation errors prevent verified-for-review status. File verification requires exact name, size and SHA-256, not just a nonempty upload widget. Selected document ownership, source/PDF fingerprints and application/profile revisions are checked against local storage.

The backend derives readiness; an imported snapshot cannot claim a state or a submission. Snapshots with unresolved issues can still be saved and recovered. The dashboard displays the validation saved with that checkpoint; `forms check` rechecks current local bindings. It cannot refresh browser observations.

## Browser capability and limits

The canonical skill routes to the host's supported browser APIs and operating instructions. Its optional read-only DOM helper handles native controls, repeated sections, visible limits, selected states and file fingerprints. Host snapshots are needed for custom widgets, frames and shadow DOM. File bytes or hashes may be unavailable through some hosts; those attachments remain unverified. On recovery, re-inspect rather than replaying saved actions. Browser element handles are not persisted.

The agent leaves login, CAPTCHA, consent and submission to the user. It avoids Enter and ambiguous final actions. These rules do not constitute a technical submission interlock over arbitrary host tools or arbitrary website JavaScript. No blanket compatibility claim is made for Greenhouse, Ashby, Lever, Workday or other portals; validate behavior in the live form. Tests use local fixtures and disposable data, never employer submissions.

## Design reference

Inspired by Career Ops' [apply workflow](https://github.com/career-ops-hq/career-ops/blob/20b9fd3a9c86d28c847e021f4dbbe93ce9a39a00/modes/apply.md). This implementation uses CV Tailor's Python CLI, existing local draft store and host-agent browser capabilities. Its DOM helper and validation are independently implemented; no Career Ops source is vendored.
