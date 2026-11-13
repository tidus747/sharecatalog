from dataclasses import asdict

import pytest

from sharecatalog.models.document import LinkStatus
from sharecatalog.services.project_store import load_project, project_from_data, save_project


def test_roundtrip_and_refresh_preserve_edits(project, tmp_path):
    document = project.documents[0]
    document.title = "Edited title"
    document.description = "Multiline\ndescription 日本"
    document.included = False
    document.link_status = LinkStatus.REVIEWED
    project.refresh([document.local_path, r"C:\Catalog\Nested\Guide.pdf"])
    project.refresh([])
    assert len(project.documents) == 2
    assert document.title == "Edited title"
    assert document.link_status == LinkStatus.REVIEWED
    path = tmp_path / "catalog.sharecatalog.json"
    save_project(path, project)
    restored = load_project(path)
    assert asdict(restored) == asdict(project)
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(schema_version=2),
        lambda d: d.update(schema_version=True),
        lambda d: d.update(documents="bad"),
        lambda d: d["documents"][0].update(included="yes"),
        lambda d: d["documents"][0].update(original_filename="Forged.pdf"),
        lambda d: d["documents"].append(d["documents"][0]),
        lambda d: d["mappings"][0].update(library_url="javascript:alert(1)"),
    ],
)
def test_invalid_data(project, mutation):
    data = asdict(project)
    mutation(data)
    with pytest.raises(ValueError):
        project_from_data(data)


def test_untrusted_stored_urls_rebuilt(project):
    data = asdict(project)
    data["documents"][0].update(
        sharepoint_url="javascript:alert(1)", link_status=LinkStatus.REVIEWED
    )
    restored = project_from_data(data)
    assert restored.documents[0].sharepoint_url.startswith("https://contoso.sharepoint.com/")
    assert restored.documents[0].link_status == LinkStatus.MAPPED


def test_invalid_json_and_failed_atomic_write(project, tmp_path, monkeypatch):
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        load_project(path)

    def fail(*args):
        raise OSError("simulated failure")

    monkeypatch.setattr("os.replace", fail)
    with pytest.raises(OSError):
        save_project(path, project)
    assert path.read_text() == "{"
    assert not list(tmp_path.glob("*.tmp"))
