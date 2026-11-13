import pytest

from sharecatalog.models.library import LibraryMapping
from sharecatalog.services.paths import normalize_path
from sharecatalog.services.sharepoint import (
    MappingResolver,
    confirm_mapping,
    mapped_url,
    mapping_confirmed,
    validate_library_url,
)


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        ("Guide.pdf", "Guide.pdf"),
        (r"Nested\Guide.pdf", "Nested/Guide.pdf"),
        ("Space name.pdf", "Space%20name.pdf"),
        ("Español 日本.pdf", "Espa%C3%B1ol%20%E6%97%A5%E6%9C%AC.pdf"),
        ("A#%&+.pdf", "A%23%25%26%2B.pdf"),
        ("Already%20named.pdf", "Already%2520named.pdf"),
    ],
)
def test_relative_encoding(mapping, relative, expected):
    assert mapped_url(mapping, "C:\\Catalog\\" + relative) == mapping.library_url + "/" + expected


def test_case_insensitive_and_most_specific(mapping):
    nested = LibraryMapping(
        r"C:\Catalog\Nested", "https://contoso.sharepoint.com/sites/Other/Documents"
    )
    resolver = MappingResolver([mapping, nested])
    assert resolver.resolve(r"c:\CATALOG\nested\Guide.pdf") == (
        nested.library_url + "/Guide.pdf",
        nested.id,
    )
    assert resolver.resolve(r"C:\CatalogOther\Guide.pdf") == ("", "")
    assert resolver.resolve(r"D:\Catalog\Guide.pdf") == ("", "")
    assert resolver.resolve(r"C:\Catalog\..\Elsewhere\Guide.pdf") == ("", "")


def test_root_encoding_is_preserved():
    root = "https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents"
    assert validate_library_url(root) == root


@pytest.mark.parametrize(
    "url",
    [
        "file:///C:/Catalog",
        "http://contoso.sharepoint.com/sites/A/Documents",
        "https://example.com/sites/A/Documents",
        "https://contoso.sharepoint.com",
        "https://contoso.sharepoint.com/sites/A/Documents/Forms/AllItems.aspx",
        "https://contoso.sharepoint.com/:b:/s/Engineering/token",
        "https://contoso.sharepoint.com/sites/A/Documents?e=token",
        "https://contoso.sharepoint.com/sites/A/Documents#fragment",
        "https://user@contoso.sharepoint.com/sites/A/Documents",
        "https://contoso.sharepoint.com:bad/sites/A/Documents",
        "https://contoso.sharepoint.com/sites/A/%GG",
        "https://contoso.sharepoint.com/sites/A/%2e%2e",
        "https://contoso.sharepoint.com/sites/A/foo%2fbar",
    ],
)
def test_reject_invalid_roots(url):
    with pytest.raises(ValueError):
        validate_library_url(url)


def test_confirmation_invalidated_when_mapping_changes(mapping):
    sample = r"C:\Catalog\Guide.pdf"
    confirm_mapping(mapping, sample, mapped_url(mapping, sample))
    assert mapping_confirmed(mapping)
    mapping.library_url = "https://contoso.sharepoint.com/sites/Other/Documents"
    assert not mapping_confirmed(mapping)
    with pytest.raises(ValueError):
        confirm_mapping(mapping, r"C:\Elsewhere\Guide.pdf", "https://example.com")


def test_unc_and_invalid_windows_paths():
    assert normalize_path(r"\\server\share\folder\..\Guide.pdf") == r"\\server\share\Guide.pdf"
    for value in (
        "relative",
        r"C:relative",
        r"\\?\C:\Catalog",
        r"C:\Catalog\File:stream",
        r"C:\Folder.\Guide.pdf",
    ):
        with pytest.raises(ValueError):
            normalize_path(value)


def test_duplicate_roots_rejected(mapping):
    with pytest.raises(ValueError):
        MappingResolver([mapping, LibraryMapping(r"c:\catalog", mapping.library_url)])
