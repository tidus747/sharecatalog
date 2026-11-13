# Mapping libraries safely

Choose the actual synchronized library directory and obtain its direct HTTPS library
path from SharePoint. Explorer folder names cannot identify a library URL. Do not
strip tokens from sharing links and assume the result is a library root.

Paths compare case-insensitively at directory boundaries. `C:\Catalog` does not
match `C:\CatalogOther`. Nested mappings win. Each relative segment is encoded
as UTF-8. Literal `%20` in a filename becomes `%2520`; `%20` in a root remains encoded
once. Unicode, spaces, `#`, `%`, `&`, and `+` are supported. Windows forbids `?` in
local filenames. Invalid/ambiguous Windows path syntax is rejected. Query strings,
fragments, view pages and sharing-token URLs cannot be roots.

Use **Detect from OneDrive** to prefill a candidate for the current search directory.
Detection reads only `MountPoint` and `UrlNamespace` from the current Windows user's
registry, merges equivalent entries and proposes the most specific root. Conflicting
or unsupported entries at that root block fallback to a broader OneDrive root.
Apply and save explicitly; detection does not confirm the mapping. Registry fields
are undocumented implementation details and may be missing, stale or misleading
for shortcuts. Root path spaces are encoded automatically.

Select an existing catalog row or paste a sample path, open the generated URL and confirm the correct
document opens. Confirmation becomes available only after opening the browser.
The project stores sample path, exact generated URL and UTC confirmation time.
Changed mappings need new confirmation. Test every library used in an export.

States: mapped but not individually reviewed, individually reviewed by user, and
unmapped/invalid. No state asserts remote verification. Opening a link does not
mark it reviewed. Users confirm review in the context menu; reviews can become stale.

Shortcuts, junctions, renamed folders and unusual tenant layouts can invalidate
lexical mappings. Use dedicated mappings, representative samples and individual
inspection. Custom domains and device-prefixed paths are unsupported. No Graph
authentication, HTTP probing, sharing-token creation or permission changes occur.
