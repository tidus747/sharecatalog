# Your first document catalog

ShareCatalog separates the original file from the description you want to publish.
Editing a title in the table never renames the document on disk.

## Search indexed files

Choose an existing local synchronized directory, then enter your filters:

| Field | Example | Behavior |
| --- | --- | --- |
| Extensions | `pdf,docx,xlsx` | Search these file types, including nested directories |
| All file types | `*` | Do not restrict extensions |
| Filename contains | `reference` | Literal case-insensitive filename substring |
| Maximum results | `10000` | Configurable in Settings, up to 100000 |

Click **Search Everything**. Search runs in a worker thread so you can continue
using the table. ShareCatalog rejects outside-root results and deduplicates
normalized absolute paths. Identical filenames in different folders remain
separate documents.

The count describes accepted results returned, not the total beyond the limit.
When a limit warning appears, narrow the filters or increase the limit. No matches
does not delete entries already in the catalog.

## Edit and select

Double-click a document title or description, or select its cell and press F2.
Original filename, extension, URL and link status are read-only. Use the Include
checkbox to choose what to export.

Click column headers to sort. The local filter narrows visible rows without
running a new Everything search. **Select All** and **Select None** affect visible
rows; exports include every checked entry, including those hidden by a filter.

The context menu can open or copy a SharePoint link, mark it manually reviewed,
and include or exclude a document. A review is your confirmation that you opened
the correct document, not an automatic network check.

## Understand link states

| State | Meaning |
| --- | --- |
| Mapped, not individually reviewed | A URL was constructed from a configured mapping |
| Individually reviewed by user | You explicitly confirmed the individual link |
| Unmapped or invalid | No usable mapping resolves this local path |

A confirmed mapping sample is required before export. Missing mappings and
individual document reviews are separate concepts: a sample does not mark every
document reviewed.

## Save and refresh

Use **Save Project** or Ctrl+S to save a `.sharecatalog.json` file. It contains
filters, mappings, titles, descriptions, selections and link review metadata.
Projects can contain sensitive paths and URLs; store them appropriately.

Running another search adds new records and preserves existing edits and
selections. A document absent from the latest search remains in the project and
may still be checked. Exclude it explicitly if it should not be exported.

Opening another project or closing with unsaved changes offers Save, Discard and
Cancel. No project is automatically saved into the source checkout.
