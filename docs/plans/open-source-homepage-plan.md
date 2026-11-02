# Open-source release and homepage plan

Status: Planning only. The current hosted app remains in place until the replacement is deliberately scheduled and deployed.

## Goal

Make CV Tailor an open-source application that people can run on their own computers. Eventually replace the hosted app at [cvtailor.me](https://cvtailor.me) with a public homepage that explains the project and directs visitors to the source code and setup instructions. The future website will be informational; it will not offer the existing hosted app.

## Homepage direction

Use [NextRole](https://next-role.dev/) as a design reference: a product-focused landing page with a dark background, large editorial headings, restrained mint accents, subtle borders, a prominent app screenshot, and clear GitHub and self-hosting calls to action. Give CV Tailor its own identity, wording, and visuals.

Proposed sections:

1. **Hero:** Explain CV Tailor in one sentence, show a real product screenshot, and link to GitHub and setup instructions.
2. **Features:** Introduce CV tailoring, PDF generation and editing, cover letters, application tracking, interview practice, and the Career Agent. Describe only functionality verified in the release.
3. **How it works:** Add a profile and job description, generate a draft, review and edit it, then download the result and track the application.
4. **Product preview:** Show real screenshots or a short demo with example data, never real users' personal information.
5. **Run it yourself:** Show the tested setup steps and prerequisites, including the user's own AI API key. A terminal-style Docker Compose example fits the reference.
6. **Open source:** State the chosen license, link to the repository and contribution instructions, and explain the project's stack and privacy considerations.

Make the page responsive and accessible. Avoid promising that data never leaves the user's machine: AI features send relevant information to the configured provider, and other integrations may also use external services. Explain provider requirements and possible costs accurately.

## Self-hosting approach

Recommend Docker Compose as the main installation path, with manual developer instructions retained. The current stack includes a Next.js frontend, a FastAPI backend, PostgreSQL, and Tectonic-based PDF generation.

- Package and configure the frontend and backend, PostgreSQL, and required PDF dependencies.
- Persist database data in a named volume and document backup, restore, updates, and removal.
- Provide an example configuration with a locally generated session secret, local frontend URLs, and no real credentials.
- Document that Gemini and OpenAI can be selected for the main AI dispatcher, while the Career Agent currently requires Gemini, including for its research features.
- Review registration: the current flow requires email verification through Resend. Design a convenient local-only setup path without weakening authentication for public deployments.
- Test first-run setup from a clean environment, including database initialization, registration, AI configuration, and PDF generation. Verify startup ordering and that data survives a restart.
- Document supported platforms, prerequisites, resource needs, troubleshooting, external service requirements, and any limitations. Treat exact commands as provisional until tested.

## Prepare the open-source repository

- Choose an open-source license. MIT is permissive; AGPL is an alternative if keeping network-accessible modifications open is a priority. The choice remains open.
- Review tracked files and Git history for secrets, private information, CVs, and third-party assets before making the repository public. Address any findings before publication.
- Update the README with screenshots, a verified quick start, configuration and privacy details, backup and update instructions, and links to the homepage and license.
- Add concise contribution and issue-reporting guidance, and verify that existing automated checks are useful to contributors.
- Confirm ownership and license compatibility of dependencies, fonts, images, and other included assets.

## Eventual transition away from the hosted app

This is a later phase, not an instruction to deploy or shut down the app now.

1. Establish whether there are active users and what data they may need to retrieve.
2. Decide on a transition timeline and a practical way for users to export or retrieve their data. Communicate the change before disabling access, if applicable.
3. Prepare and test the homepage and self-hosted release before the cutover. Check links, mobile layout, privacy language, setup instructions, and the repository's public availability.
4. When explicitly scheduled, replace the deployed app at cvtailor.me with the homepage. Account for existing URLs, account access, and user data during the transition.
5. Retire the hosted backend and associated services only after the transition and data-retention decisions are complete. Verify the homepage and links after deployment.

## Decisions still needed

- Which license should the project use?
- What local account setup offers the best balance of convenience and security?
- What is the transition timeline, and how should existing users retrieve their data?
- Which screenshots or demo best represent the released product?
