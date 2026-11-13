# Architecture

Services import no Qt modules. Windows paths use `ntpath` on every host platform.
`Project.refresh` identifies documents using UUID5 of normalized case-insensitive
absolute paths. It merges additions, retains missing records and edits, and resets
individual review when derived URLs or mapping identity changes.

`EverythingAdapter` detects ES on PATH or uses a configured executable. It launches
explicit argument lists with `shell=False`, bounded timeout and no Windows console.
ES exports UTF-8 JSON to an ephemeral directory, with CSV fallback for unknown-switch
exit code 6. It uses `-path`, `/a-d`, `-n`, `-timeout`, `-name`, and `-path-column`.
Output is parsed, deduplicated and checked against local boundaries and filters.
Filename text is regex-escaped for ES and matched literally after parsing. The count
describes accepted results, with a warning when the CLI limit is reached.

Switches and exit codes were checked against the official
[CLI reference](https://www.voidtools.com/support/everything/command_line_interface/)
and [ES source](https://github.com/voidtools/ES). Live checks are still necessary.
Custom ES defaults can affect behavior.

`DocumentResolver` allows future authoritative URL providers. v0.1 uses only explicit
`MappingResolver` rules. Export recomputes URLs and requires confirmed sample mappings.
Confirmation metadata is a historical user assertion, not cryptographic proof.

The Qt model exposes title/description edit roles and inclusion check roles. A proxy
sorts and filters. QThread workers run search/probe subprocesses; results merge on
the GUI thread. Mapping changes and project opening are disabled during search.
Closing waits for bounded worker completion rather than destroying a running thread.

Schema 1 validates exact typed fields, stable identities, unique IDs, enums and file
size. URLs rebuild on load so stored data cannot introduce arbitrary browser schemes.
New schemas need explicit migrations. Atomic writes use same-directory temporary
files, fsync and replacement. Failed writes leave the prior destination untouched.

Assumptions: explicit lexical Windows mappings, no shortcut/junction inference,
no document reads or writes, no network verification, no automatic sharing changes.
