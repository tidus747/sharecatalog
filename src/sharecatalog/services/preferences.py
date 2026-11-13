import json
from dataclasses import asdict, dataclass
from pathlib import Path

from sharecatalog.services.project_store import atomic_write


@dataclass
class Preferences:
    executable: str = ""
    result_limit: int = 10000
    width: int = 1250
    height: int = 780

    @classmethod
    def load(cls, path: Path) -> "Preferences":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or not isinstance(data.get("executable"), str)
                or any(type(data.get(k)) is not int for k in ("result_limit", "width", "height"))
                or not 1 <= data["result_limit"] <= 100000
                or not 400 <= data["width"] <= 10000
                or not 300 <= data["height"] <= 10000
            ):
                return cls()
            return cls(**data)
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, json.dumps(asdict(self), indent=2) + "\n")
