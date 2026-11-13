import json
import subprocess
from pathlib import Path

import pytest

from sharecatalog.services.everything import (
    EverythingAdapter,
    EverythingError,
    parse_extensions,
    parse_output,
)


def stub_results(monkeypatch, rows, code=0):
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        switch = "-export-json" if "-export-json" in arguments else "-export-csv"
        path = Path(arguments[arguments.index(switch) + 1])
        path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        return subprocess.CompletedProcess(arguments, code, b"", b"")

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_search_filters_deduplicates_and_keeps_duplicate_names(monkeypatch):
    rows = [
        {"Name": "Guide.pdf", "Path": r"C:\Catalog"},
        {"Name": "Guide.pdf", "Path": r"c:\CATALOG"},
        {"Name": "Guide.pdf", "Path": r"C:\Catalog\Nested"},
        {"Name": "Guide.pdf", "Path": r"C:\CatalogOther"},
        {"Name": "Guide.txt", "Path": r"C:\Catalog"},
        {"Name": "Folder\\", "Path": r"C:\Catalog"},
    ]
    calls = stub_results(monkeypatch, rows)
    result = EverythingAdapter("es.exe").search(r"C:\Catalog", "pdf", "guide", 100)
    assert len(result.paths) == 2
    args, kwargs = calls[0]
    assert kwargs["shell"] is False
    assert "/a-d" in args and "-export-json" in args and "ext:pdf" in args
    assert "-path" in args and "100" in args
    assert not result.limit_reached


def test_empty_and_limit(monkeypatch):
    stub_results(monkeypatch, [])
    assert EverythingAdapter("es.exe").search(r"C:\Catalog").paths == []
    stub_results(monkeypatch, [{"Name": "Guide.pdf", "Path": r"C:\Catalog"}])
    assert EverythingAdapter("es.exe").search(r"C:\Catalog", limit=1).limit_reached


@pytest.mark.parametrize("code", [7, 8, 4])
def test_ipc_and_cli_failure(monkeypatch, code):
    stub_results(monkeypatch, [], code)
    with pytest.raises(EverythingError):
        EverythingAdapter("es.exe").search(r"C:\Catalog")


def test_missing_and_timeout(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(EverythingError, match="not found"):
        EverythingAdapter().probe()

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("es.exe", 30)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(EverythingError, match="timed out"):
        EverythingAdapter("es.exe").probe()


def test_csv_fallback(monkeypatch):
    def run(arguments, **kwargs):
        if "-export-json" in arguments:
            return subprocess.CompletedProcess(arguments, 6)
        Path(arguments[arguments.index("-export-csv") + 1]).write_text(
            "Name,Path\nGuide.pdf,C:\\Catalog\n", encoding="utf-8"
        )
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(subprocess, "run", run)
    assert EverythingAdapter("es.exe").search(r"C:\Catalog").paths == [r"C:\Catalog\Guide.pdf"]


def test_output_and_extension_validation():
    assert parse_output('[{"filename":"C:\\\\Catalog\\\\Guide.pdf"}]')
    assert parse_output("Name,Path\nGuide.pdf,C:\\Catalog\n", "csv") == [r"C:\Catalog\Guide.pdf"]
    for text in ("{}", "[{}]", "garbage", "[null]"):
        with pytest.raises(EverythingError):
            parse_output(text)
    assert parse_extensions("*") == set()
    assert parse_extensions(".PDF;docx,md") == {"pdf", "docx", "md"}
    with pytest.raises(ValueError):
        parse_extensions("pdf|folder:")
