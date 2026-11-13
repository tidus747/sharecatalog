from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from sharecatalog.services.preferences import Preferences


class SettingsDialog(QDialog):
    def __init__(self, preferences: Preferences, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 220)
        layout = QFormLayout(self)
        self.executable = QLineEdit(preferences.executable)
        self.executable.setPlaceholderText("Automatic detection from PATH")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.browse)
        row = QHBoxLayout()
        row.addWidget(self.executable)
        row.addWidget(browse)
        layout.addRow("Everything CLI (es.exe)", row)
        self.limit = QSpinBox()
        self.limit.setRange(1, 100000)
        self.limit.setValue(preferences.result_limit)
        layout.addRow("Maximum search results", self.limit)
        note = QLabel("Everything must be running. ES and Everything remain external dependencies.")
        note.setWordWrap(True)
        layout.addRow(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Everything CLI", "", "Executable (es.exe)"
        )
        if path:
            self.executable.setText(path)
