# Copy to Confluence and export

Every export uses checked catalog entries. Resolve or exclude unmapped documents
and manually confirm a sample for each selected library before proceeding.

## Copy for Confluence

Click **Copy for Confluence**, then paste into the Confluence rich-text editor.
The clipboard includes both HTML and plain text. The HTML contains a table with
real hyperlink anchors, not local `file://` paths.

| Document | Description | SharePoint Link |
| --- | --- | --- |
| Calibration reference | Fictional example of an editable description | Open document |

The example above illustrates the column structure. It is not a link to a real
document. ShareCatalog uses your generated SharePoint URLs in the actual export.

Inspect the pasted table and follow representative links before publishing.
Confluence editors and paste handling vary; compatibility with every version has
not been established. If rich paste is unavailable, use the plain-text fallback
or export HTML and inspect it in a browser.

## CSV

**Export CSV** writes UTF-8 with a byte order mark for Excel compatibility:

```text
Document,Description,SharePointURL
```

CSV quoting preserves commas, quotes and multiline descriptions. Potentially
executable spreadsheet cells receive a leading apostrophe, including formula-like
titles beginning with `=`, `+`, `-` or `@`. This protection changes the export only,
not the saved document data. Check display in the spreadsheet application you use.

## Standalone HTML

**Export HTML** creates a complete HTML document with a clean table and clickable
links. It contains no external CSS or JavaScript dependencies. Titles,
descriptions and link attributes are escaped.

## Export failures and sensitive data

If a selected entry has an unresolved link or uses an unconfirmed mapping, the
entire export is blocked with an explanation. ShareCatalog does not quietly export
an invalid entry as a working link. Uncheck the entry or correct its mapping.

Save exports outside Git, for example in the ignored `exports/` directory. Exported
filenames, descriptions and URLs can reveal internal information. Copying a link
does not grant its recipient access to the document or change sharing permissions.
