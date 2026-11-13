# Windows build and distribution

Use 64-bit Python 3.11+ on Windows, install `requirements-dev.txt` and the checkout
with `python -m pip install --no-deps -e .`.

```powershell
python -m PyInstaller --noconfirm ShareCatalog.spec
```

Distribute the entire `dist/ShareCatalog` directory, including `_internal`, never
the EXE alone. The windowed build suppresses the console and requests no elevation.
Everything and ES are not collected. Build artifacts are ignored by Git.

The spec copies installed Python/PySide6/Shiboken licenses when present. Inspect
the output, add missing third-party notices, and fulfill source/offer obligations
from `THIRD_PARTY_NOTICES.md`. Record dependency versions with the pinned requirements.
Rebuild in a clean environment for release. Signing/installers are outside v0.1.

Test on clean Windows without Python: CLI setup, real indexed search, browser sample
confirmation, Confluence paste, export and persistence. Developer-machine launch
and automated source tests do not prove this clean-machine workflow.
