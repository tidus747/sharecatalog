import csv
import io

import pytest

from sharecatalog.models.document import DocumentEntry
from sharecatalog.services.exporter import (
    ExportError,
    csv_text,
    html_document,
    html_table,
    plain_text,
    spreadsheet_safe,
)


def test_exports_escape_and_select(project):
    project.documents[0].title = '<script>"&'
    project.documents[0].description = "Line one\n<Line two>"
    excluded = DocumentEntry.from_path(r"C:\Other\Private.pdf")
    excluded.included = False
    project.documents.append(excluded)
    table = html_table(project)
    assert "<script>" not in table
    assert "&lt;script&gt;&quot;&amp;" in table
    assert '<a href="https://' in table and "<br>" in table
    assert "Private" not in table
    assert "<!doctype html>" in html_document(project)
    assert "SharePoint Link" in plain_text(project)
    rows = list(csv.reader(io.StringIO(csv_text(project))))
    assert rows[0] == ["Document", "Description", "SharePointURL"]
    assert rows[1][0] == '<script>"&'


@pytest.mark.parametrize("value", ["=SUM(1,2)", "+1", "-1", "@cmd", "  =1", "\t=1", "\ntext"])
def test_formula_safety(project, value):
    project.documents[0].title = value
    rows = list(csv.reader(io.StringIO(csv_text(project))))
    assert rows[1][0] == "'" + value
    assert project.documents[0].title == value
    assert spreadsheet_safe("Ordinary title") == "Ordinary title"


def test_unresolved_unconfirmed_and_tampered_blocked(project):
    project.documents.append(DocumentEntry.from_path(r"C:\Other\Guide.pdf"))
    with pytest.raises(ExportError, match="unresolved"):
        html_table(project)
    project.documents.pop()
    project.mappings[0].confirmed_at = ""
    with pytest.raises(ExportError, match="confirm"):
        csv_text(project)
    project.documents[0].sharepoint_url = "javascript:bad"
    with pytest.raises(ExportError):
        html_document(project)
    project.documents[0].included = False
    with pytest.raises(ExportError, match="at least"):
        html_table(project)
