# ShareCatalog

ShareCatalog v0.1.0 is a Windows desktop utility for turning files indexed by
Everything into an editable catalog with SharePoint document links. Copy a table
into Confluence, export CSV or HTML, and save your work as JSON. No Microsoft Graph
permissions, Confluence tokens, administrator access, or remote service required.

**Screenshot: not yet available.**

## Features

- Background Everything CLI searches within a local synchronized directory.
- Custom extensions or all file types, literal filename text, configurable result limit.
- Explicit local-root to SharePoint-library mappings, including nested mappings.
- Sample mapping confirmation before export, plus individual link review states.
- Editable titles and descriptions, inclusion checkboxes, sorting and local filtering.
- Confluence clipboard HTML with real anchors and a plain-text fallback.
- Excel-friendly UTF-8 BOM CSV with formula protection, standalone HTML.
- Atomic, validated JSON projects; refreshed searches retain existing edits.
- Light native-widget interface, keyboard editing, remembered window size and preferences.

## Windows installation

Requirements: Windows 10/11, Python 3.11 or newer (64-bit recommended),
[Everything](https://www.voidtools.com/downloads/) installed and running, and the
separate [Everything CLI (ES)](https://www.voidtools.com/support/everything/command_line_interface/).
Everything must already index the chosen directory. Index configuration is external
to ShareCatalog. There is no recursive filesystem search fallback.

From a checkout, in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m sharecatalog
```

With the environment activated, `python -m sharecatalog` or `sharecatalog` launches
the application. No elevation is needed for ShareCatalog.

Extract `es.exe` somewhere you control. Add its folder to PATH or select it under
**Settings > Everything CLI**. Start Everything, then click **Retry connection**.
ES and Everything are external software and are never bundled in this repository
or the executable distribution. Use a current ES release; older releases fall back
to structured CSV if JSON is unsupported. Reset custom ES defaults outside this
application if they interfere with output or search behavior.

## Create and review a catalog

1. Browse to a local synchronized directory. Enter extensions such as
   `pdf,docx,xlsx,pptx,txt,csv,md`, custom extensions, or `*` for all file types.
   Filename text is a literal, case-insensitive substring, not Everything query syntax.
2. Click **Search Everything**. The count is accepted files returned, not a total
   beyond the configured limit. Narrow your search when the limit is reached.
3. Configure each library in **Configure mappings**. Local folder names do not need
   to match SharePoint names. The most specific local root wins.
4. Select a mapping and click **Test Mapping**. Choose an existing sample file, click
   **Open in Browser**, and confirm only after the correct document opens.
5. Double-click a title or description, or press F2, to edit it. Filenames and URLs
   are read-only. Use the context menu to open, copy, review, include, or exclude links.
6. Check entries to include. Select All/None applies to currently visible rows.
   Exports include **all checked catalog entries, including rows hidden by a filter**.
7. Save a `.sharecatalog.json` project outside the source checkout.

Repeated searches merge new files and preserve prior entries, titles, descriptions,
selections, and unchanged link reviews. Files absent from the latest search remain
in the project and may still be included in export. Exclude them explicitly if needed.

## SharePoint mapping and link correctness

Fictional mapping:

```text
Local: C:\Users\Example\Contoso\Engineering - Documents
Web:   https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents
File:  Calibration\Reference #1.pdf
URL:   https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents/Calibration/Reference%20%231.pdf
```

Use an HTTPS library root, not `AllItems.aspx`, a sharing-token link, a `file://`
URL, or an arbitrary copied document link. Supported hosts are tenant subdomains
of `sharepoint.com`, `sharepoint.us`, `sharepoint.de`, and `sharepoint.cn`, with
`/sites`, `/teams`, or `/personal` library paths. Root components must be valid
percent-encoded URL components. Unsupported forms are rejected conservatively.

**A generated URL is not remotely verified.** A manually confirmed sample supports
using that mapping but does not validate every document, permission, move, or sync
state. Individual links remain "Mapped, not individually reviewed" until you confirm
them. Even reviewed links can become stale. An HTTP 200 or authentication redirect
does not prove correctness; ShareCatalog performs no HTTP validation requests.
Each selected mapping needs sample confirmation before any export. Unresolved entries
block export; fix the mapping or uncheck those entries. Changing a mapping resets
its confirmation, and changed document URLs reset individual reviews.

OneDrive shortcuts, junctions, renamed folders, custom domains, and ambiguous sync
layouts cannot be discovered authoritatively in v0.1. Configure a dedicated mapping
and test a real sample. No sharing links or permissions are created or changed.
See [mapping details](docs/sharepoint-mapping.md).

## Confluence and file export

Click **Copy for Confluence** and paste into a Confluence rich-text editor. Qt puts
both `text/html` and `text/plain` on the Windows clipboard. The table contains
Document, Description, and SharePoint Link columns. Inspect pasted links before
publishing. Compatibility with every Confluence editor/version has not been tested.
CSV uses `Document,Description,SharePointURL`, quotes multiline data, and adds a
leading apostrophe to potentially executable spreadsheet cells without modifying
saved titles or descriptions. HTML exports are self-contained with no scripts
or external styles. Save exports outside the repository, for example in `exports/`
(ignored by Git).

## Privacy

No telemetry, analytics, uploads, content extraction, credentials, or remote backend.
Source documents are never renamed, moved, modified, or downloaded by ShareCatalog.
Opening a link uses your browser and its normal authentication. Selecting a sample
checks file existence only. Searches use local Everything IPC. A temporary output
file containing result paths is deleted when the search finishes; a crash may leave
it in the OS temporary directory.

Projects, exports, and clipboard contents can contain sensitive filenames, paths,
descriptions, and URLs. Treat them accordingly. Project files and common exports
are ignored by Git; arbitrary HTML files outside `exports/` are not. Preferences
store the ES executable path, result limit, and window size in Qt's user-specific
AppConfigLocation, normally `%LOCALAPPDATA%\ShareCatalog\ShareCatalog`, not the checkout.
No application file logging is enabled. OS errors shown interactively may include
the destination path of an unsuccessful save.

## Development and verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

`requirements-dev.txt` pins tested development dependencies. Package metadata allows
compatible updates. Tests mock ES output and require no tenant or Everything;
core services are platform independent. GUI tests use Qt's offscreen platform.
Windows CI is primary, with Linux checks too. Real integration testing is separate:
[manual checklist](docs/validation.md).

Structure: `src/sharecatalog/models/` contains records and merge behavior;
`services/` contains search, mapping, export, preferences, and persistence;
`ui/` contains Qt models, dialogs, and the main window; `tests/` contains regression
tests; `docs/` explains architecture, mapping, validation, and distribution.

## Build a Windows executable

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm ShareCatalog.spec
.\dist\ShareCatalog\ShareCatalog.exe
```

The one-directory build has no console window. Keep the entire directory together.
It excludes Everything/ES and does not require administrator privileges. See
[build and distribution](docs/build.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## Roadmap

- v0.1.0: Everything search, explicit mappings and sample confirmation, editable
  catalogs, CSV/HTML/clipboard export, JSON persistence.
- v0.2.0: improved mapping discovery, batch editing, OneDrive shortcut handling,
  search presets, enhanced link review.
- v1.0.0: stable UX, reliable Windows packaging, accessibility, mature tests and docs.
- Future investigation: optional Graph authoritative `driveItem.webUrl`, optional
  Confluence API, additional formats.

## Contributing and publishing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use short feature branches and pull requests.
Existing history and origin are preserved. For an unconnected checkout, create an
empty GitHub repository yourself, then:

```powershell
git remote -v
# Only when origin does not already exist:
git remote add origin https://github.com/YOUR-ACCOUNT/sharecatalog.git
git push -u origin main
```

If origin exists, review it and push intentionally, or add a new remote name. Do not
overwrite it blindly. No remote repository, tag, release, or push is created
automatically. After real integration validation, tag v0.1.0 and prepare a release
with the complete package and dependency notices.

## License

MIT, with a replaceable copyright holder placeholder in [LICENSE](LICENSE).
Third-party dependencies have separate terms, particularly Qt/PySide6. The initial
repository license was GPLv3; this implementation changes the project license to
MIT as requested by the owner. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
