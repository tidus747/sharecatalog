import ntpath
from dataclasses import dataclass
from enum import StrEnum
from uuid import NAMESPACE_URL, uuid5

from sharecatalog.services.paths import normalize_path, path_key


class LinkStatus(StrEnum):
    MAPPED = "Mapped, not individually reviewed"
    REVIEWED = "Individually reviewed by user"
    UNMAPPED = "Unmapped or invalid"


@dataclass
class DocumentEntry:
    id: str
    original_filename: str
    local_path: str
    extension: str
    title: str
    description: str = ""
    sharepoint_url: str = ""
    mapping_id: str = ""
    included: bool = True
    link_status: LinkStatus = LinkStatus.UNMAPPED

    @classmethod
    def from_path(cls, path: str) -> "DocumentEntry":
        path = normalize_path(path)
        filename = ntpath.basename(path)
        return cls(
            id=str(uuid5(NAMESPACE_URL, path_key(path))),
            original_filename=filename,
            local_path=path,
            extension=ntpath.splitext(filename)[1].lstrip(".").lower(),
            title=ntpath.splitext(filename)[0],
        )
