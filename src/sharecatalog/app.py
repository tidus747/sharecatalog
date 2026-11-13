import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from sharecatalog.services.preferences import Preferences
from sharecatalog.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ShareCatalog")
    app.setOrganizationName("ShareCatalog")
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")
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
    preferences_path = (
        Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
        / "preferences.json"
    )
    window = MainWindow(Preferences.load(preferences_path), preferences_path)
    window.show()
    return app.exec()
