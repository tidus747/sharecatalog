# OneDrive mapping detection and file hydration

Finding a file through Everything does not establish its SharePoint URL. No matching
configured mapping means `Unmapped or invalid`, even if Explorer can copy a link.

## Use the application

Choose your search directory and open **Configure mappings > Detect from OneDrive**.
The detector reads `MountPoint` and `UrlNamespace` under the current Windows user's
`Software\SyncEngines\Providers\OneDrive` registry branch. It does not query synced
files or invoke Explorer, COM properties, previews, or sharing commands.

The most specific matching root wins. Equivalent duplicates are merged. If that
root has conflicting or unsupported URLs, detection stops rather than falling
back to a broader personal OneDrive root. The candidate prepopulates the form;
review and save it explicitly. A browser sample still needs manual confirmation
before export. Raw spaces in the library URL are encoded automatically.

These registry fields are undocumented implementation details, not a supported
Microsoft mapping API. They can be absent, stale or unsuitable for shortcuts.
Detection proposes a mapping; it cannot establish remote accessibility.

## Corrected diagnostic script

The first diagnostic used a native file picker and queried a Shell property.
A user observed that running it downloaded an online-only file. We cannot attribute
that behavior to a particular step from this observation alone. Calling an API
without explicit writes does not ensure the storage provider leaves local state
unchanged. Microsoft documents
[automatic app downloads](https://support.microsoft.com/en-us/windows/experience/automatic-file-download-notifications-in-windows)
for online-only files.

The corrected diagnostic removes both file selection and Shell metadata queries.
It asks for a path as plain text and reads registry values only. It does not resolve,
stat, enumerate, open or read that file. You can supply a nonexistent fictional path
to exercise the same behavior. Run as your normal OneDrive Windows user:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\diagnose_onedrive.ps1
```

Paste a local file or directory path. A local window shows distinct registry
candidates ordered by specificity. The console summary omits all paths and URLs.
The script does not modify registry values, clipboard contents or sharing permissions,
write reports, or open remote URLs. Keep metadata displayed in the window private.
ExecutionPolicy Bypass applies to this process only; managed restrictions still apply.

For a noninteractive check:

```powershell
.\scripts\diagnose_onedrive.ps1 -Path 'C:\Catalog\NotDownloaded.pdf' -SummaryOnly
```

## Sample validation

The mapping test now uses plain text input instead of the Explorer file picker.
Selecting a catalog row before **Test Mapping** prefills its path. The test checks
file existence using filesystem metadata and generates the URL lexically. It does
not request document content. Opening the generated URL is a separate explicit
browser action. Registry detection itself has no synced filesystem access.

Verify actual Files On-Demand behavior on the target OneDrive installation before
claiming live no-hydration validation. Automated tests ensure the detector does
not invoke filesystem functions, but do not simulate Windows Cloud Files drivers.
