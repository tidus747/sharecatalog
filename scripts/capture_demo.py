"""Capture the actual Qt window using fictional in-memory data and no document access."""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from sharecatalog.models.library import LibraryMapping  # noqa: E402
from sharecatalog.services.preferences import Preferences  # noqa: E402
from sharecatalog.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    app = QApplication([])
    app.setStyle("Fusion")
    # Offscreen Qt does not always discover Windows system fonts automatically.
    font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf"
    if font_path.is_file():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            app.setFont(QFont(families[0], 9))
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, "#f5f7fa"),
        (QPalette.ColorRole.WindowText, "#243248"),
        (QPalette.ColorRole.Base, "#ffffff"),
        (QPalette.ColorRole.AlternateBase, "#f0f4f9"),
        (QPalette.ColorRole.Text, "#243248"),
        (QPalette.ColorRole.Button, "#e8eef6"),
        (QPalette.ColorRole.ButtonText, "#243248"),
        (QPalette.ColorRole.Highlight, "#2466ad"),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    with tempfile.TemporaryDirectory(prefix="sharecatalog-demo-") as temporary:
        window = MainWindow(
            Preferences(width=1440, height=860), Path(temporary) / "preferences.json"
        )
        window.directory.setText(r"C:\Catalog\Engineering")
        window.project.mappings = [
            LibraryMapping(
                r"C:\Catalog\Engineering",
                "https://contoso.sharepoint.com/sites/Engineering/Shared%20Documents",
            )
        ]
        examples = [
            (
                "Calibration reference.pdf",
                "Calibration reference",
                "Reference procedure for the test bench.",
            ),
            ("Design review.docx", "Design review", "Decisions, assumptions and open questions."),
            (
                "Equipment register.xlsx",
                "Equipment register",
                "A fictional inventory for this example.",
            ),
            ("Getting started.md", "Getting started", "A short guide for the engineering team."),
            ("Release checklist.pdf", "Release checklist", "Review steps before a release."),
        ]
        window.project.refresh(["C:\\Catalog\\Engineering\\" + name for name, _, _ in examples])
        for document, (_, title, description) in zip(
            window.project.documents, examples, strict=True
        ):
            document.title, document.description = title, description
        window.model.replace(window.project.documents)
        window.update_mappings()
        window.count.setText(
            "5 fictional example documents. Generated links are not remotely verified."
        )
        window.statusBar().showMessage(
            "Illustrative catalog. No real files were searched or opened."
        )
        window.show()
        app.processEvents()
        destination = Path(__file__).resolve().parents[1] / "website/public/images/sharecatalog.png"
        if not window.grab().save(str(destination)):
            raise RuntimeError("Could not save the demo screenshot.")
        window.dirty = False
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    print("Captured the fictional example catalog.")


if __name__ == "__main__":
    main()
