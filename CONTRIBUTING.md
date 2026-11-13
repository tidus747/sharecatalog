# Contributing

Use English for source, UI, comments, docs and commits. Do not use Unicode U+2014
anywhere in tracked files. Use fictional tenants/documents. Never contribute real
catalog projects, exports, credentials or organizational data.

1. Fork/clone and create a short branch: `git switch -c feat/topic`.
2. Install Python 3.11+ and pinned development requirements as in README.
3. Make a focused change and add meaningful regression tests.
4. Run `python -m ruff format .`, `python -m ruff check .`, and `python -m pytest`.
5. Update documentation/changelog as needed.
6. Commit with a conventional message, push your branch, and open a pull request.

Describe the problem, resulting behavior, validation and limitations in the PR.
Windows is primary. Services must remain testable without Windows/Everything.
Use the manual checklist for external integrations. Avoid speculative dependencies,
telemetry, uploads, document modifications, and automatic sharing changes.
