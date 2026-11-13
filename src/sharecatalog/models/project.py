from dataclasses import dataclass, field

from sharecatalog.models.document import DocumentEntry
from sharecatalog.models.library import LibraryMapping
from sharecatalog.services.paths import path_key
from sharecatalog.services.sharepoint import MappingResolver


@dataclass
class Project:
    schema_version: int = 1
    search_directory: str = ""
    extensions: str = "pdf,docx,xlsx,pptx,txt,csv,md"
    filename_filter: str = ""
    mappings: list[LibraryMapping] = field(default_factory=list)
    documents: list[DocumentEntry] = field(default_factory=list)

    def refresh(self, paths: list[str]) -> int:
        """Merge search results. Retain absent entries and every user edit."""
        existing = {path_key(d.local_path): d for d in self.documents}
        added = 0
        resolver = MappingResolver(self.mappings)
        for path in paths:
            key = path_key(path)
            if key not in existing:
                entry = DocumentEntry.from_path(path)
                self.documents.append(entry)
                existing[key] = entry
                added += 1
        for entry in self.documents:
            resolver.apply(entry)
        return added
