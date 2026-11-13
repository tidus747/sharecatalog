import pytest

from sharecatalog.services.onedrive import DiscoveryError, discover_mapping
from sharecatalog.services.sharepoint import mapped_url, mapping_confirmed, validate_library_url

ROOT = r"C:\Users\Example\OneDrive - Contoso"
LIBRARY = ROOT + r"\Shared documents - Engineering"
GENERAL_URL = "https://contoso-my.sharepoint.com/personal/example_contoso_com/Documents/"
LIBRARY_URL = "https://contoso.sharepoint.com/sites/Engineering/Documentos compartidos/"


def test_specific_library_wins_and_spaces_are_encoded():
    mapping = discover_mapping(
        LIBRARY + r"\Planning",
        [
            (ROOT, GENERAL_URL),
            (LIBRARY, LIBRARY_URL),
            (ROOT, GENERAL_URL),
        ],
    )
    assert mapping.local_root == LIBRARY
    assert mapping.library_url.endswith("/Documentos%20compartidos")
    assert mapped_url(mapping, LIBRARY + r"\Planning\Guide #1.pdf").endswith(
        "/Documentos%20compartidos/Planning/Guide%20%231.pdf"
    )
    assert not mapping_confirmed(mapping)


def test_deduplicate_case_paths_and_encoded_urls():
    mapping = discover_mapping(
        LIBRARY,
        [
            (LIBRARY.lower(), LIBRARY_URL),
            (LIBRARY, LIBRARY_URL.replace(" ", "%20").rstrip("/")),
        ],
    )
    assert mapping is not None


def test_boundaries_and_no_result():
    assert discover_mapping(LIBRARY + "Other", [(LIBRARY, LIBRARY_URL)]) is None
    assert discover_mapping(r"D:\Unrelated", [(LIBRARY, LIBRARY_URL)]) is None


@pytest.mark.parametrize(
    "specific_urls",
    [
        [LIBRARY_URL, "https://contoso.sharepoint.com/sites/Other/Documents"],
        ["https://contoso.sharepoint.com/:b:/s/Engineering/token"],
        ["https://contoso.sharepoint.com/sites/Engineering/Documents/Forms/AllItems.aspx"],
    ],
)
def test_ambiguous_or_invalid_specific_entry_blocks_parent(specific_urls):
    pairs = [(ROOT, GENERAL_URL)] + [(LIBRARY, url) for url in specific_urls]
    with pytest.raises(DiscoveryError):
        discover_mapping(LIBRARY + r"\Planning", pairs)


def test_detection_never_touches_the_filesystem(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Synced file access is forbidden during detection")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("os.stat", forbidden)
    monkeypatch.setattr("os.scandir", forbidden)
    monkeypatch.setattr(
        "sharecatalog.services.onedrive.read_registry_pairs", lambda: [(LIBRARY, LIBRARY_URL)]
    )
    assert discover_mapping(LIBRARY + r"\Not downloaded").local_root == LIBRARY


def test_raw_and_encoded_root_spaces_have_same_canonical_url():
    assert validate_library_url(LIBRARY_URL) == validate_library_url(
        LIBRARY_URL.replace(" ", "%20")
    )
    assert validate_library_url(GENERAL_URL).startswith("https://contoso-my.sharepoint.com/")
