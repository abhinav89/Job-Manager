---
name: cv-code-practice
description: Run coding interview exercises, give progressive hints, explain errors, and review solutions. Use for Python interview practice and role-relevant coding exercises.
---

# cv-code-practice

Get built-in exercises using `cv-tailor --json practice problems` or `practice problems --id ID`. Generate additional exercises yourself using the job and `schema code_problems`; do not call CV Tailor AI endpoints.
Let the user attempt the problem. Offer increasingly specific hints when asked, preserving the opportunity to solve it. Run Python with `practice run --input /absolute/path/solution.py --stdin "input"`. The default native executor runs with the user's OS permissions and bounded time/output; retain the configured execution backend.
Use actual output to explain errors and review correctness and complexity. Follow `schema code_review` for a saved review. Persist exercises/reviews using `practice save --kind code_problems|code_review --application ID --input file.json --request-id UNIQUE_ID`. Never claim code passed unless execution and checks support it.

Commands accept `--json` and `--data-dir`. Activate the repository virtual environment first; see the root AGENTS.md for executable paths. Use file/stdin JSON to avoid shell escaping errors.
