"""Lexical Windows paths, usable on every test platform without touching documents."""

import ntpath
import re


def normalize_path(value: str) -> str:
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ValueError("A nonempty absolute Windows path is required.")
    value = value.replace("/", "\\")
    if value.startswith(("\\\\?\\", "\\\\.\\")):
        raise ValueError("Device and extended paths are not supported.")
    drive, tail = ntpath.splitdrive(value)
    if not (re.fullmatch(r"[A-Za-z]:", drive) or drive.startswith("\\\\")):
        raise ValueError("Use an absolute drive or UNC path.")
    if not tail.startswith("\\") or any(c in tail for c in ':*?"<>|'):
        raise ValueError("Invalid absolute Windows path.")
    parts = tail.split("\\")
    if any(p not in ("", ".", "..") and p.endswith((" ", ".")) for p in parts):
        raise ValueError("Ambiguous trailing spaces or dots in a Windows path.")
    return ntpath.normpath(value)


def path_key(value: str) -> str:
    return normalize_path(value).casefold()


def relative_path(path: str, root: str) -> str | None:
    path, root = normalize_path(path), normalize_path(root)
    try:
        if ntpath.commonpath([path.casefold(), root.casefold()]) != root.casefold():
            return None
    except ValueError:
        return None
    result = ntpath.relpath(path, root)
    return result if result != "." else None
