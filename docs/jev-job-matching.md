# Jev job matching

The Job Search Agent can optionally use TypeSafe Jev to order discovered jobs by their relationship to the requested role, confirmed experience, and explicitly stated preferences. The chat shows the individual judgments as estimates, without numerical fit scores. Every search result remains available. A missing or incomplete profile or job description is treated as unknown, not as evidence of a gap.

Set `JEV_API_KEY` (or `TYPESAFE_API_KEY`) in the backend environment. `JEV_MODEL` optionally selects a TypeSafe model and defaults to `jev-latest`. Restart the backend after changing its environment. When no key is present, or TypeSafe is unavailable, job search still works and preserves the source order.

When enabled, relevant work history, confirmed skills, projects, education and certifications, an exact quote of job preferences when available, and job posting details are sent to TypeSafe. Name, email, telephone number, and profile links are not included as separate fields. Free-text descriptions and preferences may themselves contain personal information, so users should review what they enter. TypeSafe usage may incur charges.

Jev does not find jobs or write explanations: existing search sources provide postings, the application uses Jev's judgments to order them, and the agent should ground any explanation in the actual profile and job text. Judgments are estimates and can be wrong. Users should review the original posting before acting.
