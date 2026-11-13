# Troubleshooting

## Files found, but links say Unmapped or invalid

Everything finds indexed local paths. It does not supply SharePoint URLs.
Configure a local-root to library-root mapping separately. Use **Configure mappings
> Detect from OneDrive** for the selected directory, review the proposal and save.
The table recalculates its links after saving mappings.

The local root must contain the files at a real directory boundary. A mapping for
`C:\Catalog` cannot resolve `C:\CatalogOther`. A nested library mapping takes
precedence over a general personal OneDrive mapping.

## Detection finds nothing or reports conflicting URLs

Run ShareCatalog as the same Windows user running OneDrive. Detection uses that
user's registry, and the relevant metadata may not exist for every sync layout.
OneDrive's registry schema is undocumented and can change.

Do not guess a URL from a display folder name or strip a token from a sharing link.
Enter a known direct library root manually and validate a sample. Conflicting or
unsupported entries at the most specific root block fallback to its parent.

## Everything connection fails

Check the executable in Settings. `es.exe` is a separate download from Everything.
Start the Everything search client and click **Retry connection**. Check that the
target directory is indexed and custom ES settings do not interfere with output.

A timeout does not trigger a recursive filesystem scan. Narrow large queries and
try again. Everything installation/index maintenance is handled outside ShareCatalog.

## The generated URL opens the wrong page

Use a direct document library root, not a site landing page, `AllItems.aspx`, or
a sharing URL. Local and web folder names may differ. Recheck the most specific
mapping, especially for shortcuts, renamed libraries and nested synced folders.

An authentication redirect or HTTP 200 is not proof that the correct document
opened. Confirm the actual document in your authenticated browser.

## A diagnostic downloaded an online-only file

The first diagnostic used a native file picker and Shell metadata calls. A user
reported that this downloaded a selected file. Those operations have been removed.
The corrected diagnostic accepts plain text paths and reads registry values only.
The application detector also avoids synced file access.

Mapping sample validation now uses a text prompt rather than the native file
picker. It checks file existence through metadata. Live Files On-Demand behavior
still needs confirmation on the target installation. See the OneDrive detection
guide for the distinction between registry detection and sample validation.

## Old entries remain after a search

This preserves saved edits. Refreshing a query merges new entries instead of
deleting documents absent from the latest results. Uncheck stale entries before
export, including entries hidden by the local table filter.

## Cannot save or export

Choose a writable destination and check whether another application has locked
the file. Projects and exports use atomic replacement. A failed write should not
replace an existing destination with partial JSON, HTML or CSV.

## Report a problem

Open an issue in the GitHub repository with your Windows/Python/ShareCatalog
versions, the action taken, expected result and actual result. Use fictional paths
and redacted screenshots. Do not attach corporate documents, real catalog files,
internal URLs, credentials or tokens.
