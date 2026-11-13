"""Propose mappings from local registry metadata, without accessing synced files.

These registry fields are OneDrive implementation details. Candidates always
need user acceptance and sample confirmation; they are not authoritative URLs.
"""

import sys
from collections.abc import Iterable

from sharecatalog.models.library import LibraryMapping
from sharecatalog.services.paths import normalize_path, path_key, relative_path
from sharecatalog.services.sharepoint import validate_mapping


class DiscoveryError(ValueError):
    pass


def read_registry_pairs() -> list[tuple[str, str]]:
    if sys.platform != "win32":
        raise DiscoveryError("OneDrive mapping detection is available on Windows only.")
    import winreg

    location = r"Software\SyncEngines\Providers\OneDrive"
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, location, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise DiscoveryError(
            "Cannot read OneDrive mapping metadata for this Windows user."
        ) from exc
    pairs = []
    try:
        with root:
            for index in range(winreg.QueryInfoKey(root)[0]):
                with winreg.OpenKey(root, winreg.EnumKey(root, index), 0, winreg.KEY_READ) as key:
                    try:
                        local, local_type = winreg.QueryValueEx(key, "MountPoint")
                        url, url_type = winreg.QueryValueEx(key, "UrlNamespace")
                    except FileNotFoundError:
                        continue
                    if (
                        not isinstance(local, str)
                        or not isinstance(url, str)
                        or local_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ)
                        or url_type != winreg.REG_SZ
                    ):
                        continue
                    if local_type == winreg.REG_EXPAND_SZ:
                        local = winreg.ExpandEnvironmentStrings(local)
                    pairs.append((local, url))
    except OSError as exc:
        # An incomplete read could hide a more specific root. Do not pick a parent.
        raise DiscoveryError(
            "OneDrive mapping metadata could not be read completely. Use a manual mapping."
        ) from exc
    return pairs


def discover_mapping(
    directory: str, pairs: Iterable[tuple[str, str]] | None = None
) -> LibraryMapping | None:
    """Return the most specific unambiguous candidate, with no filesystem queries.

    An invalid or conflicting specific entry blocks fallback to a broader root.
    Identical entries are merged after normalizing paths and URL encoding.
    """
    directory = normalize_path(directory)
    matching: list[LibraryMapping] = []
    for local, url in read_registry_pairs() if pairs is None else pairs:
        try:
            local = normalize_path(local)
        except ValueError:
            continue
        if path_key(local) == path_key(directory) or relative_path(directory, local) is not None:
            matching.append(LibraryMapping(local, url))
    if not matching:
        return None
    longest = max(len(m.local_root) for m in matching)
    specific = [m for m in matching if len(m.local_root) == longest]
    unique = {}
    for mapping in specific:
        try:
            validate_mapping(mapping)
        except ValueError as exc:
            raise DiscoveryError(
                "The most specific OneDrive entry has an unsupported web URL. "
                "Configure this library manually."
            ) from exc
        unique[(path_key(mapping.local_root), mapping.library_url)] = mapping
    if len(unique) != 1:
        raise DiscoveryError(
            "OneDrive reports conflicting URLs for this local root. "
            "Configure this library manually."
        )
    return next(iter(unique.values()))
