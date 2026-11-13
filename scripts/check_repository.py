"""Check source text without inspecting ignored private catalog data."""

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            "ls-files",
            "-co",
            "--exclude-standard",
            "-z",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    invalid = []
    for name in set(output.decode("utf-8").split("\0")) - {""}:
        path = root / name
        if not path.is_file():
            continue
        try:
            if chr(0x2014) in path.read_text(encoding="utf-8"):
                invalid.append(name)
        except UnicodeDecodeError:
            continue
    if invalid:
        print("Forbidden punctuation in: " + ", ".join(sorted(invalid)))
        return 1
    print("Repository text check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
