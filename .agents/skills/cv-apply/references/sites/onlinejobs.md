# OnlineJobs application guide

Use for canonical HTTPS `onlinejobs.ph` or `www.onlinejobs.ph` posting URLs under `/jobseekers/job/`. Structure observed on November 5, 2026. These are navigation and field hints, not cached values, limits, account state or permission to submit. Follow the main skill's checkpoints and final user review.

## Prepare before entering the form

Draft the complete subject and message from the posting and `forms prepare` context first. Include exact subject wording or screening answers requested by the employer. Use confirmed portfolio links and personal evidence; a request for a production example requires a confirmed example. Ask for missing required facts together and keep unfinished text out of the live form. Prepare PDFs only when requested by the user or posting/form.

## Reach the intended application

If the intended compose form is already open, verify its role/URL and start with the fresh inventory below. Do not reopen the posting or re-enter Apply when resuming a confirmed target.

1. Reuse the supported browser/session. Open the posting and verify its title, active application entry and **ABOUT THE EMPLOYER** business/contact name. The scraped job may omit the employer name; resolve it from the posting before filling.
2. Use that posting's exact **APPLY FOR THIS JOB** entry. The observed entry posts routing data to `/apply`; navigating directly to `/apply` does not establish which job it belongs to. Do not read or cache hidden contact/token values.
3. Confirm the compose page's role heading matches the intended job. A closed posting, login screen, different role or unfamiliar form needs resolution before filling. **SEND EMAIL** is the final action; leave it for user review and submission. Never click it to test validation.

## Field map

Use stable selectors or their visible labels through the host's supported tools. Never reuse old element indexes, handles or pixel coordinates.

| Checkpoint key | Selector hint | Visible label | Handling |
| --- | --- | --- | --- |
| `olj/application/subject` | `#subject` | SUBJECT | Fill the prepared subject if empty. |
| `olj/application/message` | `#message` | MESSAGE | Fill the complete prepared message if empty. |
| `olj/application/contact-info` | `#contact-info-content` | CONTACT INFO | Preserve current contact details. |
| `olj/application/apply-points` | `input[name="points"]` | APPLY POINTS | Preserve; do not choose/spend an amount without the user's instruction. |

Inventory the whole application form containing subject/message in one live observation, excluding unrelated header search controls. Include any additional visible fields, exact options, required states, rendered limits/help, original values, attachments and portal errors. Do not assume these four fields are exhaustive or that a previously absent `maxlength` is still absent. If a hint is missing, duplicated or unreadable, or the layout differs, use [generic browser inspection](../browser.md) before filling.

Save the planned snapshot once, then fill the authorized empty subject/message as a batch. Preserve populated contact information and points; request approval for any proposed replacement of existing text. Inspect new conditional controls if they appear.

Independently read the complete field values, selected states and errors back from the live form once after filling. Compare against the prepared text and original preserved values, record the actual observation time, then revise the checkpoint and run `forms check`. If the complete inventory is unchanged and no errors appear, avoid another full navigation or inspection cycle. Leave **SEND EMAIL** untouched and show the draft for review.
