# Release validation

Automated tests cover path/URL boundaries and encoding, root precedence, malformed
roots, confirmation invalidation, ES parsing/failures, edit preservation, exports,
HTML escaping, formula protection, atomic persistence, tampered URLs, Qt table
edit roles, keyboard interaction, worker delivery and clipboard MIME types.
These do not establish live third-party compatibility.

Before publishing v0.1.0, use disposable authorized data outside Git:

- Start Everything/ES on Windows. Configure the executable and retry IPC.
- Search an indexed synced folder with nested Unicode files, custom/all extensions,
  literal filename text and low limits. Verify boundaries, counts and no directories.
- Edit a catalog, search again and remove a file externally. Confirm edits and
  missing entries remain. ShareCatalog must never modify original documents.
- Configure overlapping libraries and test root precedence. Open every mapping's
  sample in the browser and confirm the exact document, not an authentication page.
- Verify unresolved/unconfirmed selected entries block all export methods.
- Individually review links, then change mappings and confirm reviews reset.
- Paste into the target Confluence editor, inspect the table and follow its links.
  Record editor/version and browser used.
- Check CSV in Excel for Unicode, multiline cells and formula-like titles; inspect HTML.
- Save/reopen projects and exercise Save/Discard/Cancel and denied destinations.
- Run the complete packaged app on clean Windows without Python. Check no console,
  expected DLLs/notices, and external Everything/ES setup.

Record live results before claiming release acceptance. Sample confirmation does
not guarantee every catalog link. Mocked tests cannot replace these checks.

## OneDrive detection revision

- 66 automated tests passed, including longest-root selection, duplicate handling,
  conflict rejection, root space encoding and detection without filesystem calls.
- GUI tests cover candidate review before applying and sample text input without
  an Explorer file picker. Ruff checks and the repository text check passed.
- The corrected registry-only PowerShell diagnostic was run on a nonexistent
  fictional input path. It made no file lookup and reported no registered provider
  in the execution account. It still needs a target-user OneDrive test.
- Live Files On-Demand no-hydration behavior and the generated sample browser link
  need confirmation on the actual target installation. The first diagnostic was
  observed to download a file; its Shell queries and native file picker were removed.

## Development verification, November 13, 2026

- Windows, Python 3.11.9: 56 pytest tests passed, including offscreen GUI tests.
- Ruff lint/format and the repository punctuation check passed.
- The real `python -m sharecatalog` entry point opened a native Windows window.
- A PyInstaller one-directory, windowed executable was built locally.
- The packaged executable opened a native window; its PE subsystem is Windows GUI.
- Everything/ES was not installed in this environment. Real indexed search,
  authenticated SharePoint sample links, Confluence paste, Excel display and
  clean-machine executable distribution remain unverified.

`python scripts/smoke_windows.py` checks source startup on Windows.
Add `--packaged` to check the built executable. The smoke script detects a new
native window and terminates only its startup process; it does not exercise a
catalog workflow or save user preferences. GUI tests separately cover normal close.
