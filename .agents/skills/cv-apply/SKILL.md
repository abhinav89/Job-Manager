---
name: cv-apply
description: Assist with a tracked job's live application form using the local agent's browser or computer tools, save recoverable answers, and stop for user review before submission. Use for filling employer forms or drafting their application answers.
---

# cv-apply

CV Tailor supplies facts, selected documents, validated checkpoints and tracking. A dashboard handoff does not itself control the PC. First check the running host's available browser/computer tools and documented skill. When they support the user's selected browser/session, use them directly; do not require the CV Tailor browser wizard, automation extra or MCP server. This applies to Claude, Codex, Antigravity and other hosts according to the capabilities actually exposed in that session, not the model's name. If neither native tools nor the optional adapter are available, draft from pasted questions and supply copyable answers; retain unknown observations and never report the form filled.

Use [cv-browser](../cv-browser/SKILL.md) only when native access is unavailable/incompatible, the user explicitly chooses the adapter, or the task is resuming a wizard-created session. Never ask for passwords, MFA/recovery codes, cookies or sign-in tokens in chat on either path. With native tools, let the user sign in through the host's supported local browser flow. The optional wizard accepts sign-in directly in its own visible browser; its restricted MCP adapter reuses that session without a credential-read API. Keep wizard-created sessions behind that adapter and never bypass its sign-in block with general browser or shell tools. This is an interface restriction, not OS isolation from an unrestricted local agent.

## Select the application and documents

Run `cv-tailor --json status` and use the same `--data-dir` throughout. Load `applications get ID`, `profile get`, and `drafts list --application ID`. Require an explicit application ID and selected resume/cover-letter draft IDs; use the user's choice or ask when ambiguous. Never pick a document just because it is newest or shares a company name. If documents are needed, use cv-resume/cv-cover-letter first.

Export context with `context export --task application_form --application ID`. Start a form session with:

```text
cv-tailor --json forms prepare --application ID --resume RESUME_DRAFT_ID --cover-letter LETTER_DRAFT_ID
```

Omit absent document flags. The response contains `context`, a `snapshot` template, the output schema, and selected document manifests. Identity/contact facts come from the confirmed profile; experience wording should match the selected CV, with full confirmed history used when explicitly requested by the form. A prior draft never establishes a new personal fact. Surface contradictions instead of letting a tailored document override confirmed facts. Read the selected document contents and relevant conversation evidence, not unrelated applications.

Export each selected document as PDF to the **exact filename** in its manifest, using `drafts export ID --format pdf --output ABSOLUTE_PATH`. The manifest pins draft ID, source hash, PDF hash and size. Upload only the selected document to its matching field. Do not substitute a cover letter for a resume or change identity/email to work around duplicate detection.

## Inspect and prepare

Read [browser operation](references/browser.md) before using the live form. Check the intended company, role, current form URL, active posting and any existing application to the same role. Flag a duplicate for the user; do not create another application record. A form for another role or a closed posting needs a resolved target before filling.

Use `applications list --company COMPANY` to check existing applications, then compare the returned role and URL. Company matches alone do not mean duplicate roles.

Inventory every visible control on the current step, including required state, exact options, rendered limits, existing values and repeated-entry sections. Keep an `original_value` and a unique semantic `key` per step/section/entry/question. Browser element handles are transient and are not checkpoint identities. Capture conditional controls after dependent answers change. Set `inventory_complete` only after a complete fresh pass; `all_steps_complete` stays false until all steps have been inspected and completed.

Draft concise answers from confirmed personal evidence and the actual job. Record each field's `source` and specific `evidence`. Match HTML `maxlength` in UTF-16 code units; use visible word limits when provided. Unknown limits remain unknown. The CLI's whitespace word count is an estimate: use the portal's own counter to resolve a disagreement and shorten as needed.

Ask together for unresolved facts needed to proceed: work authorization, sponsorship, compensation, relocation, availability, demographic/self-identification answers and consent. Never infer these from a name, address, CV, or job requirement. Explicit user answers stay scoped to this application; pass new assertions via `--evidence facts.json`. Set `user_confirmed` only for an answer the user explicitly supplied or confirmed. Optional unanswered questions can stay blank. Do not auto-accept consent or select “prefer not to say” on the user's behalf.

Preserve nonempty existing values. Propose changes only when requested, and set `change_confirmed` only after approval. Pre-existing values can use `source: user_existing` with evidence identifying the live field; do not silently promote them into the profile.

For uploads, retain `original_files` from the first inspection, including hashes when available. Confirm before replacing an existing attachment; a selected document does not authorize silently overwriting a different uploaded file.

## Fill, verify and checkpoint

Save the populated `snapshot` object as JSON **before filling**, through:

```text
cv-tailor --json drafts import --kind application_form --application ID --input form.json --request-id UNIQUE_ID
```

Use its returned draft ID for all subsequent versions:

```text
cv-tailor --json drafts revise --kind application_form --application ID --parent LATEST_DRAFT_ID --input form.json --request-id NEW_UNIQUE_ID
cv-tailor --json forms check LATEST_DRAFT_ID
```

Keep `session_id`, selected manifests and original values when revising. Reuse a request ID only for an identical retry. Checkpoint after each completed step and before a human handoff or interruption. On resume, load the last checkpoint's `metadata.structured_content`, inspect the live page again and remap fields by step, section, entry and label. Reconcile user edits, changed options and new required controls; never replay saved clicks. If the profile, application revision or selected document changed, review the relevant answers and update the checkpoint's bindings only after reinspection. Preparing a new document produces a new manifest through `forms prepare`; keep the active session ID when adopting that manifest.

Fill supported controls through the host tools. Re-read the exact text, selected option labels, checked states and files from a fresh observation after filling. Set `observed_at` to the actual observation time with timezone. A screenshot that cannot establish a value is `unreadable`, not success. Never populate `observed_value` from `proposed_value`. A missing control is `missing`; reconcile it before continuing. For files, verify filename, size and SHA-256 when the host exposes them; otherwise leave the attachment unverified for the user. `forms check` validates reported observations; it does not independently inspect a browser or guarantee factual accuracy.

Repeat the required-field inventory until a pass adds no controls and reports no unresolved required fields or portal errors. Read and verify before each clearly nonfinal Next/Save/Continue action. Stop at ambiguous actions that might submit. Do not press Enter in a single-line field or use broad “Apply” clicks as a navigation shortcut. Leave login, CAPTCHA and final consent to the user. These are operating rules for the host agent, not an absolute technical submission interlock.

Show the resulting state, copyable answers, selected attachments, and every unresolved item. `drafted` and `partially_filled` do not mean ready. `verified_for_review` means the recorded live observations passed deterministic checks, subject to any warnings. Leave the form open for user review and submission. Never submit or contact the employer in this workflow.

## Record the user's submission

Only after the user explicitly confirms they submitted, refresh the application revision and run:

```text
cv-tailor --json forms confirm-submission LATEST_DRAFT_ID --revision CURRENT_REVISION --on YYYY-MM-DD --user-confirmed --request-id UNIQUE_ID
```

Use the actual submission date in the user's timezone; ask if unclear. This atomically creates a confirmation checkpoint and marks the application Applied. It never sends a form. The checkpoint records last observed values, since manual edits after observation may differ. Do not mark Applied merely because answers were drafted, copied, filled or handed over. `drafts apply` remains a separate operation for selecting current CV/cover-letter documents.
