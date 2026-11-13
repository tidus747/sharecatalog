# Install ShareCatalog

ShareCatalog is a Windows desktop application. This website is its documentation;
your documents are never processed by the website.

## Requirements

- Windows 10 or 11. Use a Windows version supported by your organization.
- Python 3.11 or newer, preferably 64-bit.
- Everything installed, running, and already indexing your synchronized directory.
- The separate Everything command-line client, `es.exe`.
- A OneDrive-synchronized SharePoint library and browser access to its documents.

ShareCatalog itself needs no administrator access, Microsoft Graph permissions,
Confluence API token, or account of its own.

## Install from source

Install Python from [python.org](https://www.python.org/downloads/windows/).
Clone the repository, then run these commands in PowerShell:

```powershell
git clone https://github.com/tidus747/sharecatalog.git
cd sharecatalog
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m sharecatalog
```

If Python 3.11 is not installed but a newer supported version is, substitute its
version in the `py` command. Activating the virtual environment is optional when
you use the explicit interpreter path shown above.

## Configure Everything

Install [Everything](https://www.voidtools.com/downloads/) and download the separate
[ES command-line client](https://www.voidtools.com/support/everything/command_line_interface/).
Extract `es.exe` into a directory you control. Do not place either binary in the
ShareCatalog source repository.

1. Start Everything and wait for its index to be ready.
2. Open ShareCatalog's **Settings**.
3. Select your `es.exe`, or leave the field empty to detect it from PATH.
4. Set a maximum result count if needed.
5. Save settings and click **Retry connection**.

An IPC error usually means the Everything search client is not running or cannot
be contacted in the current session. ShareCatalog does not recursively scan files
when the index is unavailable.

## Connect a library

Select a synchronized directory in the search section. Open **Configure mappings**
and click **Detect from OneDrive**. Review the proposed local root and SharePoint
library root before saving. Detection reads registry metadata only; it does not
access synchronized files.

You can also enter a mapping manually. A library URL is a direct root such as
`https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents`, not an
`AllItems.aspx` view or a tokenized sharing link.

Select a sample catalog row, click **Test Mapping**, accept or paste its existing
file path, and open the generated URL. Confirm only after the correct document
opens. The sample supports the mapping; other documents remain unreviewed.

## Next steps

Search by directory, extension and optional filename text. Edit document titles
and descriptions, check the entries you want, then copy or export the catalog.
Save your project outside the repository as `.sharecatalog.json` to continue later.

The documentation index includes dedicated guides for your first catalog,
SharePoint mappings, Confluence export, troubleshooting and Windows packaging.
