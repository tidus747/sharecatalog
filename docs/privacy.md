# Privacy and practical limits

ShareCatalog operates locally. It has no telemetry, analytics, remote backend,
automatic uploads, account system, document extraction or credential storage.
It does not create sharing links or change document permissions.

## Where your data goes

- Everything queries use local IPC through the external `es.exe` client.
- Detection reads current-user OneDrive registry mapping metadata only.
- Opening a document link launches your browser and its normal authenticated session.
- Project JSON and CSV/HTML exports are saved only to the destination you choose.
- Clipboard contents are available to other applications through the OS clipboard.
- Preferences store window size, result limit and the ES executable path in Qt's
  user-specific application configuration directory.

Search output briefly exists in a temporary file and is deleted after the query.
A crash can leave that file in the OS temporary directory. Projects, exports and
clipboard content can contain sensitive paths, filenames, descriptions and URLs.
No application file logging is enabled by default. Interactive OS save errors may
include their destination path.

## Documents and Files On-Demand

The application does not rename, move, edit or request the contents of original
documents. Registry detection does not access synchronized files. Sample validation
checks existence through filesystem metadata and uses a browser action only after
you request it. Native Windows/OneDrive components can have side effects, which is
why Shell metadata queries and native sample file picking were removed.

These implementation checks are not a blanket guarantee about every installed
provider, sync state or browser configuration. Validate the behavior you depend on
in your actual Windows environment.

## Generated links are not remotely verified

A deterministic mapping is useful only when the local and remote folder structure
correspond. Sample confirmation is a user assertion about one document. Other
links remain unreviewed, and reviewed links can become stale after a move or
permission change. Importing someone else's project does not prove their reviews.

Custom domains, ambiguous shortcuts and unusual sync layouts may require manual
configuration or be unsupported. A future Graph integration could retrieve the
authoritative `driveItem.webUrl`; it is not part of v0.1.

## This documentation website

The website is static and hosted on GitHub Pages. It has no document upload or
account form. Fonts and assets are served with the site, with no third-party font
requests. Noir/Paper preference uses browser local storage. GitHub's hosting
infrastructure handles ordinary HTTP requests under its own policies.
