"""Versioned, validated JSON persistence with same-directory atomic replacement."""

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from sharecatalog.models.document import DocumentEntry, LinkStatus
from sharecatalog.models.library import LibraryMapping
from sharecatalog.models.project import Project
from sharecatalog.services.paths import normalize_path, path_key
from sharecatalog.services.sharepoint import MappingResolver


def atomic_write(path: Path, text: str, encoding: str = "utf-8") -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, newline="", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def _record(value: object, cls: type) -> dict:
    if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
        raise ValueError("Invalid project record fields.")
    for key, field_value in value.items():
        if key == "included":
            if type(field_value) is not bool:
                raise ValueError("Invalid inclusion flag.")
        elif not isinstance(field_value, str) or len(field_value) > 1000000:
            raise ValueError("Invalid project text field.")
    return value


def project_from_data(data: object) -> Project:
    try:
        if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
            raise ValueError("Missing project schema version.")
        if data["schema_version"] != 1:
            raise ValueError("Unsupported project schema version. This release supports version 1.")
        if set(data) != set(Project.__dataclass_fields__):
            raise ValueError("Invalid project fields.")
        for name in ("search_directory", "extensions", "filename_filter"):
            if not isinstance(data[name], str):
                raise ValueError("Invalid search settings.")
        if data["search_directory"]:
            normalize_path(data["search_directory"])
        for name in ("mappings", "documents"):
            if not isinstance(data[name], list) or len(data[name]) > 100000:
                raise ValueError("Invalid project collection.")
        mappings = [LibraryMapping(**_record(m, LibraryMapping)) for m in data["mappings"]]
        if len({m.id for m in mappings}) != len(mappings) or any(not m.id for m in mappings):
            raise ValueError("Duplicate or empty mapping IDs.")
        resolver = MappingResolver(mappings)
        documents = []
        ids, paths = set(), set()
        for record in data["documents"]:
            document = DocumentEntry(**_record(record, DocumentEntry))
            document.link_status = LinkStatus(document.link_status)
            expected = DocumentEntry.from_path(document.local_path)
            if (
                document.id != expected.id
                or document.original_filename != expected.original_filename
                or document.extension != expected.extension
                or document.id in ids
                or path_key(document.local_path) in paths
            ):
                raise ValueError("Invalid or duplicate document identity.")
            ids.add(document.id)
            paths.add(path_key(document.local_path))
            # Never trust stored URL schemes or review status for a changed URL.
            resolver.apply(document)
            documents.append(document)
        return Project(
            search_directory=data["search_directory"],
            extensions=data["extensions"],
            filename_filter=data["filename_filter"],
            mappings=mappings,
            documents=documents,
        )
    except (TypeError, KeyError, UnicodeError) as exc:
        raise ValueError("Invalid ShareCatalog project data.") from exc


def save_project(path: Path, project: Project) -> None:
    data = asdict(project)
    project_from_data(data)
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_project(path: Path) -> Project:
    if path.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Project exceeds the 100 MiB safety limit.")
    try:
        return project_from_data(json.loads(path.read_text(encoding="utf-8-sig")))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("The project is not valid UTF-8 JSON.") from exc
