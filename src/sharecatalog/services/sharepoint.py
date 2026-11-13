"""Deterministic mapping only. This service never asserts remote accessibility."""

import re
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from sharecatalog.models.document import DocumentEntry, LinkStatus
from sharecatalog.models.library import LibraryMapping
from sharecatalog.services.paths import normalize_path, path_key, relative_path


def validate_library_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        port = parts.port
    except ValueError as exc:
        raise ValueError("Malformed SharePoint library URL.") from exc
    if (
        parts.scheme != "https"
        or not re.fullmatch(r"[A-Za-z0-9-]+\.sharepoint\.(?:com|us|de|cn)", host)
        or port not in (None, 443)
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or value != value.strip()
        or any(ord(c) < 32 for c in value)
        or "\\" in value
    ):
        raise ValueError("Use a direct HTTPS SharePoint library URL without query or fragment.")
    segments = parts.path.strip("/").split("/")
    if len(segments) < 3 or segments[0].lower() not in ("sites", "teams", "personal"):
        raise ValueError("Use a library root, such as /sites/Engineering/Shared%20Documents.")
    for segment in segments:
        if re.search(r"%(?![0-9a-fA-F]{2})", segment):
            raise ValueError("Invalid percent encoding in library URL.")
        decoded = unquote(segment, errors="strict")
        if (
            not decoded
            or decoded in (".", "..")
            or any(c in decoded for c in "/\\:")
            or any(ord(c) < 32 for c in decoded)
            or decoded.lower().endswith(".aspx")
        ):
            raise ValueError("Page-view and sharing URLs cannot be used as library roots.")
    encoded = "/" + "/".join(quote(unquote(s), safe="") for s in segments)
    return urlunsplit(("https", host.lower(), encoded, "", ""))


def validate_mapping(mapping: LibraryMapping) -> None:
    mapping.local_root = normalize_path(mapping.local_root)
    mapping.library_url = validate_library_url(mapping.library_url)


def mapped_url(mapping: LibraryMapping, path: str) -> str | None:
    relative = relative_path(path, mapping.local_root)
    if relative is None:
        return None
    return (
        validate_library_url(mapping.library_url)
        + "/"
        + "/".join(quote(segment, safe="") for segment in relative.split("\\"))
    )


def mapping_confirmed(mapping: LibraryMapping) -> bool:
    try:
        return bool(
            mapping.confirmed_at
            and mapping.sample_path
            and mapping.confirmed_url == mapped_url(mapping, mapping.sample_path)
        )
    except ValueError:
        return False


def confirm_mapping(mapping: LibraryMapping, sample_path: str, opened_url: str) -> None:
    url = mapped_url(mapping, sample_path)
    if not url or url != opened_url:
        raise ValueError("The sample must be inside this mapping and match the opened URL.")
    mapping.sample_path = normalize_path(sample_path)
    mapping.confirmed_url = url
    mapping.confirmed_at = datetime.now(UTC).isoformat()


class DocumentResolver(Protocol):
    """A future Graph resolver may retrieve driveItem.webUrl through this boundary."""

    def resolve(self, path: str) -> tuple[str, str]: ...


class MappingResolver:
    def __init__(self, mappings: list[LibraryMapping]):
        self.mappings = mappings
        seen = set()
        for mapping in mappings:
            validate_mapping(mapping)
            key = path_key(mapping.local_root)
            if key in seen:
                raise ValueError("Two mappings cannot have the same local root.")
            seen.add(key)

    def resolve(self, path: str) -> tuple[str, str]:
        for mapping in sorted(self.mappings, key=lambda m: len(m.local_root), reverse=True):
            url = mapped_url(mapping, path)
            if url:
                return url, mapping.id
        return "", ""

    def apply(self, entry: DocumentEntry) -> None:
        url, mapping_id = self.resolve(entry.local_path)
        unchanged = (entry.sharepoint_url, entry.mapping_id) == (url, mapping_id)
        entry.link_status = (
            LinkStatus.REVIEWED
            if unchanged and url and entry.link_status == LinkStatus.REVIEWED
            else LinkStatus.MAPPED
            if url
            else LinkStatus.UNMAPPED
        )
        entry.sharepoint_url, entry.mapping_id = url, mapping_id
