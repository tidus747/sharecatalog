import csv
import html
import io

from sharecatalog.models.document import DocumentEntry, LinkStatus
from sharecatalog.models.project import Project
from sharecatalog.services.sharepoint import MappingResolver, mapping_confirmed


class ExportError(ValueError):
    pass


def selected_documents(project: Project) -> list[DocumentEntry]:
    selected = [d for d in project.documents if d.included]
    if not selected:
        raise ExportError("Select at least one document to export.")
    resolver = MappingResolver(project.mappings)
    mappings = {m.id: m for m in project.mappings}
    for document in selected:
        url, mapping_id = resolver.resolve(document.local_path)
        if (
            not url
            or document.sharepoint_url != url
            or document.mapping_id != mapping_id
            or document.link_status == LinkStatus.UNMAPPED
        ):
            raise ExportError(
                "Selected documents include unresolved links. Correct mappings or exclude them."
            )
        if not mapping_confirmed(mappings[mapping_id]):
            raise ExportError(
                "Test and manually confirm a sample for every selected library before export."
            )
    return selected


def html_table(project: Project) -> str:
    rows = []
    for document in selected_documents(project):
        title, description, url = (
            html.escape(value, quote=True)
            for value in (document.title, document.description, document.sharepoint_url)
        )
        rows.append(
            f"<tr><td>{title}</td><td>{description.replace(chr(10), '<br>')}</td>"
            f'<td><a href="{url}">Open document</a></td></tr>'
        )
    return (
        '<table border="1" cellpadding="7" cellspacing="0"><thead><tr>'
        "<th>Document</th><th>Description</th><th>SharePoint Link</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def plain_text(project: Project) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t")
    writer.writerow(["Document", "Description", "SharePoint Link"])
    writer.writerows(
        (d.title, d.description, d.sharepoint_url) for d in selected_documents(project)
    )
    return output.getvalue()


def spreadsheet_safe(value: str) -> str:
    if value.lstrip(" \t\r\n\ufeff").startswith(("=", "+", "-", "@")) or value.startswith(
        ("\t", "\r", "\n")
    ):
        return "'" + value
    return value


def csv_text(project: Project) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Document", "Description", "SharePointURL"])
    writer.writerows(
        tuple(spreadsheet_safe(v) for v in (d.title, d.description, d.sharepoint_url))
        for d in selected_documents(project)
    )
    return output.getvalue()


def html_document(project: Project) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>ShareCatalog</title><style>body{font:15px system-ui;margin:2rem;color:#243248}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;"
        "padding:12px;text-align:left;overflow-wrap:anywhere}th{background:#eff4fa}"
        "a{color:#1756a9}</style></head><body><h1>Document catalog</h1>"
        + html_table(project)
        + "</body></html>"
    )
