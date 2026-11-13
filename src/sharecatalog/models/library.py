from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class LibraryMapping:
    local_root: str
    library_url: str
    id: str = field(default_factory=lambda: str(uuid4()))
    sample_path: str = ""
    confirmed_url: str = ""
    confirmed_at: str = ""
