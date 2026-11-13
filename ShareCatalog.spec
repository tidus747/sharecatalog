# Build on Windows: python -m PyInstaller --noconfirm ShareCatalog.spec
import sys
from importlib.metadata import distribution
from importlib.util import find_spec
from pathlib import Path

root = Path(SPECPATH)
datas = [(str(root / "LICENSE"), "."), (str(root / "THIRD_PARTY_NOTICES.md"), ".")]
if (root / "licenses").is_dir():
    datas.append((str(root / "licenses"), "licenses/qt-terms"))
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    datas.append((str(python_license), "licenses/python"))
for package in ("PySide6", "shiboken6"):
    package_root = Path(find_spec(package).origin).parent
    for directory in (package_root / "support", package_root / "Qt", package_root):
        for license_dir in (directory / "licenses", directory / "LICENSES"):
            if license_dir.is_dir():
                datas.append((str(license_dir), f"licenses/{package}/{directory.name}"))
for package in ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6"):
    installed = distribution(package)
    for file in installed.files or []:
        if "license" in str(file).lower() and installed.locate_file(file).is_file():
            datas.append((str(installed.locate_file(file)), f"licenses/{package}"))

a = Analysis(
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=[], datas=datas, hiddenimports=[], hookspath=[],
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtPdf",
              "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtNetwork", "PySide6.QtTest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="ShareCatalog", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="ShareCatalog")
