"""Everything CLI integration. No recursive filesystem search or document reads."""

import csv
import io
import json
import ntpath
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sharecatalog.services.paths import normalize_path, path_key, relative_path


class EverythingError(RuntimeError):
    pass


def parse_extensions(value: str) -> set[str]:
    if value.strip() in ("", "*", "*.*"):
        return set()
    result = {s.strip().lstrip(".").lower() for s in re.split(r"[,; ]+", value) if s.strip()}
    if not all(re.fullmatch(r"[a-z0-9_-]+", s) for s in result):
        raise ValueError("Enter extensions separated by commas, or * for all file types.")
    return result


def parse_output(text: str, output_format: str = "json") -> list[str]:
    if not text.strip():
        return []
    try:
        rows = (
            json.loads(text.lstrip("\ufeff"))
            if output_format == "json"
            else list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))
        )
        if not isinstance(rows, list):
            raise ValueError
        paths = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError
            fields = {re.sub(r"[^a-z]", "", k.lower()): v for k, v in row.items()}
            path = fields.get("fullpathandname") or fields.get("filename")
            if not path:
                name, parent = fields.get("name"), fields.get("path")
                if not isinstance(name, str) or not isinstance(parent, str):
                    raise ValueError
                path = ntpath.join(parent, name)
            if not isinstance(path, str):
                raise ValueError
            if not path.endswith(("/", "\\")):
                paths.append(path)
        return paths
    except (ValueError, TypeError, AttributeError) as exc:
        raise EverythingError(
            "Unexpected ES output. Install a current Everything CLI release."
        ) from exc


@dataclass
class SearchResult:
    paths: list[str]
    limit_reached: bool


class EverythingAdapter:
    def __init__(self, executable: str = "", timeout: int = 30):
        self.executable = executable or shutil.which("es.exe") or ""
        self.timeout = timeout

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess:
        if not self.executable:
            raise EverythingError(
                "es.exe was not found. Install Everything CLI or choose it in Settings."
            )
        try:
            return subprocess.run(
                [self.executable, *arguments],
                shell=False,
                capture_output=True,
                timeout=self.timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except subprocess.TimeoutExpired as exc:
            raise EverythingError(
                "Everything timed out. Check that it is running, then retry."
            ) from exc
        except OSError as exc:
            raise EverythingError(
                "Cannot start es.exe. Check its executable path in Settings."
            ) from exc

    @staticmethod
    def _check(code: int) -> None:
        if code in (7, 8):
            raise EverythingError(
                "Everything IPC is unavailable. Start Everything and retry connection."
            )
        if code not in (0, 9):
            raise EverythingError(
                f"Everything CLI failed (exit code {code}). Check its version and settings."
            )

    def probe(self) -> None:
        result = self._run(["-get-everything-version"])
        self._check(result.returncode)

    def search(
        self, directory: str, extensions: str = "*", filename: str = "", limit: int = 10000
    ) -> SearchResult:
        directory = normalize_path(directory)
        selected = parse_extensions(extensions)
        if not 1 <= limit <= 100000:
            raise ValueError("Result limit must be between 1 and 100000.")
        if any(ord(c) < 32 or c == '"' for c in filename):
            raise ValueError("The filename filter cannot contain quotes or control characters.")
        query = []
        if selected:
            query.append("ext:" + ";".join(sorted(selected)))
        if filename.strip():
            query.append('regex:"' + re.escape(filename.strip()) + '"')
        # Export files are UTF-8, independent of the Windows console code page.
        with tempfile.TemporaryDirectory(prefix="sharecatalog-es-") as temp:
            output = Path(temp) / "results.json"
            arguments = [
                "-path",
                directory,
                "/a-d",
                "-n",
                str(limit),
                "-timeout",
                "5000",
                "-name",
                "-path-column",
                "-export-json",
                str(output),
                *query,
            ]
            result = self._run(arguments)
            output_format = "json"
            if result.returncode == 6:
                # Older ES releases support CSV but not JSON.
                arguments[arguments.index("-export-json")] = "-export-csv"
                result = self._run(arguments)
                output_format = "csv"
            self._check(result.returncode)
            if result.returncode == 9:
                return SearchResult([], False)
            try:
                paths = parse_output(output.read_text(encoding="utf-8-sig"), output_format)
            except (OSError, UnicodeError) as exc:
                raise EverythingError(
                    "Cannot read Everything output. Check the CLI installation."
                ) from exc
        accepted = {}
        for path in paths:
            try:
                if relative_path(path, directory) is None:
                    continue
                if selected and ntpath.splitext(path)[1].lstrip(".").lower() not in selected:
                    continue
                if filename.strip().casefold() not in ntpath.basename(path).casefold():
                    continue
                accepted.setdefault(path_key(path), normalize_path(path))
            except ValueError:
                continue
        return SearchResult(list(accepted.values()), len(paths) >= limit)
